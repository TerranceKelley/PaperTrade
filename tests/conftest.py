"""Pytest configuration and fixtures."""

import pytest
import os
import tempfile
import shutil
from pathlib import Path


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    # Use temporary database for tests
    test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db.close()
    
    monkeypatch.setenv("DB_PATH", test_db.name)
    monkeypatch.setenv("TRADING_DISABLED", "true")
    monkeypatch.setenv("ACCOUNT_SIZE", "1000")
    monkeypatch.setenv("LOG_DIR", str(Path(tempfile.gettempdir()) / "test_logs"))
    
    yield
    
    # Cleanup
    if os.path.exists(test_db.name):
        os.unlink(test_db.name)
    
    test_log_dir = Path(tempfile.gettempdir()) / "test_logs"
    if test_log_dir.exists():
        shutil.rmtree(test_log_dir)


@pytest.fixture
def mock_ib_connection():
    """Mock IB connection for unit tests."""
    from unittest.mock import MagicMock, patch
    
    with patch('options_bot.ibkr.connection.ib_conn') as mock_conn:
        mock_conn.is_connected.return_value = True
        mock_conn.get_account_id.return_value = "DU123456"
        mock_conn.is_paper_account.return_value = True
        yield mock_conn
