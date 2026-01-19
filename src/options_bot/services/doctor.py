"""Doctor command for diagnostics."""

import sys
from typing import Dict, Optional

from ..config import config
from ..logging_setup import setup_logging, get_logger
from ..ibkr.connection import ib_conn
from ..ibkr.market_data import get_stock_quote, get_option_quote
from ..ibkr.options_chain import get_option_chain

logger = get_logger(__name__)


def run_doctor():
    """Run diagnostic checks."""
    setup_logging()
    logger.info("Starting bot doctor diagnostics...")

    results = {
        "connection": False,
        "account_id": None,
        "is_paper": False,
        "market_data": False,
        "options_chain": False,
        "greeks_available": False,
        "errors": []
    }

    # 1. Connection check
    print("\n" + "=" * 60)
    print("1. IB Gateway Connection")
    print("=" * 60)
    if ib_conn.connect():
        results["connection"] = True
        print("✓ Connected to IB Gateway")
    else:
        results["errors"].append("Failed to connect to IB Gateway")
        print("✗ Failed to connect to IB Gateway")
        print("\nPlease ensure:")
        print("  - IB Gateway is running (docker compose up -d)")
        print("  - Gateway is logged in and 2FA completed")
        print("  - Port matches IB_PORT in .env")
        _print_summary(results)
        sys.exit(1)

    try:
        # 2. Account check
        print("\n" + "=" * 60)
        print("2. Account Verification")
        print("=" * 60)
        account_id = ib_conn.get_account_id()
        if account_id:
            results["account_id"] = account_id
            print(f"✓ Account ID: {account_id}")
            is_paper = ib_conn.is_paper_account(account_id)
            results["is_paper"] = is_paper
            if is_paper:
                print("✓ Paper account detected (DU prefix)")
            else:
                print("⚠ WARNING: Not a paper account (missing DU prefix)")
                print("  This may be a live account. Proceed with caution.")
        else:
            results["errors"].append("No account found")
            print("✗ No account found")

        # 3. Market data check - SPY
        print("\n" + "=" * 60)
        print("3. Market Data - SPY Quote")
        print("=" * 60)
        spy_quote = get_stock_quote("SPY")
        if spy_quote and spy_quote.get("has_bid_ask"):
            results["market_data"] = True
            print(f"✓ SPY Quote:")
            print(f"  Bid: {spy_quote.get('bid')}")
            print(f"  Ask: {spy_quote.get('ask')}")
            print(f"  Last: {spy_quote.get('last')}")
        elif spy_quote:
            print("⚠ SPY Quote retrieved but missing bid/ask")
            print("  This may indicate delayed market data")
            print(f"  Last: {spy_quote.get('last')}")
        else:
            results["errors"].append("Failed to get SPY quote")
            print("✗ Failed to get SPY quote")

        # 4. Options chain check
        print("\n" + "=" * 60)
        print("4. Options Chain - SPY")
        print("=" * 60)
        chain = get_option_chain("SPY")
        if chain and chain.expirations:
            results["options_chain"] = True
            print(f"✓ Options chain retrieved")
            print(f"  Expirations: {len(chain.expirations)}")
            print(f"  First expiration: {chain.expirations[0]}")
            print(f"  Last expiration: {chain.expirations[-1]}")
        else:
            results["errors"].append("Failed to get options chain")
            print("✗ Failed to get options chain")
            print("  This may indicate missing options permissions")

        # 5. Option quote and Greeks check
        print("\n" + "=" * 60)
        print("5. Option Quote & Greeks - SPY")
        print("=" * 60)
        if chain and chain.expirations and chain.strikes:
            # Try to get a quote for a near-the-money option
            exp = chain.expirations[0]
            strikes = chain.strikes.get(exp, [])
            if strikes:
                # Get current SPY price to find near-the-money strike
                spy_price = spy_quote.get("last") or spy_quote.get("bid") or spy_quote.get("ask")
                if spy_price:
                    # Find closest strike
                    closest_strike = min(strikes, key=lambda x: abs(x - spy_price))
                    option_quote = get_option_quote("SPY", exp, closest_strike, "P")
                    if option_quote:
                        print(f"✓ Option Quote (SPY {exp} {closest_strike} Put):")
                        print(f"  Bid: {option_quote.get('bid')}")
                        print(f"  Ask: {option_quote.get('ask')}")
                        has_bid_ask = option_quote.get("has_bid_ask", False)
                        if has_bid_ask:
                            print("  ✓ Has bid/ask")
                        else:
                            print("  ⚠ Missing bid/ask (may indicate delayed data)")

                        # Check Greeks
                        has_greeks = option_quote.get("has_greeks", False)
                        delta = option_quote.get("delta")
                        results["greeks_available"] = has_greeks
                        if has_greeks and delta is not None:
                            print(f"  ✓ Greeks available (Delta: {delta:.4f})")
                        else:
                            print("  ⚠ Greeks NOT available from market data")
                            print("    This will affect delta-based selection")
                            if config.require_greeks:
                                print("    ⚠ REQUIRE_GREEKS=true - candidates will be rejected")
                            else:
                                print("    ℹ REQUIRE_GREEKS=false - will use OTM fallback")
                    else:
                        print("✗ Failed to get option quote")
                        results["errors"].append("Failed to get option quote")
                else:
                    print("⚠ Cannot determine SPY price for option test")
            else:
                print("⚠ No strikes found for first expiration")
        else:
            print("⚠ Cannot test option quote (chain not available)")

        # Summary
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        _print_summary(results)

    finally:
        ib_conn.disconnect()


def _print_summary(results: Dict):
    """Print diagnostic summary."""
    print(f"\nConnection: {'✓' if results['connection'] else '✗'}")
    print(f"Account: {results['account_id'] or 'N/A'}")
    print(f"Paper Account: {'✓' if results['is_paper'] else '✗'}")
    print(f"Market Data: {'✓' if results['market_data'] else '✗'}")
    print(f"Options Chain: {'✓' if results['options_chain'] else '✗'}")
    print(f"Greeks Available: {'✓' if results['greeks_available'] else '✗'}")

    if results["errors"]:
        print("\nErrors:")
        for error in results["errors"]:
            print(f"  - {error}")

    if all([
        results["connection"],
        results["account_id"],
        results["market_data"],
        results["options_chain"]
    ]):
        print("\n✓ All critical checks passed!")
        if not results["greeks_available"]:
            print("⚠ Warning: Greeks not available - consider checking market data subscriptions")
    else:
        print("\n✗ Some checks failed - please review errors above")
