"""Configuration management from environment variables."""

import os
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Application configuration from environment variables."""

    # IB Connection
    ib_host: str = "127.0.0.1"
    ib_port: int = 4002
    ib_client_id: int = 7
    ib_readonly: bool = False
    ib_account_id: str = ""

    # Timezone
    timezone: str = "America/New_York"

    # Safety Settings
    trading_disabled: bool = True
    account_size: float = 1000.0
    risk_per_trade_pct: float = 0.02
    max_daily_loss_pct: float = 0.03
    max_trades_per_day: int = 2

    # Strategy Parameters
    underlyings: List[str] = None
    dte_min: int = 7
    dte_max: int = 21
    delta_min: float = 0.15
    delta_max: float = 0.25
    spread_width: float = 1.0
    leg_max_bidask: float = 0.10
    require_greeks: bool = True
    otm_target_pct: float = 0.04

    # Exit Management
    tp_capture_pct: float = 0.50
    sl_multiple: float = 2.0
    time_exit_dte: int = 3

    # Execution
    entry_window_start: str = "10:00"
    entry_window_end: str = "11:00"
    manage_interval_seconds: int = 300
    entry_max_slippage: float = 0.05
    entry_retry_seconds: int = 60

    # Database
    db_path: str = "./data/bot.db"

    # Logging
    log_dir: str = "./logs"
    log_max_bytes: int = 10485760
    log_backup_count: int = 5

    # AI Advisor
    ai_advisor_enabled: bool = False
    ai_advisor_provider: str = "ollama"
    ai_advisor_model: str = "llama3.2"
    ai_advisor_api_url: str = "http://localhost:11434"
    ai_advisor_api_key: str = ""

    def __post_init__(self):
        """Parse environment variables after initialization."""
        # IB Connection
        self.ib_host = os.getenv("IB_HOST", self.ib_host)
        self.ib_port = int(os.getenv("IB_PORT", self.ib_port))
        self.ib_client_id = int(os.getenv("IB_CLIENT_ID", self.ib_client_id))
        self.ib_readonly = os.getenv("IB_READONLY", "false").lower() == "true"
        self.ib_account_id = os.getenv("IB_ACCOUNT_ID", self.ib_account_id)

        # Timezone
        self.timezone = os.getenv("TIMEZONE", self.timezone)

        # Safety Settings
        self.trading_disabled = os.getenv("TRADING_DISABLED", "true").lower() == "true"
        self.account_size = float(os.getenv("ACCOUNT_SIZE", self.account_size))
        self.risk_per_trade_pct = float(os.getenv("RISK_PER_TRADE_PCT", self.risk_per_trade_pct))
        self.max_daily_loss_pct = float(os.getenv("MAX_DAILY_LOSS_PCT", self.max_daily_loss_pct))
        self.max_trades_per_day = int(os.getenv("MAX_TRADES_PER_DAY", self.max_trades_per_day))

        # Strategy Parameters
        underlyings_str = os.getenv("UNDERLYINGS", "SPY,QQQ")
        self.underlyings = [s.strip().upper() for s in underlyings_str.split(",")]
        self.dte_min = int(os.getenv("DTE_MIN", self.dte_min))
        self.dte_max = int(os.getenv("DTE_MAX", self.dte_max))
        self.delta_min = float(os.getenv("DELTA_MIN", self.delta_min))
        self.delta_max = float(os.getenv("DELTA_MAX", self.delta_max))
        self.spread_width = float(os.getenv("SPREAD_WIDTH", self.spread_width))
        self.leg_max_bidask = float(os.getenv("LEG_MAX_BIDASK", self.leg_max_bidask))
        self.require_greeks = os.getenv("REQUIRE_GREEKS", "true").lower() == "true"
        self.otm_target_pct = float(os.getenv("OTM_TARGET_PCT", self.otm_target_pct))

        # Exit Management
        self.tp_capture_pct = float(os.getenv("TP_CAPTURE_PCT", self.tp_capture_pct))
        self.sl_multiple = float(os.getenv("SL_MULTIPLE", self.sl_multiple))
        self.time_exit_dte = int(os.getenv("TIME_EXIT_DTE", self.time_exit_dte))

        # Execution
        self.entry_window_start = os.getenv("ENTRY_WINDOW_START", self.entry_window_start)
        self.entry_window_end = os.getenv("ENTRY_WINDOW_END", self.entry_window_end)
        self.manage_interval_seconds = int(os.getenv("MANAGE_INTERVAL_SECONDS", self.manage_interval_seconds))
        self.entry_max_slippage = float(os.getenv("ENTRY_MAX_SLIPPAGE", self.entry_max_slippage))
        self.entry_retry_seconds = int(os.getenv("ENTRY_RETRY_SECONDS", self.entry_retry_seconds))

        # Database
        self.db_path = os.getenv("DB_PATH", self.db_path)

        # Logging
        self.log_dir = os.getenv("LOG_DIR", self.log_dir)
        self.log_max_bytes = int(os.getenv("LOG_MAX_BYTES", self.log_max_bytes))
        self.log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", self.log_backup_count))

        # AI Advisor
        self.ai_advisor_enabled = os.getenv("AI_ADVISOR_ENABLED", "false").lower() == "true"
        self.ai_advisor_provider = os.getenv("AI_ADVISOR_PROVIDER", self.ai_advisor_provider)
        self.ai_advisor_model = os.getenv("AI_ADVISOR_MODEL", self.ai_advisor_model)
        self.ai_advisor_api_url = os.getenv("AI_ADVISOR_API_URL", self.ai_advisor_api_url)
        self.ai_advisor_api_key = os.getenv("AI_ADVISOR_API_KEY", self.ai_advisor_api_key)


# Global config instance
config = Config()
