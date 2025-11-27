# app/trading/alpaca_client.py
"""
Minimal Alpaca paper-trading helper using requests.
Set ALPACA_KEY and ALPACA_SECRET in your .env for it to work.

Endpoints used:
- GET  /v2/account
- POST /v2/orders
"""

import os
import requests

API_BASE = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
API_KEY = os.getenv("ALPACA_KEY")
API_SECRET = os.getenv("ALPACA_SECRET")

HEADERS = {
    "APCA-API-KEY-ID": API_KEY or "",
    "APCA-API-SECRET-KEY": API_SECRET or "",
    "Content-Type": "application/json"
}

def _auth_check():
    if not API_KEY or not API_SECRET:
        raise RuntimeError("Alpaca keys not set. Set ALPACA_KEY and ALPACA_SECRET in your environment to enable live/paper trading.")

def account_info():
    """
    Return account information dict or raise RuntimeError if keys missing.
    """
    _auth_check()
    url = f"{API_BASE}/v2/account"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()

def place_order(symbol: str, qty: int, side: str = "buy", order_type: str = "market", time_in_force: str = "gtc"):
    """
    Place an order on Alpaca (paper) and return the API response.
    """
    _auth_check()
    payload = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": order_type,
        "time_in_force": time_in_force
    }
    url = f"{API_BASE}/v2/orders"
    r = requests.post(url, json=payload, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()
