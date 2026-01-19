"""Runner service for trading sessions."""

import time
from datetime import datetime, timedelta

from ..config import config
from ..logging_setup import get_logger
from ..time_utils import is_in_entry_window, now_et
from ..ibkr.connection import ib_conn
from ..db.repo import repo
from ..strategy.selector import get_top_candidates
from ..strategy.risk import (
    can_open_new_trade,
    has_open_trade_for_symbol,
    calculate_position_size,
    update_daily_stats_for_trade_open
)
from ..ibkr.combo_orders import place_spread_order_open
from ..strategy.manager import manage_open_trades

logger = get_logger(__name__)


def run_session(duration_minutes: int):
    """Run a trading session."""
    logger.info(f"Starting trading session for {duration_minutes} minutes")

    # Connect to IB
    if not ib_conn.connect():
        logger.error("Failed to connect to IB Gateway")
        return

    try:
        # Create bot run record
        bot_run = repo.create_bot_run("run", f"Session duration: {duration_minutes} minutes")

        end_time = now_et() + timedelta(minutes=duration_minutes)
        last_manage_time = now_et()

        while now_et() < end_time:
            current_time = now_et()

            # Management loop
            if (current_time - last_manage_time).total_seconds() >= config.manage_interval_seconds:
                logger.info("Running management loop...")
                manage_open_trades()
                last_manage_time = current_time

            # Entry window - scan and potentially open trades
            if is_in_entry_window():
                logger.info("In entry window - scanning for candidates...")

                for symbol in config.underlyings:
                    # Check if we can open a new trade
                    can_open, reason = can_open_new_trade()
                    if not can_open:
                        logger.info(f"Cannot open new trade: {reason}")
                        continue

                    # Check if we already have an open trade for this symbol
                    if has_open_trade_for_symbol(symbol):
                        logger.info(f"Already have open trade for {symbol}")
                        continue

                    # Get top candidates
                    candidates = get_top_candidates(symbol, limit=3)
                    if not candidates:
                        logger.info(f"No candidates found for {symbol}")
                        continue

                    # Try to open the best candidate
                    for candidate in candidates:
                        # Calculate position size
                        position_size = calculate_position_size(candidate.max_loss)
                        if position_size <= 0:
                            logger.warning(f"Invalid position size for {symbol}")
                            continue

                        # Calculate target credit (use mid price)
                        target_credit = (candidate.short_bid + candidate.short_ask) / 2 - \
                                      (candidate.long_bid + candidate.long_ask) / 2

                        logger.info(f"Attempting to open trade: {symbol} {candidate.expiration} "
                                  f"{candidate.short_strike}/{candidate.long_strike} "
                                  f"qty={position_size} credit={target_credit:.2f}")

                        # Place order (if trading enabled)
                        if not config.trading_disabled:
                            order_result = place_spread_order_open(
                                symbol,
                                candidate.expiration,
                                candidate.short_strike,
                                candidate.long_strike,
                                position_size,
                                target_credit
                            )

                            if order_result:
                                # Create trade record
                                exp_date = datetime.strptime(candidate.expiration, "%Y%m%d")
                                trade = repo.create_trade(
                                    bot_run_id=bot_run.id,
                                    symbol=symbol,
                                    exp=exp_date,
                                    short_strike=candidate.short_strike,
                                    long_strike=candidate.long_strike,
                                    qty=position_size,
                                    credit=target_credit,
                                    reason_open=f"Delta: {candidate.short_delta}, Method: {candidate.selection_method}"
                                )

                                # Update daily stats
                                update_daily_stats_for_trade_open()

                                logger.info(f"Trade opened: ID={trade.id}")
                                break  # Only one trade per symbol
                        else:
                            logger.info("Trading disabled - would open trade but skipping")
                            break  # Simulate opening one trade

            # Sleep before next iteration
            time.sleep(30)  # Check every 30 seconds

        # Final management pass
        logger.info("Session ending - final management pass...")
        manage_open_trades()

        # Update bot run
        repo.update_bot_run(bot_run.id, ended_at=now_et())

        logger.info("Trading session completed")

    finally:
        ib_conn.disconnect()


def run_manage_only():
    """Run management only (no new entries)."""
    logger.info("Starting management-only mode")

    if not ib_conn.connect():
        logger.error("Failed to connect to IB Gateway")
        return

    try:
        bot_run = repo.create_bot_run("manage", "Management-only mode")

        # Run management loop continuously
        try:
            while True:
                manage_open_trades()
                time.sleep(config.manage_interval_seconds)
        except KeyboardInterrupt:
            logger.info("Management mode interrupted by user")
        finally:
            repo.update_bot_run(bot_run.id, ended_at=now_et())

    finally:
        ib_conn.disconnect()
