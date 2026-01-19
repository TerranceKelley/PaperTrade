"""CLI entrypoint using Typer."""

import typer
from typing import Optional

from .logging_setup import setup_logging

# Initialize logging
setup_logging()

app = typer.Typer(help="Options paper trading bot for Interactive Brokers")


@app.command()
def doctor():
    """Verify connectivity, paper account, market data, and options chain."""
    from .services.doctor import run_doctor
    run_doctor()


@app.command()
def scan():
    """Print candidate spreads per ticker."""
    from .services.scanner import scan_all_symbols, print_scan_results
    results = scan_all_symbols()
    print_scan_results(results)


@app.command()
def run(
    session: int = typer.Option(120, "--session", "-s", help="Session duration in minutes")
):
    """Run trading session with scanning and management."""
    from .services.runner import run_session
    run_session(session)


@app.command()
def manage():
    """Manage existing positions only (no new entries)."""
    from .services.runner import run_manage_only
    run_manage_only()


@app.command()
def report():
    """Print today's trades, P/L, win rate, and open risk."""
    from .services.reporter import print_daily_report
    print_daily_report()


@app.command()
def export(
    csv: str = typer.Option(..., "--csv", help="Output CSV file path")
):
    """Export trades/orders/fills to CSV."""
    from .services.exporter import export_to_csv
    export_to_csv(csv)


if __name__ == "__main__":
    app()
