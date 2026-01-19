"""Tests for option selection logic."""

import pytest
from options_bot.strategy.selector import SpreadCandidate


def test_spread_candidate():
    """Test SpreadCandidate dataclass."""
    candidate = SpreadCandidate(
        symbol="SPY",
        expiration="20240119",
        dte=10,
        short_strike=450.0,
        long_strike=449.0,
        short_delta=0.20,
        credit=0.50,
        max_loss=0.50,
        short_bid=0.52,
        short_ask=0.54,
        long_bid=0.01,
        long_ask=0.02,
        short_bidask_spread=0.02,
        long_bidask_spread=0.01,
        has_greeks=True,
        selection_method="delta"
    )

    assert candidate.symbol == "SPY"
    assert candidate.credit == 0.50
    assert candidate.max_loss == 0.50
    assert candidate.has_greeks is True
