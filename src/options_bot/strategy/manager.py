"""Trade management logic (TP/SL/time exits)."""

from datetime import datetime
from typing import Optional

from ..config import config
from ..db.repo import repo
from ..logging_setup import get_logger
from ..time_utils import days_to_expiration, now_et
from ..ibkr.options_chain import get_option_contract_with_greeks
from ..ibkr.combo_orders import place_spread_order_close
from ..strategy.risk import update_daily_stats_for_trade_close

logger = get_logger(__name__)


def check_trade_exits(trade_id: int) -> Optional[str]:
    """Check if a trade should be closed. Returns reason or None."""
    from ..db.schema import Trade

    # Get trade from database
    with repo.get_session() as session:
        trade = session.query(Trade).filter(Trade.id == trade_id).first()
        if not trade or trade.status != "open":
            return None

        # Get current spread value
        exp_str = trade.exp.strftime("%Y%m%d")
        short_opt = get_option_contract_with_greeks(
            trade.symbol,
            exp_str,
            trade.short_strike,
            "P"
        )
        long_opt = get_option_contract_with_greeks(
            trade.symbol,
            exp_str,
            trade.long_strike,
            "P"
        )

        if not short_opt or not long_opt:
            logger.warning(f"Cannot get quotes for trade {trade_id}")
            return None

        if not short_opt.get("has_bid_ask") or not long_opt.get("has_bid_ask"):
            logger.warning(f"Missing bid/ask for trade {trade_id}")
            return None

        # Calculate current spread value (debit to close)
        short_ask = short_opt.get("ask", 0)
        long_bid = long_opt.get("bid", 0)
        current_debit = short_ask - long_bid

        # Check take-profit: close when debit <= 50% of credit
        tp_threshold = trade.credit * config.tp_capture_pct
        if current_debit <= tp_threshold:
            return "take_profit"

        # Check stop-loss: close when debit >= 2.0x credit
        sl_threshold = trade.credit * config.sl_multiple
        if current_debit >= sl_threshold:
            return "stop_loss"

        # Check time exit: close when DTE <= 3
        dte = days_to_expiration(trade.exp, now_et())
        if dte <= config.time_exit_dte:
            return "time_exit"

        return None


def close_trade(trade_id: int, reason: str) -> bool:
    """Close a trade."""
    from ..db.schema import Trade

    with repo.get_session() as session:
        trade = session.query(Trade).filter(Trade.id == trade_id).first()
        if not trade or trade.status != "open":
            return False

        # Get current spread value
        exp_str = trade.exp.strftime("%Y%m%d")
        short_opt = get_option_contract_with_greeks(
            trade.symbol,
            exp_str,
            trade.short_strike,
            "P"
        )
        long_opt = get_option_contract_with_greeks(
            trade.symbol,
            exp_str,
            trade.long_strike,
            "P"
        )

        if not short_opt or not long_opt:
            logger.error(f"Cannot get quotes to close trade {trade_id}")
            return False

        short_ask = short_opt.get("ask", 0)
        long_bid = long_opt.get("bid", 0)
        debit_to_close = short_ask - long_bid

        # Calculate P/L
        pnl = (trade.credit - debit_to_close) * trade.qty

        # Place close order (if trading enabled)
        if not config.trading_disabled:
            order_result = place_spread_order_close(
                trade.symbol,
                exp_str,
                trade.short_strike,
                trade.long_strike,
                trade.qty,
                debit_to_close
            )
            if not order_result:
                logger.warning(f"Failed to place close order for trade {trade_id}")
        else:
            logger.info(f"Trading disabled - simulating close for trade {trade_id}")

        # Update trade in database
        repo.update_trade(
            trade_id,
            status="closed",
            debit_to_close=debit_to_close,
            pnl=pnl,
            reason_close=reason
        )

        # Update daily stats
        update_daily_stats_for_trade_close(pnl)

        logger.info(f"Closed trade {trade_id}: {reason}, P/L: ${pnl:.2f}")
        return True


def manage_open_trades():
    """Check and manage all open trades."""
    open_trades = repo.get_open_trades()
    logger.info(f"Managing {len(open_trades)} open trades")

    for trade in open_trades:
        reason = check_trade_exits(trade.id)
        if reason:
            logger.info(f"Trade {trade.id} should be closed: {reason}")
            close_trade(trade.id, reason)
