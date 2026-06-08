#!/usr/bin/env python3
"""
cli.py - Command-line interface for the Binance Futures Testnet trading bot.

Usage examples
--------------
# Market BUY
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Limit SELL
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 70000

# Stop-Limit BUY (bonus order type)
python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.001 --price 68000 --stop-price 67500

Credentials can be passed via CLI flags or environment variables:
  BINANCE_API_KEY
  BINANCE_API_SECRET
"""

from __future__ import annotations

import argparse
import os
import sys
import textwrap

from bot.client import BinanceFuturesClient, BinanceAPIError
from bot.logging_config import setup_logging, get_logger
from bot.orders import OrderManager
from bot.validators import validate_order_params, ValidationError

# ── Colours (degrade gracefully on Windows / no-TTY) ─────────────────────────
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"

def _c(colour: str, text: str) -> str:
    return f"{colour}{text}{RESET}" if sys.stdout.isatty() else text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """\
            Binance Futures Testnet – Order Placement CLI
            ─────────────────────────────────────────────
            Place MARKET, LIMIT, or STOP_LIMIT orders on the
            Binance Futures USDT-M Testnet.
            """
        ),
        epilog=textwrap.dedent(
            """\
            Examples:
              python cli.py --symbol BTCUSDT --side BUY  --type MARKET     --quantity 0.001
              python cli.py --symbol BTCUSDT --side SELL --type LIMIT       --quantity 0.001 --price 70000
              python cli.py --symbol BTCUSDT --side BUY  --type STOP_LIMIT  --quantity 0.001 --price 68000 --stop-price 67500
            """
        ),
    )

    # ── Order parameters ──────────────────────────────────────────────────────
    order_group = parser.add_argument_group("Order parameters")
    order_group.add_argument(
        "--symbol", required=True, metavar="SYMBOL",
        help="Trading pair, e.g. BTCUSDT",
    )
    order_group.add_argument(
        "--side", required=True, choices=["BUY", "SELL"],
        help="Order side: BUY or SELL",
    )
    order_group.add_argument(
        "--type", dest="order_type", required=True,
        choices=["MARKET", "LIMIT", "STOP_LIMIT"],
        metavar="TYPE",
        help="Order type: MARKET | LIMIT | STOP_LIMIT",
    )
    order_group.add_argument(
        "--quantity", required=True, metavar="QTY",
        help="Order quantity (base asset)",
    )
    order_group.add_argument(
        "--price", default=None, metavar="PRICE",
        help="Limit price (required for LIMIT and STOP_LIMIT)",
    )
    order_group.add_argument(
        "--stop-price", dest="stop_price", default=None, metavar="STOP_PRICE",
        help="Stop trigger price (required for STOP_LIMIT)",
    )

    # ── Credentials ───────────────────────────────────────────────────────────
    cred_group = parser.add_argument_group(
        "Credentials",
        "May also be supplied via BINANCE_API_KEY / BINANCE_API_SECRET env vars.",
    )
    cred_group.add_argument("--api-key", default=None, metavar="KEY")
    cred_group.add_argument("--api-secret", default=None, metavar="SECRET")

    # ── Misc ──────────────────────────────────────────────────────────────────
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Console log verbosity (default: INFO)",
    )

    return parser


def resolve_credentials(args: argparse.Namespace) -> tuple[str, str]:
    api_key = args.api_key or os.environ.get("BINANCE_API_KEY", "")
    api_secret = args.api_secret or os.environ.get("BINANCE_API_SECRET", "")
    if not api_key or not api_secret:
        print(
            _c(RED, "\n[ERROR] API credentials are required.\n")
            + "  Pass --api-key / --api-secret flags, or set the environment variables:\n"
            + "    BINANCE_API_KEY\n"
            + "    BINANCE_API_SECRET\n"
        )
        sys.exit(1)
    return api_key, api_secret


def print_request_summary(params: dict) -> None:
    print()
    print(_c(BOLD, "┌── Order Request Summary ─────────────────────────────"))
    print(f"│  Symbol     : {_c(CYAN, params['symbol'])}")
    print(f"│  Side       : {_c(YELLOW, params['side'])}")
    print(f"│  Type       : {params['order_type']}")
    print(f"│  Quantity   : {params['quantity']}")
    if params.get("price"):
        print(f"│  Price      : {params['price']}")
    if params.get("stop_price"):
        print(f"│  Stop Price : {params['stop_price']}")
    print(_c(BOLD, "└──────────────────────────────────────────────────────"))
    print()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # ── Logging ───────────────────────────────────────────────────────────────
    setup_logging(args.log_level)
    logger = get_logger("cli")
    logger.debug("CLI args: %s", vars(args))

    # ── Credentials ───────────────────────────────────────────────────────────
    api_key, api_secret = resolve_credentials(args)

    # ── Validate inputs ───────────────────────────────────────────────────────
    try:
        params = validate_order_params(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValidationError as exc:
        print(_c(RED, f"\n[VALIDATION ERROR] {exc}\n"))
        logger.error("Validation failed: %s", exc)
        sys.exit(2)

    print_request_summary(params)

    # ── Place order ───────────────────────────────────────────────────────────
    try:
        with BinanceFuturesClient(api_key=api_key, api_secret=api_secret) as client:
            manager = OrderManager(client)
            result = manager.place_order(
                symbol=params["symbol"],
                side=params["side"],
                order_type=params["order_type"],
                quantity=params["quantity"],
                price=params.get("price"),
                stop_price=params.get("stop_price"),
            )

        print(_c(GREEN, "✔  Order placed successfully!\n"))
        print(result.summary())
        logger.info("Done. orderId=%s status=%s", result.order_id, result.status)

    except BinanceAPIError as exc:
        print(_c(RED, f"\n[API ERROR] {exc}\n"))
        logger.error("Binance API error: %s", exc)
        sys.exit(3)
    except Exception as exc:
        print(_c(RED, f"\n[UNEXPECTED ERROR] {exc}\n"))
        logger.exception("Unexpected error during order placement")
        sys.exit(4)


if __name__ == "__main__":
    main()
