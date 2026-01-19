"""Database schema using SQLAlchemy."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, Float, String, Boolean, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class BotRun(Base):
    """Bot run session."""
    __tablename__ = "bot_runs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    mode = Column(String(50), nullable=False)  # 'run', 'manage', 'scan'
    notes = Column(Text, nullable=True)

    # Relationships
    trades = relationship("Trade", back_populates="bot_run")


class MarketSnapshot(Base):
    """Market data snapshot."""
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True)
    ts = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    underlying_px = Column(Float, nullable=True)
    data_json = Column(Text, nullable=True)  # JSON string of full snapshot


class Trade(Base):
    """Trade record."""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    bot_run_id = Column(Integer, ForeignKey("bot_runs.id"), nullable=True)
    ts_open = Column(DateTime, nullable=False, index=True)
    ts_close = Column(DateTime, nullable=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    exp = Column(DateTime, nullable=False)
    short_strike = Column(Float, nullable=False)
    long_strike = Column(Float, nullable=False)
    qty = Column(Integer, nullable=False)
    credit = Column(Float, nullable=False)
    debit_to_close = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="open")  # open, closed, cancelled
    pnl = Column(Float, nullable=True)
    reason_open = Column(String(100), nullable=True)
    reason_close = Column(String(100), nullable=True)

    # Relationships
    bot_run = relationship("BotRun", back_populates="trades")
    orders = relationship("Order", back_populates="trade")

    __table_args__ = (
        Index("idx_trades_symbol_status", "symbol", "status"),
    )


class Order(Base):
    """Order record."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True)
    ts = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    action = Column(String(20), nullable=False)  # 'open', 'close'
    order_type = Column(String(20), nullable=False)  # 'limit', 'market'
    limit_price = Column(Float, nullable=True)
    status = Column(String(20), nullable=False)  # 'pending', 'submitted', 'filled', 'cancelled', 'rejected'
    ib_order_id = Column(Integer, nullable=True, unique=True)
    raw_json = Column(Text, nullable=True)  # JSON string of full order

    # Relationships
    trade = relationship("Trade", back_populates="orders")
    fills = relationship("Fill", back_populates="order")


class Fill(Base):
    """Fill record."""
    __tablename__ = "fills"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    ts = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    price = Column(Float, nullable=False)
    qty = Column(Integer, nullable=False)
    raw_json = Column(Text, nullable=True)  # JSON string of full fill

    # Relationships
    order = relationship("Order", back_populates="fills")


class DailyStats(Base):
    """Daily statistics."""
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True)
    day = Column(DateTime, nullable=False, unique=True, index=True)  # Date only
    realized_pnl = Column(Float, nullable=False, default=0.0)
    unrealized_pnl = Column(Float, nullable=False, default=0.0)
    max_drawdown_est = Column(Float, nullable=False, default=0.0)
    trades_count = Column(Integer, nullable=False, default=0)
    losses_count = Column(Integer, nullable=False, default=0)
    wins_count = Column(Integer, nullable=False, default=0)
