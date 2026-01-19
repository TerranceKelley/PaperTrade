"""Scanner service for finding candidates."""

from ..config import config
from ..logging_setup import get_logger
from ..ibkr.connection import ib_conn
from ..strategy.selector import get_top_candidates, SpreadCandidate

logger = get_logger(__name__)


def scan_all_symbols() -> dict[str, list[SpreadCandidate]]:
    """Scan all configured symbols for candidates."""
    results = {}

    if not ib_conn.connect():
        logger.error("Failed to connect to IB Gateway")
        return results

    try:
        for symbol in config.underlyings:
            logger.info(f"Scanning {symbol}...")
            candidates = get_top_candidates(symbol, limit=5)
            results[symbol] = candidates
            logger.info(f"Found {len(candidates)} candidates for {symbol}")

    finally:
        ib_conn.disconnect()

    return results


def print_scan_results(results: dict[str, list[SpreadCandidate]]):
    """Print scan results in a formatted way."""
    print("\n" + "=" * 80)
    print("SCAN RESULTS - Put Credit Spread Candidates")
    print("=" * 80)

    for symbol, candidates in results.items():
        if not candidates:
            print(f"\n{symbol}: No candidates found")
            continue

        print(f"\n{symbol}: {len(candidates)} candidates")
        print("-" * 80)
        print(f"{'Exp':<12} {'DTE':<5} {'Short':<8} {'Long':<8} {'Delta':<8} {'Credit':<8} {'Max Loss':<10} {'Method':<15}")
        print("-" * 80)

        for cand in candidates:
            delta_str = f"{cand.short_delta:.3f}" if cand.short_delta else "N/A"
            print(f"{cand.expiration:<12} {cand.dte:<5} {cand.short_strike:<8.2f} {cand.long_strike:<8.2f} "
                  f"{delta_str:<8} ${cand.credit:<7.2f} ${cand.max_loss:<9.2f} {cand.selection_method:<15}")

    print("\n" + "=" * 80)
