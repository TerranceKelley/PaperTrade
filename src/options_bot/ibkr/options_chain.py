"""Options chain retrieval and filtering."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from ib_insync import Stock, Option, Contract
from ib_insync.ticker import Ticker

from ..config import config
from ..logging_setup import get_logger
from ..time_utils import days_to_expiration
from .connection import ib_conn
from .market_data import get_stock_contract, get_ticker

logger = get_logger(__name__)


class OptionChain:
    """Represents an option chain for a symbol."""

    def __init__(self, symbol: str, expirations: List[str], strikes: Dict[str, List[float]]):
        """Initialize option chain."""
        self.symbol = symbol
        self.expirations = expirations
        self.strikes = strikes  # expiration -> list of strikes


def get_option_chain(symbol: str) -> Optional[OptionChain]:
    """Get option chain for symbol."""
    if not ib_conn.is_connected():
        logger.error("Not connected to IB")
        return None

    try:
        stock = get_stock_contract(symbol)
        ib_conn.ib.qualifyContracts(stock)

        # Request option chain
        chains = ib_conn.ib.reqSecDefOptParams(
            stock.symbol,
            "",
            stock.secType,
            stock.conId
        )

        if not chains:
            logger.warning(f"No option chains found for {symbol}")
            return None

        # Use first chain (typically the main exchange)
        chain = chains[0]
        expirations = sorted(chain.expirations)
        strikes = {exp: sorted(chain.strikes) for exp in expirations}

        logger.info(f"Found {len(expirations)} expirations for {symbol}")
        return OptionChain(symbol, expirations, strikes)
    except Exception as e:
        logger.error(f"Error getting option chain for {symbol}: {e}")
        return None


def get_option_contract_with_greeks(
    symbol: str,
    expiration: str,
    strike: float,
    right: str
) -> Optional[Dict]:
    """Get option contract with market data and Greeks."""
    try:
        stock = get_stock_contract(symbol)
        option = Option(
            symbol,
            expiration,
            strike,
            right,
            "SMART"
        )
        ib_conn.ib.qualifyContracts(option)

        # Request market data
        ticker = get_ticker(option)
        if not ticker:
            return None

        # Extract Greeks from ticker
        delta = None
        has_greeks = False
        if hasattr(ticker, 'modelGreeks') and ticker.modelGreeks:
            delta = ticker.modelGreeks.delta
            has_greeks = True
        elif hasattr(ticker, 'optionGreeks') and ticker.optionGreeks:
            delta = ticker.optionGreeks.delta
            has_greeks = True

        bid = ticker.bid if ticker.bid else None
        ask = ticker.ask if ticker.ask else None
        bid_ask_spread = None
        if bid is not None and ask is not None:
            bid_ask_spread = ask - bid

        return {
            "contract": option,
            "symbol": symbol,
            "expiration": expiration,
            "strike": strike,
            "right": right,
            "bid": bid,
            "ask": ask,
            "bid_ask_spread": bid_ask_spread,
            "delta": delta,
            "has_greeks": has_greeks,
            "has_bid_ask": bid is not None and ask is not None,
        }
    except Exception as e:
        logger.error(f"Error getting option with Greeks for {symbol} {expiration} {strike} {right}: {e}")
        return None


def filter_expirations_by_dte(expirations: List[str], dte_min: int, dte_max: int) -> List[str]:
    """Filter expirations by days to expiration."""
    from ..time_utils import now_et
    now = now_et()
    filtered = []
    for exp_str in expirations:
        try:
            exp_date = datetime.strptime(exp_str, "%Y%m%d")
            dte = days_to_expiration(exp_date, now)
            if dte_min <= dte <= dte_max:
                filtered.append(exp_str)
        except ValueError:
            logger.warning(f"Invalid expiration format: {exp_str}")
    return filtered
