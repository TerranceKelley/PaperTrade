"""Integration tests (require IB Gateway connection)."""

import pytest
from options_bot.ibkr.connection import ib_conn
from options_bot.services.doctor import run_doctor


@pytest.mark.integration
def test_ib_connection():
    """Test IB Gateway connection."""
    if not ib_conn.connect():
        pytest.skip("IB Gateway not available")
    
    try:
        assert ib_conn.is_connected()
        accounts = ib_conn.get_accounts()
        assert len(accounts) > 0
    finally:
        ib_conn.disconnect()


@pytest.mark.integration
def test_paper_account_detection():
    """Test paper account detection."""
    if not ib_conn.connect():
        pytest.skip("IB Gateway not available")
    
    try:
        account_id = ib_conn.get_account_id()
        if account_id:
            is_paper = ib_conn.is_paper_account(account_id)
            # In paper trading, account should start with DU
            # But we can't enforce this in test - just verify function works
            assert isinstance(is_paper, bool)
    finally:
        ib_conn.disconnect()


@pytest.mark.integration
def test_market_data_retrieval():
    """Test market data retrieval."""
    if not ib_conn.connect():
        pytest.skip("IB Gateway not available")
    
    try:
        from options_bot.ibkr.market_data import get_stock_quote
        quote = get_stock_quote("SPY")
        # During market hours, should have bid/ask
        # Outside market hours, may only have last/close
        assert quote is not None
        assert "symbol" in quote
    finally:
        ib_conn.disconnect()


@pytest.mark.integration
def test_options_chain_retrieval():
    """Test options chain retrieval."""
    if not ib_conn.connect():
        pytest.skip("IB Gateway not available")
    
    try:
        from options_bot.ibkr.options_chain import get_option_chain
        chain = get_option_chain("SPY")
        if chain:
            assert chain.symbol == "SPY"
            assert len(chain.expirations) > 0
    finally:
        ib_conn.disconnect()


@pytest.mark.integration
def test_greeks_availability():
    """Test Greeks availability from market data."""
    if not ib_conn.connect():
        pytest.skip("IB Gateway not available")
    
    try:
        from options_bot.ibkr.options_chain import get_option_contract_with_greeks
        from datetime import datetime
        
        # Get a near-term expiration
        from options_bot.ibkr.options_chain import get_option_chain
        chain = get_option_chain("SPY")
        if chain and chain.expirations:
            exp = chain.expirations[0]
            strikes = chain.strikes.get(exp, [])
            if strikes:
                # Try to get Greeks for first strike
                opt_data = get_option_contract_with_greeks("SPY", exp, strikes[0], "P")
                if opt_data:
                    # Verify structure
                    assert "has_greeks" in opt_data
                    assert "delta" in opt_data or not opt_data.get("has_greeks")
    finally:
        ib_conn.disconnect()
