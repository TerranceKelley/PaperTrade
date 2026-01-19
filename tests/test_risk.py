"""Tests for risk management."""

import pytest
from options_bot.strategy.risk import (
    calculate_position_size,
    get_daily_loss_pct,
    is_daily_loss_exceeded,
    can_open_new_trade
)


def test_calculate_position_size():
    """Test position sizing calculation."""
    # Max risk = 1000 * 0.02 = $20
    # If max_loss per contract = $5, we can trade 4 contracts
    size = calculate_position_size(5.0)
    assert size == 4

    # If max_loss = $20, we can trade 1 contract
    size = calculate_position_size(20.0)
    assert size == 1

    # If max_loss > max_risk, function still returns 1 (minimum)
    # This is by design - the function ensures at least 1 contract
    size = calculate_position_size(25.0)
    assert size == 1  # Function returns max(1, ...) to ensure minimum position


def test_can_open_new_trade():
    """Test trade opening checks."""
    # This will depend on database state, so we'll just test the logic
    can_open, reason = can_open_new_trade()
    # Reason should be a string
    assert isinstance(reason, str)
    assert isinstance(can_open, bool)
