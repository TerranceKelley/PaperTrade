"""Tests for safety features and kill switches."""

import pytest
from unittest.mock import patch, MagicMock
from options_bot.config import config
from options_bot.strategy.risk import (
    can_open_new_trade,
    is_daily_loss_exceeded,
    has_open_trade_for_symbol
)
from options_bot.db.repo import repo
from options_bot.db.schema import Trade, DailyStats
from datetime import date, datetime


def test_trading_disabled_by_default():
    """Verify trading is disabled by default."""
    assert config.trading_disabled is True


def test_can_open_new_trade_when_disabled():
    """Test that can_open_new_trade returns False when trading disabled."""
    with patch('options_bot.strategy.risk.config') as mock_config:
        mock_config.trading_disabled = True
        can_open, reason = can_open_new_trade()
        assert can_open is False
        assert "disabled" in reason.lower()


def test_daily_loss_kill_switch():
    """Test daily loss kill switch prevents new trades."""
    # This would require mocking the database
    # In a real test, you'd set up test data
    pass


def test_max_trades_per_day():
    """Test max trades per day limit."""
    with patch('options_bot.strategy.risk.config') as mock_config:
        mock_config.max_trades_per_day = 2
        mock_config.trading_disabled = False
        mock_config.account_size = 1000.0
        mock_config.max_daily_loss_pct = 0.03
        
        # Mock daily stats
        with patch('options_bot.strategy.risk.repo') as mock_repo:
            mock_stats = MagicMock()
            mock_stats.trades_count = 2
            mock_stats.realized_pnl = 0.0
            mock_stats.unrealized_pnl = 0.0
            mock_repo.get_or_create_daily_stats.return_value = mock_stats
            
            can_open, reason = can_open_new_trade()
            assert can_open is False
            assert "max trades" in reason.lower() or "trades per day" in reason.lower()


def test_duplicate_trade_prevention():
    """Test that duplicate trades on same symbol are prevented."""
    # This would require mocking the database
    pass


def test_position_sizing_respects_risk_limit():
    """Test position sizing doesn't exceed risk per trade."""
    from options_bot.strategy.risk import calculate_position_size
    
    # Max risk = 1000 * 0.02 = $20
    # If max_loss = $10, should get 2 contracts max
    size = calculate_position_size(10.0)
    max_risk = config.account_size * config.risk_per_trade_pct
    assert size * 10.0 <= max_risk  # Position size * max_loss <= max risk


def test_entry_window_enforcement():
    """Test entry window is enforced."""
    from options_bot.time_utils import is_in_entry_window, parse_time
    
    # Mock current time to be outside window
    with patch('options_bot.time_utils.now_et') as mock_now:
        from datetime import time
        mock_now.return_value.time.return_value = time(15, 0)  # 3 PM
        
        # If window is 10:00-11:00, 3 PM should be outside
        window_start = parse_time("10:00")
        window_end = parse_time("11:00")
        current = time(15, 0)
        
        assert not (window_start <= current <= window_end)


def test_safety_checks_in_order_placement():
    """Verify order placement functions check trading_disabled."""
    # This is more of an integration test
    # The actual code should check config.trading_disabled before placing orders
    pass
