"""
validators.py - Input validation for order parameters.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

from bot.logging_config import get_logger

logger = get_logger("validators")

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}


class ValidationError(ValueError):
    """Raised when order parameter validation fails."""


def _positive_decimal(value: str, field: str) -> Decimal:
    """Parse *value* as a positive Decimal or raise ValidationError."""
    try:
        d = Decimal(str(value))
    except InvalidOperation:
        raise ValidationError(f"'{field}' must be a valid number, got: {value!r}")
    if d <= 0:
        raise ValidationError(f"'{field}' must be greater than zero, got: {d}")
    return d


def validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not s.isalnum():
        raise ValidationError(f"Symbol must be alphanumeric, got: {symbol!r}")
    if len(s) < 4 or len(s) > 12:
        raise ValidationError(f"Symbol length looks wrong: {s!r}")
    return s


def validate_side(side: str) -> str:
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValidationError(f"Side must be one of {sorted(VALID_SIDES)}, got: {side!r}")
    return s


def validate_order_type(order_type: str) -> str:
    t = order_type.strip().upper()
    if t not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Order type must be one of {sorted(VALID_ORDER_TYPES)}, got: {order_type!r}"
        )
    return t


def validate_quantity(quantity) -> Decimal:
    return _positive_decimal(quantity, "quantity")


def validate_price(price, order_type: str) -> Optional[Decimal]:
    order_type = order_type.strip().upper()
    if order_type == "MARKET":
        if price is not None:
            logger.warning("Price is ignored for MARKET orders.")
        return None
    if price is None:
        raise ValidationError(f"Price is required for {order_type} orders.")
    return _positive_decimal(price, "price")


def validate_stop_price(stop_price, order_type: str) -> Optional[Decimal]:
    order_type = order_type.strip().upper()
    if order_type != "STOP_LIMIT":
        return None
    if stop_price is None:
        raise ValidationError("stop_price is required for STOP_LIMIT orders.")
    return _positive_decimal(stop_price, "stop_price")


def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity,
    price=None,
    stop_price=None,
) -> dict:
    """
    Validate all order parameters and return a cleaned dict.
    Raises ValidationError on any invalid input.
    """
    clean = {}
    clean["symbol"] = validate_symbol(symbol)
    clean["side"] = validate_side(side)
    clean["order_type"] = validate_order_type(order_type)
    clean["quantity"] = validate_quantity(quantity)
    clean["price"] = validate_price(price, clean["order_type"])
    clean["stop_price"] = validate_stop_price(stop_price, clean["order_type"])

    logger.debug("Validated order params: %s", clean)
    return clean
