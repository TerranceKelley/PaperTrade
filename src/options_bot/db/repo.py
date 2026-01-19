"""Database repository with CRUD operations."""

from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session

from .schema import Base, BotRun, MarketSnapshot, Trade, Order, Fill, DailyStats
from ..config import config


class Repository:
    """Database repository."""

    def __init__(self):
        """Initialize database connection."""
        # Ensure directory exists
        from pathlib import Path
        db_path = Path(config.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.engine = create_engine(f"sqlite:///{config.db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    # BotRun operations
    def create_bot_run(self, mode: str, notes: Optional[str] = None) -> BotRun:
        """Create a new bot run."""
        with self.get_session() as session:
            bot_run = BotRun(mode=mode, notes=notes, started_at=datetime.utcnow())
            session.add(bot_run)
            session.commit()
            session.refresh(bot_run)
            return bot_run

    def update_bot_run(self, run_id: int, ended_at: Optional[datetime] = None, notes: Optional[str] = None):
        """Update bot run."""
        with self.get_session() as session:
            bot_run = session.query(BotRun).filter(BotRun.id == run_id).first()
            if bot_run:
                if ended_at:
                    bot_run.ended_at = ended_at
                if notes:
                    bot_run.notes = notes
                session.commit()

    # MarketSnapshot operations
    def create_market_snapshot(self, symbol: str, underlying_px: Optional[float], data_json: Optional[str]) -> MarketSnapshot:
        """Create a market snapshot."""
        with self.get_session() as session:
            snapshot = MarketSnapshot(
                symbol=symbol,
                underlying_px=underlying_px,
                data_json=data_json,
                ts=datetime.utcnow()
            )
            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)
            return snapshot

    # Trade operations
    def create_trade(
        self,
        bot_run_id: Optional[int],
        symbol: str,
        exp: datetime,
        short_strike: float,
        long_strike: float,
        qty: int,
        credit: float,
        reason_open: Optional[str] = None
    ) -> Trade:
        """Create a new trade."""
        with self.get_session() as session:
            trade = Trade(
                bot_run_id=bot_run_id,
                ts_open=datetime.utcnow(),
                symbol=symbol,
                exp=exp,
                short_strike=short_strike,
                long_strike=long_strike,
                qty=qty,
                credit=credit,
                status="open",
                reason_open=reason_open
            )
            session.add(trade)
            session.commit()
            session.refresh(trade)
            return trade

    def get_open_trades(self, symbol: Optional[str] = None) -> List[Trade]:
        """Get open trades, optionally filtered by symbol."""
        with self.get_session() as session:
            query = session.query(Trade).filter(Trade.status == "open")
            if symbol:
                query = query.filter(Trade.symbol == symbol)
            return query.all()

    def update_trade(
        self,
        trade_id: int,
        status: Optional[str] = None,
        debit_to_close: Optional[float] = None,
        pnl: Optional[float] = None,
        reason_close: Optional[str] = None
    ):
        """Update trade."""
        with self.get_session() as session:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if trade:
                if status:
                    trade.status = status
                if debit_to_close is not None:
                    trade.debit_to_close = debit_to_close
                if pnl is not None:
                    trade.pnl = pnl
                if reason_close:
                    trade.reason_close = reason_close
                if status == "closed":
                    trade.ts_close = datetime.utcnow()
                session.commit()

    # Order operations
    def create_order(
        self,
        trade_id: Optional[int],
        action: str,
        order_type: str,
        limit_price: Optional[float],
        status: str = "pending",
        ib_order_id: Optional[int] = None,
        raw_json: Optional[str] = None
    ) -> Order:
        """Create a new order."""
        with self.get_session() as session:
            order = Order(
                trade_id=trade_id,
                action=action,
                order_type=order_type,
                limit_price=limit_price,
                status=status,
                ib_order_id=ib_order_id,
                raw_json=raw_json,
                ts=datetime.utcnow()
            )
            session.add(order)
            session.commit()
            session.refresh(order)
            return order

    def update_order(self, order_id: int, status: Optional[str] = None, ib_order_id: Optional[int] = None):
        """Update order."""
        with self.get_session() as session:
            order = session.query(Order).filter(Order.id == order_id).first()
            if order:
                if status:
                    order.status = status
                if ib_order_id:
                    order.ib_order_id = ib_order_id
                session.commit()

    # Fill operations
    def create_fill(self, order_id: int, price: float, qty: int, raw_json: Optional[str] = None) -> Fill:
        """Create a fill record."""
        with self.get_session() as session:
            fill = Fill(
                order_id=order_id,
                price=price,
                qty=qty,
                raw_json=raw_json,
                ts=datetime.utcnow()
            )
            session.add(fill)
            session.commit()
            session.refresh(fill)
            return fill

    # DailyStats operations
    def get_or_create_daily_stats(self, day: date) -> DailyStats:
        """Get or create daily stats for a date."""
        with self.get_session() as session:
            day_dt = datetime.combine(day, datetime.min.time())
            stats = session.query(DailyStats).filter(
                func.date(DailyStats.day) == day
            ).first()
            if not stats:
                stats = DailyStats(day=day_dt)
                session.add(stats)
                session.commit()
                session.refresh(stats)
            return stats

    def update_daily_stats(
        self,
        day: date,
        realized_pnl: Optional[float] = None,
        unrealized_pnl: Optional[float] = None,
        trades_count: Optional[int] = None,
        wins_count: Optional[int] = None,
        losses_count: Optional[int] = None
    ):
        """Update daily stats."""
        stats = self.get_or_create_daily_stats(day)
        with self.get_session() as session:
            stats = session.query(DailyStats).filter(DailyStats.id == stats.id).first()
            if stats:
                if realized_pnl is not None:
                    stats.realized_pnl = realized_pnl
                if unrealized_pnl is not None:
                    stats.unrealized_pnl = unrealized_pnl
                if trades_count is not None:
                    stats.trades_count = trades_count
                if wins_count is not None:
                    stats.wins_count = wins_count
                if losses_count is not None:
                    stats.losses_count = losses_count
                session.commit()


# Global repository instance
repo = Repository()
