"""BAG combo order creation and execution."""

import time
import json
from typing import Optional, Dict
from ib_insync import LimitOrder, ComboLeg, Contract, Order, Stock, Option

from ..config import config
from ..logging_setup import get_logger
from ..db.repo import repo
from .connection import ib_conn

logger = get_logger(__name__)


def create_combo_order(
    symbol: str,
    expiration: str,
    short_strike: float,
    long_strike: float,
    action: str,  # "BUY" or "SELL"
    quantity: int,
    limit_price: float
) -> Optional[Contract]:
    """Create a BAG combo order contract for put credit spread."""
    try:
        # Create underlying stock contract
        stock = Stock(symbol, "SMART", "USD")
        ib_conn.ib.qualifyContracts(stock)

        # Create option contracts
        short_put = Option(symbol, expiration, short_strike, "P", "SMART")
        long_put = Option(symbol, expiration, long_strike, "P", "SMART")

        ib_conn.ib.qualifyContracts(short_put, long_put)

        # Create combo contract (BAG)
        combo = Contract()
        combo.symbol = symbol
        combo.secType = "BAG"
        combo.currency = "USD"
        combo.exchange = "SMART"

        # Create combo legs
        # For put credit spread: SELL short put, BUY long put
        if action == "SELL":
            # Opening: sell short put, buy long put
            combo.comboLegs = [
                ComboLeg(conId=short_put.conId, ratio=1, action="SELL", exchange="SMART"),
                ComboLeg(conId=long_put.conId, ratio=1, action="BUY", exchange="SMART"),
            ]
        else:
            # Closing: buy short put, sell long put
            combo.comboLegs = [
                ComboLeg(conId=short_put.conId, ratio=1, action="BUY", exchange="SMART"),
                ComboLeg(conId=long_put.conId, ratio=1, action="SELL", exchange="SMART"),
            ]

        return combo
    except Exception as e:
        logger.error(f"Error creating combo order: {e}")
        return None


def place_combo_order(
    combo: Contract,
    quantity: int,
    limit_price: float,
    action: str
) -> Optional[Order]:
    """Place a combo limit order."""
    if not ib_conn.is_connected():
        logger.error("Not connected to IB")
        return None

    if config.trading_disabled:
        logger.warning("Trading is disabled - order not placed")
        return None

    try:
        # Create limit order
        order = LimitOrder(action, quantity, limit_price)
        order.tif = "DAY"  # Day order

        # Place order
        trade = ib_conn.ib.placeOrder(combo, order)
        logger.info(f"Placed {action} order for {quantity} contracts at {limit_price}")

        # Store order in database
        repo.create_order(
            trade_id=None,  # Will be updated when trade is created
            action=action.lower(),
            order_type="limit",
            limit_price=limit_price,
            status="submitted",
            ib_order_id=trade.order.orderId if trade.order else None,
            raw_json=json.dumps({
                "symbol": combo.symbol,
                "quantity": quantity,
                "limit_price": limit_price,
                "action": action
            })
        )

        return trade.order
    except Exception as e:
        logger.error(f"Error placing combo order: {e}")
        return None


def place_spread_order_open(
    symbol: str,
    expiration: str,
    short_strike: float,
    long_strike: float,
    quantity: int,
    target_credit: float
) -> Optional[Dict]:
    """Place order to open a put credit spread with retry logic."""
    if config.trading_disabled:
        logger.warning("Trading is disabled - order not placed")
        return None

    # Create combo contract
    combo = create_combo_order(symbol, expiration, short_strike, long_strike, "SELL", quantity, target_credit)
    if not combo:
        return None

    # Try placing order with price adjustments
    max_attempts = 5
    price_adjustment = 0.0
    max_adjustment = config.entry_max_slippage

    for attempt in range(max_attempts):
        limit_price = target_credit - price_adjustment
        if limit_price <= 0:
            logger.warning(f"Limit price too low: {limit_price}")
            break

        logger.info(f"Attempt {attempt + 1}: placing order at {limit_price} (target: {target_credit})")

        order = place_combo_order(combo, quantity, limit_price, "SELL")
        if order:
            # Wait for fill or timeout
            trade = ib_conn.ib.reqAllOpenOrders()
            # Check if order filled (simplified - in production, monitor order status)
            time.sleep(2)  # Give it a moment

            # Return order info
            return {
                "order": order,
                "combo": combo,
                "limit_price": limit_price,
                "quantity": quantity
            }

        # Adjust price for next attempt
        price_adjustment += 0.01
        if price_adjustment > max_adjustment:
            logger.warning(f"Max slippage exceeded, cancelling order")
            break

        time.sleep(1)

    logger.error("Failed to place order after all attempts")
    return None


def place_spread_order_close(
    symbol: str,
    expiration: str,
    short_strike: float,
    long_strike: float,
    quantity: int,
    target_debit: float
) -> Optional[Dict]:
    """Place order to close a put credit spread."""
    if config.trading_disabled:
        logger.warning("Trading is disabled - order not placed")
        return None

    # Create combo contract
    combo = create_combo_order(symbol, expiration, short_strike, long_strike, "BUY", quantity, target_debit)
    if not combo:
        return None

    # Place order
    order = place_combo_order(combo, quantity, target_debit, "BUY")
    if order:
        return {
            "order": order,
            "combo": combo,
            "limit_price": target_debit,
            "quantity": quantity
        }

    return None
