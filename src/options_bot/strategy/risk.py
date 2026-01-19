"""Risk management module."""

from datetime import date
from typing import Optional

from ..config import config
from ..db.repo import repo
from ..logging_setup import get_logger

logger = get_logger(__name__)


def calculate_position_size(max_loss: float) -> int:
    """Calculate position size based on risk per trade."""
    max_risk_amount = config.account_size * config.risk_per_trade_pct
    if max_loss <= 0:
        return 0
    # Position size is number of contracts
    # Each contract has max_loss, so we can risk max_risk_amount
    position_size = int(max_risk_amount / max_loss)
    return max(1, position_size)  # At least 1 contract


def get_daily_pnl() -> tuple[float, float]:
    """Get today's realized and unrealized P/L."""
    today = date.today()
    stats = repo.get_or_create_daily_stats(today)
    return stats.realized_pnl, stats.unrealized_pnl


def get_daily_loss_pct() -> float:
    """Get today's loss as percentage of account."""
    realized, unrealized = get_daily_pnl()
    total_pnl = realized + unrealized
    loss_pct = abs(min(0, total_pnl)) / config.account_size
    return loss_pct


def is_daily_loss_exceeded() -> bool:
    """Check if daily loss limit is exceeded."""
    loss_pct = get_daily_loss_pct()
    exceeded = loss_pct >= config.max_daily_loss_pct
    if exceeded:
        logger.warning(f"Daily loss limit exceeded: {loss_pct:.2%} >= {config.max_daily_loss_pct:.2%}")
    return exceeded


def get_trades_today_count() -> int:
    """Get number of trades opened today."""
    today = date.today()
    stats = repo.get_or_create_daily_stats(today)
    return stats.trades_count


def can_open_new_trade() -> tuple[bool, str]:
    """Check if we can open a new trade. Returns (allowed, reason)."""
    # Check trading disabled
    if config.trading_disabled:
        return False, "Trading is disabled (TRADING_DISABLED=true)"

    # Check daily loss
    if is_daily_loss_exceeded():
        return False, f"Daily loss limit exceeded ({get_daily_loss_pct():.2%})"

    # Check trade count
    trades_today = get_trades_today_count()
    if trades_today >= config.max_trades_per_day:
        return False, f"Max trades per day reached ({trades_today}/{config.max_trades_per_day})"

    return True, "OK"


def has_open_trade_for_symbol(symbol: str) -> bool:
    """Check if there's an open trade for the symbol."""
    open_trades = repo.get_open_trades(symbol=symbol)
    return len(open_trades) > 0


def update_daily_stats_for_trade_open():
    """Update daily stats when opening a trade."""
    today = date.today()
    stats = repo.get_or_create_daily_stats(today)
    repo.update_daily_stats(today, trades_count=stats.trades_count + 1)


def update_daily_stats_for_trade_close(pnl: float):
    """Update daily stats when closing a trade."""
    today = date.today()
    stats = repo.get_or_create_daily_stats(today)
    new_realized = stats.realized_pnl + pnl
    new_wins = stats.wins_count + (1 if pnl > 0 else 0)
    new_losses = stats.losses_count + (1 if pnl < 0 else 0)
    repo.update_daily_stats(
        today,
        realized_pnl=new_realized,
        wins_count=new_wins,
        losses_count=new_losses
    )
