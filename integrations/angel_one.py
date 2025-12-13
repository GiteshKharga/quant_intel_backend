# integrations/angel_one.py
"""
Angel One SmartAPI integration (MVP wrapper).

Usage:
    from integrations.angel_one import AngelOneClient
    client = AngelOneClient(api_key=..., api_secret=..., access_token=..., user_id=...)
    resp = client.place_order(symbol="NIFTY", qty=50, side="BUY", order_type="MARKET")
"""

import time
import logging
import hmac
import hashlib
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# NOTE: replace base URLs with Angel One actual endpoints if different.
BASE_REST = "https://api.angelone.in"  # placeholder
LOGIN_ENDPOINT = "/client/v1/login"    # placeholder
ORDER_ENDPOINT = "/client/v1/orders"   # placeholder
QUOTE_ENDPOINT = "/client/v1/market/quote"  # placeholder

class AngelOneClient:
    def __init__(self,
                 api_key: str,
                 api_secret: str,
                 access_token: Optional[str] = None,
                 user_id: Optional[str] = None,
                 rest_base: str = BASE_REST,
                 timeout: int = 5):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.user_id = user_id
        self.rest_base = rest_base.rstrip("/")
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-KEY": self.api_key,
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Exchange refresh token for access token (MVP — adjust per Angel docs)."""
        url = f"{self.rest_base}{LOGIN_ENDPOINT}"
        payload = {"client_id": self.api_key, "refresh_token": refresh_token}
        r = requests.post(url, json=payload, timeout=self.timeout)
        r.raise_for_status()
        j = r.json()
        # expected keys depend on Angel API; adjust accordingly
        self.access_token = j.get("access_token") or j.get("data", {}).get("access_token")
        self.user_id = j.get("user_id") or j.get("data", {}).get("user_id")
        return j

    def place_order(self,
                    symbol: str,
                    qty: int,
                    side: str = "BUY",          # BUY or SELL
                    order_type: str = "MARKET", # MARKET or LIMIT
                    product_type: str = "MIS",  # MIS, CNC, NRML etc.
                    price: Optional[float] = None,
                    stop_loss: Optional[float] = None,
                    tag: Optional[str] = None) -> Dict[str, Any]:
        """
        Place an order via REST. Returns broker response dict.
        """
        if not self.access_token:
            raise RuntimeError("No access token. Call refresh_token or set access_token.")

        payload = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": order_type,
            "product": product_type,
            # Angel's actual API uses instrument tokens/segment — map symbol before calling
        }
        if price is not None:
            payload["price"] = price
        if stop_loss is not None:
            payload["stop_loss"] = stop_loss
        if tag is not None:
            payload["tag"] = tag

        url = f"{self.rest_base}{ORDER_ENDPOINT}"
        r = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        try:
            r.raise_for_status()
        except Exception as e:
            logger.exception("Order placement failed: %s", e)
            raise
        return r.json()

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get market quote for symbol (MVP)."""
        url = f"{self.rest_base}{QUOTE_ENDPOINT}"
        params = {"symbol": symbol}
        r = requests.get(url, params=params, headers=self._headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # Minimal WebSocket / streaming helper (stub)
    def ws_subscribe(self, symbols: list, on_message_callback):
        """
        Start websocket subscription for given symbols and run callback per message.
        This is a blocking helper (MVP). For production use an async loop or robust reconnect.
        """
        import websocket
        ws_url = "wss://ws.angelone.in/stream"  # placeholder
        def _on_msg(ws, message):
            on_message_callback(message)
        def _on_open(ws):
            # send subscribe msg depending on Angel protocol
            sub = {"type": "subscribe", "symbols": symbols}
            ws.send(json.dumps(sub))
        ws = websocket.WebSocketApp(ws_url, on_message=_on_msg, on_open=_on_open,
                                    header=[f"Authorization: Bearer {self.access_token}"])
        ws.run_forever()
