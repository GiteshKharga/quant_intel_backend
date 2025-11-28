# app/services/market_service.py  (create this file)
from flask import current_app
from app.services.market_weather import compute_market_weather
from app.models.market import MarketWeatherSnapshot

def get_market_weather_cached(symbol: str, period: str, interval: str, cache_timeout: int = 60):
    cache = current_app.extensions.get("cache")
    cache_key = f"market_weather:{symbol}:{period}:{interval}"
    cached = cache.get(cache_key) if cache else None
    if cached:
        return cached

    res = compute_market_weather(symbol, period=period, interval=interval)
    if res and cache:
        cache.set(cache_key, res, timeout=cache_timeout)
    # persist snapshot
    if res:
        try:
            rec = MarketWeatherSnapshot(symbol=symbol, data=res)
            from app.extensions import db
            db.session.add(rec)
            db.session.commit()
        except Exception:
            current_app.logger.exception("Failed to persist market snapshot")
    return res
