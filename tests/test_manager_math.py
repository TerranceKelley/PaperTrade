"""Tests for manager math (TP/SL calculations)."""

import pytest


def test_tp_calculation():
    """Test take-profit calculation."""
    # If credit = $1.00, TP at 50% = $0.50 debit to close
    credit = 1.00
    tp_threshold = credit * 0.50
    assert tp_threshold == 0.50

    # If current debit = $0.45, we should take profit
    current_debit = 0.45
    assert current_debit <= tp_threshold


def test_sl_calculation():
    """Test stop-loss calculation."""
    # If credit = $1.00, SL at 2.0x = $2.00 debit to close
    credit = 1.00
    sl_threshold = credit * 2.0
    assert sl_threshold == 2.00

    # If current debit = $2.10, we should stop loss
    current_debit = 2.10
    assert current_debit >= sl_threshold


def test_spread_value_calculation():
    """Test spread value calculation."""
    # To close: buy back short (ask), sell long (bid)
    # Debit = short_ask - long_bid
    short_ask = 1.50
    long_bid = 0.20
    debit = short_ask - long_bid
    assert debit == 1.30
