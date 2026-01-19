"""IBKR connection management with retries."""

import time
from typing import Optional
from ib_insync import IB, util

from ..config import config
from ..logging_setup import get_logger

logger = get_logger(__name__)


class IBConnection:
    """Manages IBKR connection."""

    def __init__(self):
        """Initialize connection."""
        self.ib = IB()
        self.connected = False

    def connect(self, retries: int = 3, retry_delay: float = 2.0) -> bool:
        """Connect to IB Gateway with retries."""
        for attempt in range(retries):
            try:
                logger.info(f"Connecting to IB Gateway at {config.ib_host}:{config.ib_port} (attempt {attempt + 1}/{retries})")
                self.ib.connect(
                    config.ib_host,
                    config.ib_port,
                    clientId=config.ib_client_id,
                    readonly=config.ib_readonly
                )
                self.connected = True
                logger.info("Successfully connected to IB Gateway")
                return True
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("Failed to connect after all retries")
                    return False
        return False

    def disconnect(self):
        """Disconnect from IB Gateway."""
        if self.connected:
            try:
                self.ib.disconnect()
                self.connected = False
                logger.info("Disconnected from IB Gateway")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")

    def is_connected(self) -> bool:
        """Check if connected."""
        if not self.connected:
            return False
        try:
            # Try to get account values as a health check
            self.ib.accountValues()
            return True
        except Exception:
            self.connected = False
            return False

    def get_accounts(self) -> list[str]:
        """Get list of account IDs."""
        try:
            accounts = self.ib.accountValues()
            account_ids = set()
            for av in accounts:
                if av.account:
                    account_ids.add(av.account)
            return sorted(list(account_ids))
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            return []

    def get_account_id(self) -> Optional[str]:
        """Get the account ID to use."""
        accounts = self.get_accounts()
        if not accounts:
            return None

        # If configured, use that
        if config.ib_account_id:
            if config.ib_account_id in accounts:
                return config.ib_account_id
            logger.warning(f"Configured account {config.ib_account_id} not found")

        # Otherwise, prefer paper account (DU prefix)
        for account in accounts:
            if account.startswith("DU"):
                return account

        # Fall back to first account
        return accounts[0]

    def is_paper_account(self, account_id: Optional[str] = None) -> bool:
        """Check if account is a paper account (DU prefix)."""
        if account_id is None:
            account_id = self.get_account_id()
        return account_id is not None and account_id.startswith("DU")

    def get_account_summary(self, account_id: Optional[str] = None) -> dict:
        """Get account summary."""
        if account_id is None:
            account_id = self.get_account_id()
        if not account_id:
            return {}

        try:
            summary = self.ib.accountSummary(account_id)
            result = {}
            for item in summary:
                result[item.tag] = item.value
            return result
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return {}


# Global connection instance
ib_conn = IBConnection()
