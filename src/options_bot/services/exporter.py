"""Export service for CSV export."""

import csv
from datetime import datetime
from typing import List

from ..db.repo import repo
from ..db.schema import Trade, Order, Fill
from ..logging_setup import get_logger

logger = get_logger(__name__)


def export_to_csv(filepath: str):
    """Export trades, orders, and fills to CSV."""
    with repo.get_session() as session:
        # Get all trades
        trades = session.query(Trade).all()
        orders = session.query(Order).all()
        fills = session.query(Fill).all()

    # Write trades
    trades_file = filepath.replace(".csv", "_trades.csv")
    with open(trades_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "ts_open", "ts_close", "symbol", "exp", "short_strike", "long_strike",
            "qty", "credit", "debit_to_close", "status", "pnl", "reason_open", "reason_close"
        ])
        for trade in trades:
            writer.writerow([
                trade.id,
                trade.ts_open.isoformat() if trade.ts_open else "",
                trade.ts_close.isoformat() if trade.ts_close else "",
                trade.symbol,
                trade.exp.isoformat() if trade.exp else "",
                trade.short_strike,
                trade.long_strike,
                trade.qty,
                trade.credit,
                trade.debit_to_close,
                trade.status,
                trade.pnl,
                trade.reason_open,
                trade.reason_close
            ])

    # Write orders
    orders_file = filepath.replace(".csv", "_orders.csv")
    with open(orders_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "trade_id", "ts", "action", "order_type", "limit_price",
            "status", "ib_order_id"
        ])
        for order in orders:
            writer.writerow([
                order.id,
                order.trade_id,
                order.ts.isoformat() if order.ts else "",
                order.action,
                order.order_type,
                order.limit_price,
                order.status,
                order.ib_order_id
            ])

    # Write fills
    fills_file = filepath.replace(".csv", "_fills.csv")
    with open(fills_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "order_id", "ts", "price", "qty"
        ])
        for fill in fills:
            writer.writerow([
                fill.id,
                fill.order_id,
                fill.ts.isoformat() if fill.ts else "",
                fill.price,
                fill.qty
            ])

    logger.info(f"Exported data to {trades_file}, {orders_file}, {fills_file}")
    print(f"Exported to:")
    print(f"  - {trades_file}")
    print(f"  - {orders_file}")
    print(f"  - {fills_file}")
