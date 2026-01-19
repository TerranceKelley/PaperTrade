"""Timezone and time utilities for ET handling."""

from datetime import datetime, time
from typing import Optional
import pytz

from .config import config

# ET timezone
ET = pytz.timezone(config.timezone)


def now_et() -> datetime:
    """Get current time in ET timezone."""
    return datetime.now(ET)


def now_utc() -> datetime:
    """Get current time in UTC."""
    return datetime.utcnow().replace(tzinfo=pytz.UTC)


def et_to_utc(dt: datetime) -> datetime:
    """Convert ET datetime to UTC."""
    if dt.tzinfo is None:
        dt = ET.localize(dt)
    return dt.astimezone(pytz.UTC)


def utc_to_et(dt: datetime) -> datetime:
    """Convert UTC datetime to ET."""
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    return dt.astimezone(ET)


def parse_time(time_str: str) -> time:
    """Parse time string in HH:MM format."""
    hour, minute = map(int, time_str.split(":"))
    return time(hour, minute)


def is_in_entry_window() -> bool:
    """Check if current time is within entry window."""
    now = now_et()
    window_start = parse_time(config.entry_window_start)
    window_end = parse_time(config.entry_window_end)
    current_time = now.time()

    return window_start <= current_time <= window_end


def days_to_expiration(exp_date: datetime, current_date: Optional[datetime] = None) -> int:
    """Calculate days to expiration."""
    if current_date is None:
        current_date = now_et()
    if exp_date.tzinfo is None:
        exp_date = ET.localize(exp_date)
    if current_date.tzinfo is None:
        current_date = ET.localize(current_date)
    delta = exp_date.date() - current_date.date()
    return delta.days
