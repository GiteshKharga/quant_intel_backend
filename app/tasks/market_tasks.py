from app.extensions import celery
from app.services.market_weather import compute_market_weather
from app.models.market import MarketWeatherSnapshot

@celery.task
def snapshot_market_weather(symbol):
    res = compute_market_weather(symbol)
    if res:
        rec = MarketWeatherSnapshot(symbol=symbol, data=res)
        from app.extensions import db
        db.session.add(rec); db.session.commit()
