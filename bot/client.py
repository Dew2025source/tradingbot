

from __future__ import annotations

import hashlib
import hmac
import time
import urllib.parse
from typing import Any, Dict, Optional

import requests

from bot.logging_config import get_logger

logger = get_logger("client")

TESTNET_BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_TIMEOUT = 10  # seconds
RECV_WINDOW = 5000


class BinanceAPIError(Exception):
    """Wraps HTTP / API-level errors from Binance."""

    def __init__(self, message: str, status_code: Optional[int] = None, code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code  # Binance error code, e.g. -1121

    def __str__(self):
        parts = [super().__str__()]
        if self.status_code:
            parts.append(f"HTTP {self.status_code}")
        if self.code:
            parts.append(f"Binance code {self.code}")
        return " | ".join(parts)


class BinanceFuturesClient:
    """
    Thin, authenticated wrapper around the Binance Futures Testnet REST API.

    Usage
    -----
    client = BinanceFuturesClient(api_key="...", api_secret="...")
    response = client.post("/fapi/v1/order", params={...})
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = TESTNET_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must not be empty.")
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.info("BinanceFuturesClient initialised. Base URL: %s", self._base_url)

    # Internal helpers
  

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, query_string: str) -> str:
        return hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _build_signed_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        params = {k: v for k, v in params.items() if v is not None}
        params["timestamp"] = self._timestamp()
        params["recvWindow"] = RECV_WINDOW
        query_string = urllib.parse.urlencode(params)
        params["signature"] = self._sign(query_string)
        return params

    def _handle_response(self, response: requests.Response) -> dict:
        logger.debug(
            "HTTP %s %s -> status %d | body: %.500s",
            response.request.method,
            response.url,
            response.status_code,
            response.text,
        )
        try:
            data = response.json()
        except ValueError:
            raise BinanceAPIError(
                f"Non-JSON response: {response.text[:200]}",
                status_code=response.status_code,
            )

        if not response.ok or isinstance(data, dict) and "code" in data and data["code"] < 0:
            code = data.get("code") if isinstance(data, dict) else None
            msg = data.get("msg", response.text) if isinstance(data, dict) else response.text
            raise BinanceAPIError(msg, status_code=response.status_code, code=code)

        return data

    # Public interface

    def post(self, path: str, params: Optional[Dict[str, Any]] = None) -> dict:
        """Signed POST request (used for order placement)."""
        params = self._build_signed_params(params or {})
        url = f"{self._base_url}{path}"
        logger.debug("POST %s | params (excl. signature): %s", url, {k: v for k, v in params.items() if k != "signature"})
        try:
            resp = self._session.post(url, data=params, timeout=self._timeout)
        except requests.exceptions.Timeout:
            raise BinanceAPIError(f"Request timed out after {self._timeout}s")
        except requests.exceptions.ConnectionError as exc:
            raise BinanceAPIError(f"Network error: {exc}")
        return self._handle_response(resp)

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, signed: bool = False) -> dict:
        """GET request, optionally signed."""
        if signed:
            params = self._build_signed_params(params or {})
        url = f"{self._base_url}{path}"
        logger.debug("GET %s | params: %s", url, params)
        try:
            resp = self._session.get(url, params=params, timeout=self._timeout)
        except requests.exceptions.Timeout:
            raise BinanceAPIError(f"Request timed out after {self._timeout}s")
        except requests.exceptions.ConnectionError as exc:
            raise BinanceAPIError(f"Network error: {exc}")
        return self._handle_response(resp)

    def close(self):
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
