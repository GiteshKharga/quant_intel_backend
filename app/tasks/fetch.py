# app/tasks/fetch.py
from app.celery_app import celery
from app.services.market_data import fetch_and_store_symbol
from celery.schedules import crontab

@celery.task(bind=True, max_retries=3)
def periodic_fetch(self, symbol):
    try:
        fetch_and_store_symbol(symbol)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # every 5 minutes for hot symbols
    sender.add_periodic_task(300.0, periodic_fetch.s('RELIANCE.NS'), name='fetch_reliance')
    # daily data quality job at 02:00
    sender.add_periodic_task(crontab(hour=2, minute=0), data_quality_check.s())
