# app/tasks/quality.py
from app.celery_app import celery
from app.services.market_data import validate_symbol_data

@celery.task(bind=True)
def data_quality_check(self):
    # fetch all important symbols and validate
    symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]
    alerts = []
    for s in symbols:
        ok, info = validate_symbol_data(s)
        if not ok:
            alerts.append({s: info})
    if alerts:
        # send alert via monitoring (Sentry) or email (SES)
        raise Exception("Data quality failed: %s" % alerts)
