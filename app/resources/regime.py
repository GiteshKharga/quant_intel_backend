# app/resources/regime.py
from flask_smorest import Blueprint
from flask.views import MethodView
from marshmallow import Schema, fields
from flask import request, current_app
from app.services.regime_engine import classify_regime
from app.extensions import limiter

blp = Blueprint("Regime", "regime", description="Regime detection")


class RegimeQuerySchema(Schema):
    symbol = fields.Str(required=True, metadata={"description": "Ticker symbol (e.g. RELIANCE.NS)"})
    period = fields.Str(load_default="60d", metadata={"description": "lookback period"})
    interval = fields.Str(load_default="1d", metadata={"description": "ohlcv interval"})


@blp.route("/regime", methods=["GET"])
@limiter.limit("60/minute")
def get_regime():
    args = request.args.to_dict()
    schema = RegimeQuerySchema()
    params = schema.load(args)
    symbol = params.get("symbol")
    period = params.get("period")
    interval = params.get("interval")
    result = classify_regime(symbol)  # regime engine can accept period/interval if you extend it
    if result is None:
        return {"error": "no data"}, 404
    return result
