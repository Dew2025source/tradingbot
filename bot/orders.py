"""
orders.py - Order placement logic for Binance Futures Testnet.

Translates validated order parameters into API calls and returns
normalised OrderResult objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, Optional

from bot.client import BinanceFuturesClient, BinanceAPIError
from bot.logging_config import get_logger

logger = get_logger("orders")

ORDER_ENDPOINT = "/fapi/v1/order"


@dataclass
class OrderResult:
    """Normalised representation of a Binance order response."""

    order_id: int
    symbol: str
    side: str
    order_type: str
    status: str
    orig_qty: str
    executed_qty: str
    avg_price: str
    price: str  # limit price sent
    client_order_id: str
    time_in_force: str
    raw: Dict[str, Any] = field(repr=False, default_factory=dict)

    @classmethod
    def from_response(cls, data: dict) -> "OrderResult":
        return cls(
            order_id=data.get("orderId", 0),
            symbol=data.get("symbol", ""),
            side=data.get("side", ""),
            order_type=data.get("type", ""),
            status=data.get("status", ""),
            orig_qty=data.get("origQty", "0"),
            executed_qty=data.get("executedQty", "0"),
            avg_price=data.get("avgPrice", "0"),
            price=data.get("price", "0"),
            client_order_id=data.get("clientOrderId", ""),
            time_in_force=data.get("timeInForce", ""),
            raw=data,
        )

    def summary(self) -> str:
        lines = [
            "─" * 50,
            f"  Order ID     : {self.order_id}",
            f"  Symbol       : {self.symbol}",
            f"  Side         : {self.side}",
            f"  Type         : {self.order_type}",
            f"  Status       : {self.status}",
            f"  Orig Qty     : {self.orig_qty}",
            f"  Executed Qty : {self.executed_qty}",
        ]
        if float(self.avg_price or 0) > 0:
            lines.append(f"  Avg Price    : {self.avg_price}")
        if self.order_type != "MARKET" and float(self.price or 0) > 0:
            lines.append(f"  Limit Price  : {self.price}")
        lines.append(f"  Client OID   : {self.client_order_id}")
        lines.append("─" * 50)
        return "\n".join(lines)


class OrderManager:
    """
    High-level order operations built on top of BinanceFuturesClient.
    """

    def __init__(self, client: BinanceFuturesClient):
        self._client = client

    # ------------------------------------------------------------------
    # Core placement
    # ------------------------------------------------------------------

    def _place(self, params: dict) -> OrderResult:
        logger.info(
            "Placing order: symbol=%s side=%s type=%s qty=%s price=%s",
            params.get("symbol"),
            params.get("side"),
            params.get("type"),
            params.get("quantity"),
            params.get("price", "N/A"),
        )
        response = self._client.post(ORDER_ENDPOINT, params=params)
        logger.info(
            "Order placed successfully: orderId=%s status=%s executedQty=%s",
            response.get("orderId"),
            response.get("status"),
            response.get("executedQty"),
        )
        return OrderResult.from_response(response)

    # ------------------------------------------------------------------
    # Market order
    # ------------------------------------------------------------------

    def place_market_order(self, symbol: str, side: str, quantity: Decimal) -> OrderResult:
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": str(quantity),
        }
        return self._place(params)

    # ------------------------------------------------------------------
    # Limit order
    # ------------------------------------------------------------------

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        time_in_force: str = "GTC",
    ) -> OrderResult:
        params = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "quantity": str(quantity),
            "price": str(price),
            "timeInForce": time_in_force,
        }
        return self._place(params)

    # ------------------------------------------------------------------
    # Bonus: Stop-Limit order
    # ------------------------------------------------------------------

    def place_stop_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        stop_price: Decimal,
        time_in_force: str = "GTC",
    ) -> OrderResult:
        """
        Stop-Limit order: triggers at *stop_price*, then places a limit order at *price*.
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": "STOP",
            "quantity": str(quantity),
            "price": str(price),
            "stopPrice": str(stop_price),
            "timeInForce": time_in_force,
        }
        return self._place(params)

    # ------------------------------------------------------------------
    # Dispatch helper (used by CLI)
    # ------------------------------------------------------------------

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
    ) -> OrderResult:
        """Route to the correct placement method based on order_type."""
        if order_type == "MARKET":
            return self.place_market_order(symbol, side, quantity)
        elif order_type == "LIMIT":
            return self.place_limit_order(symbol, side, quantity, price)  # type: ignore[arg-type]
        elif order_type == "STOP_LIMIT":
            return self.place_stop_limit_order(symbol, side, quantity, price, stop_price)  # type: ignore[arg-type]
        else:
            raise ValueError(f"Unknown order type: {order_type}")
