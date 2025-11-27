# app/resources/market.py
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request, current_app
from app.schemas.market import MarketWeatherSchema, DangerZoneSchema
from app.services.market_weather import compute_market_weather
from app.services.danger_zones import compute_danger_zones
from app.utils.audit import audit_endpoint

# optional imports for persistence and caching
from app.extensions import cache, db  # cache may be configured as your app.extensions.cache

# optional models to persist snapshots if you want
try:
    from app.models.market import MarketWeatherSnapshot, DangerZoneSnapshot
    _HAS_PERSIST = True
except Exception:  # pragma: no cover
    _HAS_PERSIST = False

blp = Blueprint("Market", "market", description="Market intelligence endpoints")


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

        cache_key = f"market_weather:{symbol}:{period}:{interval}"

        # try cache (if configured)
        try:
            if cache:
                cached = cache.get(cache_key)
            else:
                cached = None
        except Exception:
            current_app.logger.exception("cache.get failed; continuing without cache")
            cached = None

        if cached:
            return cached

        result = compute_market_weather(symbol, period=period, interval=interval)
        if result is None:
            abort(503, message=f"Market data unavailable for symbol: {symbol}")

        # persist snapshot (optional)
        if _HAS_PERSIST:
            try:
                rec = MarketWeatherSnapshot(symbol=symbol, data=result)
                db.session.add(rec)
                db.session.commit()
            except Exception:
                db.session.rollback()
                current_app.logger.exception("failed to persist MarketWeatherSnapshot")

        # set cache
        try:
            if cache:
                cache.set(cache_key, result, timeout=60)
        except Exception:
            current_app.logger.exception("cache.set failed; continuing")

        return result


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

        try:
            if cache:
                cached = cache.get(cache_key)
            else:
                cached = None
        except Exception:
            current_app.logger.exception("cache.get failed; continuing without cache")
            cached = None

        if cached:
            return cached

        result = compute_danger_zones(symbol, period=period, interval=interval)
        if result is None:
            abort(503, message=f"Market data unavailable for symbol: {symbol}")

        # persist snapshot (optional)
        if _HAS_PERSIST:
            try:
                rec = DangerZoneSnapshot(symbol=symbol, data=result)
                db.session.add(rec)
                db.session.commit()
            except Exception:
                db.session.rollback()
                current_app.logger.exception("failed to persist DangerZoneSnapshot")

        try:
            if cache:
                cache.set(cache_key, result, timeout=60)
        except Exception:
            current_app.logger.exception("cache.set failed; continuing")

        return result
