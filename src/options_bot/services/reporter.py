"""Reporting service."""

from datetime import date, datetime
from typing import List

from ..db.repo import repo
from ..db.schema import Trade, DailyStats
from ..logging_setup import get_logger

logger = get_logger(__name__)


def generate_daily_report() -> str:
    """Generate daily report."""
    today = date.today()

    # Get daily stats
    stats = repo.get_or_create_daily_stats(today)

    # Get today's trades
    with repo.get_session() as session:
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        trades = session.query(Trade).filter(
            Trade.ts_open >= today_start,
            Trade.ts_open <= today_end
        ).all()

    # Calculate metrics
    open_trades = repo.get_open_trades()
    total_pnl = stats.realized_pnl + stats.unrealized_pnl
    win_rate = 0.0
    if stats.wins_count + stats.losses_count > 0:
        win_rate = stats.wins_count / (stats.wins_count + stats.losses_count)

    # Build report
    report = []
    report.append("\n" + "=" * 80)
    report.append("DAILY REPORT")
    report.append("=" * 80)
    report.append(f"Date: {today}")
    report.append("")
    report.append("Performance:")
    report.append(f"  Realized P/L: ${stats.realized_pnl:.2f}")
    report.append(f"  Unrealized P/L: ${stats.unrealized_pnl:.2f}")
    report.append(f"  Total P/L: ${total_pnl:.2f}")
    report.append(f"  Win Rate: {win_rate:.1%}")
    report.append("")
    report.append("Trades:")
    report.append(f"  Opened Today: {stats.trades_count}")
    report.append(f"  Wins: {stats.wins_count}")
    report.append(f"  Losses: {stats.losses_count}")
    report.append(f"  Open Positions: {len(open_trades)}")
    report.append("")

    if trades:
        report.append("Today's Trades:")
        report.append("-" * 80)
        report.append(f"{'Symbol':<8} {'Exp':<12} {'Strikes':<20} {'Status':<10} {'P/L':<10}")
        report.append("-" * 80)
        for trade in trades:
            strikes = f"{trade.short_strike}/{trade.long_strike}"
            pnl_str = f"${trade.pnl:.2f}" if trade.pnl else "N/A"
            report.append(f"{trade.symbol:<8} {trade.exp.strftime('%Y%m%d'):<12} {strikes:<20} "
                         f"{trade.status:<10} {pnl_str:<10}")

    if open_trades:
        report.append("")
        report.append("Open Positions:")
        report.append("-" * 80)
        report.append(f"{'Symbol':<8} {'Exp':<12} {'Strikes':<20} {'Credit':<10} {'DTE':<5}")
        report.append("-" * 80)
        from ..time_utils import days_to_expiration, now_et
        for trade in open_trades:
            strikes = f"{trade.short_strike}/{trade.long_strike}"
            dte = days_to_expiration(trade.exp, now_et())
            report.append(f"{trade.symbol:<8} {trade.exp.strftime('%Y%m%d'):<12} {strikes:<20} "
                         f"${trade.credit:<9.2f} {dte:<5}")

    report.append("\n" + "=" * 80)

    return "\n".join(report)


def print_daily_report():
    """Print daily report to console."""
    report = generate_daily_report()
    print(report)
