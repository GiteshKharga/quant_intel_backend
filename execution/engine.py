# execution/engine.py
"""
Simple execution engine that receives signals and routes them to broker clients.
This file shows how to use AngelOneClient and contains basic risk checks.
"""

import logging
from typing import Dict, Any
from integrations.angel_one import AngelOneClient

logger = logging.getLogger(__name__)

class ExecutionEngine:
    def __init__(self, broker_client: AngelOneClient, max_position_per_symbol: int = 200):
        self.broker = broker_client
        self.max_position_per_symbol = max_position_per_symbol
        # in-memory position tracker (MVP). Replace with DB for production.
        self.positions = {}

    def can_execute(self, symbol: str, qty: int) -> bool:
        current = self.positions.get(symbol, 0)
        if abs(current + qty) > self.max_position_per_symbol:
            logger.warning("Position limit exceeded for %s: current=%s, req=%s", symbol, current, qty)
            return False
        return True

    def execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        signal example:
        {
          "symbol": "NIFTY",
          "action": "BUY",
          "qty": 50,
          "type": "MARKET",
          "strategy_id": "trend_v1"
        }
        """
        symbol = signal["symbol"]
        qty = int(signal["qty"]) if signal.get("action") == "BUY" else -int(signal["qty"])
        if not self.can_execute(symbol, qty):
            return {"status": "rejected", "reason": "position_limit"}
        try:
            resp = self.broker.place_order(symbol=symbol, qty=abs(qty),
                                           side="BUY" if qty > 0 else "SELL",
                                           order_type=signal.get("type", "MARKET"),
                                           product_type=signal.get("product", "MIS"))
            # update positions simplistically on success
            # NOTE: In truth, check response order status before updating
            self.positions[symbol] = self.positions.get(symbol, 0) + qty
            return {"status": "ok", "broker_response": resp}
        except Exception as e:
            logger.exception("Execution failed for %s: %s", symbol, e)
            return {"status": "error", "error": str(e)}
