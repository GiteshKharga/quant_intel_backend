# app/resources/market.py

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request, current_app

from app.schemas.market import MarketWeatherSchema, DangerZoneSchema
from app.services.market_weather import compute_market_weather
from app.services.danger_zones import compute_danger_zones
from app.utils.audit import audit_endpoint

from app.extensions import cache, db

# correct snapshot model imports
try:
    from app.models.market_weather_snapshot import MarketWeatherSnapshot
    from app.models.danger_zone_snapshot import DangerZoneSnapshot
    _HAS_PERSIST = True
except Exception:
    _HAS_PERSIST = False

blp = Blueprint("market", "market", description="Market intelligence endpoints")


# -------------------------------------------------------------------------
# MARKET WEATHER
# -------------------------------------------------------------------------
@blp.route("/market/weather")
class MarketWeatherResource(MethodView):

    @audit_endpoint("market_weather")
    @blp.response(200, MarketWeatherSchema)
    def get(self):
        symbol = request.args.get("symbol")
        period = request.args.get("period", "60d")
        interval = request.args.get("interval", "1d")

        if not symbol:
            abort(400, message="Missing required query parameter: symbol")

        # cache key
        cache_key = f"market_weather:{symbol}:{period}:{interval}"

        # read cache
        try:
            cached = cache.get(cache_key) if cache else None
        except Exception:
            current_app.logger.exception("cache.get failed; continuing")
            cached = None

        if cached:
            return cached

        # compute weather
        result = compute_market_weather(symbol, period=period, interval=interval)
        if result is None:
            abort(503, message=f"Market data unavailable for symbol: {symbol}")

        # persist (optional)
        if _HAS_PERSIST:
            try:
                rec = MarketWeatherSnapshot(symbol=symbol, data=result)
                db.session.add(rec)
                db.session.commit()
            except Exception:
                db.session.rollback()
                current_app.logger.exception(
                    "failed to persist MarketWeatherSnapshot"
                )

        # write cache
        try:
            if cache:
                cache.set(cache_key, result, timeout=60)
        except Exception:
            current_app.logger.exception("cache.set failed")

        return result


# -------------------------------------------------------------------------
# DANGER ZONES
# -------------------------------------------------------------------------
@blp.route("/market/danger-zones")
class DangerZonesResource(MethodView):

    @audit_endpoint("danger_zones")
    @blp.response(200, DangerZoneSchema)
    def get(self):
        symbol = request.args.get("symbol")
        period = request.args.get("period", "180d")
        interval = request.args.get("interval", "1d")

        if not symbol:
            abort(400, message="Missing required query parameter: symbol")

        cache_key = f"danger_zones:{symbol}:{period}:{interval}"

        # read cache
        try:
            cached = cache.get(cache_key) if cache else None
        except Exception:
            current_app.logger.exception("cache.get failed")
            cached = None

        if cached:
            return cached

        # compute danger zones
        result = compute_danger_zones(symbol, period=period, interval=interval)
        if result is None:
            abort(503, message=f"Market data unavailable for symbol: {symbol}")

        # persist snapshot
        if _HAS_PERSIST:
            try:
                rec = DangerZoneSnapshot(symbol=symbol, data=result)
                db.session.add(rec)
                db.session.commit()
            except Exception:
                db.session.rollback()
                current_app.logger.exception(
                    "failed to persist DangerZoneSnapshot"
                )

        # write cache
        try:
            if cache:
                cache.set(cache_key, result, timeout=60)
        except Exception:
            current_app.logger.exception("cache.set failed")

        return result
