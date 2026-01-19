"""Position tracking and valuation."""

from typing import List, Optional, Dict
from ib_insync import Portfolio, Position

from ..config import config
from ..logging_setup import get_logger
from .connection import ib_conn

logger = get_logger(__name__)


def get_open_positions() -> List[Position]:
    """Get all open positions."""
    if not ib_conn.is_connected():
        return []

    try:
        positions = ib_conn.ib.positions()
        return positions
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return []


def get_position_value(symbol: str, expiration: str, short_strike: float, long_strike: float) -> Optional[float]:
    """Get current value of a spread position."""
    # This is a simplified version - in production, you'd match the exact contracts
    # For now, we'll use the trade's credit/debit tracking
    # In a full implementation, you'd query the actual position and calculate mark-to-market
    return None


def calculate_spread_value(
    short_bid: float,
    short_ask: float,
    long_bid: float,
    long_ask: float
) -> float:
    """Calculate current spread value (debit to close)."""
    # To close: buy back short, sell long
    # Debit = short ask - long bid
    return short_ask - long_bid
