"""Market data retrieval."""

from typing import Optional
from ib_insync import Stock, Option, Contract
from ib_insync.ticker import Ticker

from ..config import config
from ..logging_setup import get_logger
from .connection import ib_conn

logger = get_logger(__name__)


def get_stock_contract(symbol: str) -> Stock:
    """Get stock contract for symbol."""
    contract = Stock(symbol, "SMART", "USD")
    return contract


def get_option_contract(
    symbol: str,
    expiration: str,
    strike: float,
    right: str
) -> Option:
    """Get option contract."""
    stock = get_stock_contract(symbol)
    contract = Option(
        symbol,
        expiration,
        strike,
        right,
        "SMART"
    )
    return contract


def get_ticker(contract: Contract) -> Optional[Ticker]:
    """Get ticker for contract."""
    if not ib_conn.is_connected():
        logger.error("Not connected to IB")
        return None

    try:
        ticker = ib_conn.ib.reqMktData(contract, "", False, False)
        ib_conn.ib.sleep(1)  # Wait for data
        return ticker
    except Exception as e:
        logger.error(f"Error getting ticker for {contract}: {e}")
        return None


def get_stock_quote(symbol: str) -> Optional[dict]:
    """Get stock quote with bid/ask."""
    contract = get_stock_contract(symbol)
    ticker = get_ticker(contract)
    if not ticker:
        return None

    return {
        "symbol": symbol,
        "bid": ticker.bid if ticker.bid else None,
        "ask": ticker.ask if ticker.ask else None,
        "last": ticker.last if ticker.last else None,
        "close": ticker.close if ticker.close else None,
        "has_bid_ask": ticker.bid is not None and ticker.ask is not None,
    }


def get_option_quote(
    symbol: str,
    expiration: str,
    strike: float,
    right: str
) -> Optional[dict]:
    """Get option quote with bid/ask and Greeks."""
    contract = get_option_contract(symbol, expiration, strike, right)
    ticker = get_ticker(contract)
    if not ticker:
        return None

    # Get Greeks from ticker
    delta = None
    has_greeks = False
    if ticker.modelGreeks:
        delta = ticker.modelGreeks.delta
        has_greeks = True
    elif ticker.optionGreeks:
        delta = ticker.optionGreeks.delta
        has_greeks = True

    return {
        "symbol": symbol,
        "expiration": expiration,
        "strike": strike,
        "right": right,
        "bid": ticker.bid if ticker.bid else None,
        "ask": ticker.ask if ticker.ask else None,
        "last": ticker.last if ticker.last else None,
        "delta": delta,
        "has_greeks": has_greeks,
        "has_bid_ask": ticker.bid is not None and ticker.ask is not None,
    }
