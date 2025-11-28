# app/resources/trade.py
from flask_smorest import Blueprint
from flask.views import MethodView
from marshmallow import Schema, fields
from flask import request, current_app
from app.trading.alpaca_client import place_order, account_info
from app.utils.audit import audit_endpoint
from app.extensions import limiter

blp = Blueprint("Trade", "trade", description="Paper trading endpoints")


class PlaceOrderSchema(Schema):
    symbol = fields.Str(required=True, metadata={"description": "Ticker symbol"})
    qty = fields.Int(required=True, metadata={"description": "Quantity"})
    side = fields.Str(required=False, load_default="buy", metadata={"description": "buy or sell"})
    type = fields.Str(required=False, load_default="market", metadata={"description": "order type"})
    time_in_force = fields.Str(required=False, load_default="gtc", metadata={"description": "time in force"})


@blp.route("/trade/account", methods=["GET"])
@audit_endpoint("trade_account")
@limiter.limit("30/minute")
def get_account():
    try:
        data = account_info()
        return data, 200
    except Exception as e:
        current_app.logger.exception("trade.account failed")
        return {"error": str(e)}, 400


@blp.route("/trade/place", methods=["POST"])
@blp.arguments(PlaceOrderSchema)
@audit_endpoint("trade_place")
@limiter.limit("30/minute")
def place_order_endpoint(order_data):
    """
    order_data contains validated:
    {symbol, qty, side, type, time_in_force}
    """
    try:
        resp = place_order(**order_data)
        return {"status": "success", "order": resp}, 200
    except Exception as e:
        return {"error": str(e)}, 400
