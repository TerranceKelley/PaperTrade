"""Option selection logic for put credit spreads."""

from datetime import datetime
from typing import List, Optional, Dict
from dataclasses import dataclass

from ..config import config
from ..logging_setup import get_logger
from ..time_utils import days_to_expiration, now_et
from ..ibkr.options_chain import (
    get_option_chain,
    filter_expirations_by_dte,
    get_option_contract_with_greeks
)
from ..ibkr.market_data import get_stock_quote

logger = get_logger(__name__)


@dataclass
class SpreadCandidate:
    """Represents a candidate put credit spread."""
    symbol: str
    expiration: str
    dte: int
    short_strike: float
    long_strike: float
    short_delta: Optional[float]
    credit: float
    max_loss: float
    short_bid: float
    short_ask: float
    long_bid: float
    long_ask: float
    short_bidask_spread: float
    long_bidask_spread: float
    has_greeks: bool
    selection_method: str  # "delta" or "otm_fallback"


def find_candidates(symbol: str) -> List[SpreadCandidate]:
    """Find candidate put credit spreads for a symbol."""
    candidates = []

    # Get underlying price
    stock_quote = get_stock_quote(symbol)
    if not stock_quote or not stock_quote.get("has_bid_ask"):
        logger.warning(f"No valid quote for {symbol}")
        return candidates

    underlying_price = stock_quote.get("bid") or stock_quote.get("ask") or stock_quote.get("last")
    if not underlying_price:
        logger.warning(f"Cannot determine price for {symbol}")
        return candidates

    # Get option chain
    chain = get_option_chain(symbol)
    if not chain:
        logger.warning(f"No option chain for {symbol}")
        return candidates

    # Filter expirations by DTE
    valid_expirations = filter_expirations_by_dte(chain.expirations, config.dte_min, config.dte_max)
    if not valid_expirations:
        logger.info(f"No expirations in DTE range {config.dte_min}-{config.dte_max} for {symbol}")
        return candidates

    # Process each expiration
    for exp_str in valid_expirations:
        try:
            exp_date = datetime.strptime(exp_str, "%Y%m%d")
            dte = days_to_expiration(exp_date)
            strikes = chain.strikes.get(exp_str, [])

            if not strikes:
                continue

            # Find candidate short puts
            for short_strike in strikes:
                # Calculate long strike
                long_strike = short_strike - config.spread_width
                if long_strike not in strikes:
                    continue  # Long strike not available

                # Get option data for both legs
                short_opt = get_option_contract_with_greeks(symbol, exp_str, short_strike, "P")
                long_opt = get_option_contract_with_greeks(symbol, exp_str, long_strike, "P")

                if not short_opt or not long_opt:
                    continue

                # Check liquidity
                if not short_opt.get("has_bid_ask") or not long_opt.get("has_bid_ask"):
                    continue

                short_bidask = short_opt.get("bid_ask_spread")
                long_bidask = long_opt.get("bid_ask_spread")

                if short_bidask is None or long_bidask is None:
                    continue

                if short_bidask > config.leg_max_bidask or long_bidask > config.leg_max_bidask:
                    continue  # Spread too wide

                # Check delta or use OTM fallback
                short_delta = short_opt.get("delta")
                has_greeks = short_opt.get("has_greeks", False)
                selection_method = "delta"

                if has_greeks and short_delta is not None:
                    # Use delta filter
                    if not (config.delta_min <= abs(short_delta) <= config.delta_max):
                        continue  # Delta out of range
                else:
                    # No Greeks - check if we can use fallback
                    if config.require_greeks:
                        continue  # Reject if Greeks required
                    # Use OTM fallback
                    otm_pct = (underlying_price - short_strike) / underlying_price
                    target_otm = config.otm_target_pct
                    if not (target_otm * 0.8 <= otm_pct <= target_otm * 1.2):
                        continue  # Not close enough to target OTM
                    selection_method = "otm_fallback"
                    logger.info(f"Using OTM fallback for {symbol} {exp_str} {short_strike}: {otm_pct:.2%}")

                # Calculate credit and max loss
                short_bid = short_opt.get("bid", 0)
                short_ask = short_opt.get("ask", 0)
                long_bid = long_opt.get("bid", 0)
                long_ask = long_opt.get("ask", 0)

                # Credit = short bid - long ask (we sell short, buy long)
                credit = short_bid - long_ask
                if credit <= 0:
                    continue  # Not a credit spread

                # Max loss = spread width - credit
                max_loss = config.spread_width - credit

                candidate = SpreadCandidate(
                    symbol=symbol,
                    expiration=exp_str,
                    dte=dte,
                    short_strike=short_strike,
                    long_strike=long_strike,
                    short_delta=short_delta,
                    credit=credit,
                    max_loss=max_loss,
                    short_bid=short_bid,
                    short_ask=short_ask,
                    long_bid=long_bid,
                    long_ask=long_ask,
                    short_bidask_spread=short_bidask,
                    long_bidask_spread=long_bidask,
                    has_greeks=has_greeks,
                    selection_method=selection_method
                )

                candidates.append(candidate)

        except Exception as e:
            logger.error(f"Error processing expiration {exp_str} for {symbol}: {e}")
            continue

    # Sort by credit (descending)
    candidates.sort(key=lambda x: x.credit, reverse=True)

    return candidates


def get_top_candidates(symbol: str, limit: int = 5) -> List[SpreadCandidate]:
    """Get top N candidates for a symbol."""
    candidates = find_candidates(symbol)
    return candidates[:limit]
