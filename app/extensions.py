# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_migrate import Migrate
from flask_limiter import Limiter
from celery import Celery
import logging

logger = logging.getLogger(__name__)

db = SQLAlchemy()
cache = Cache()
migrate = Migrate()
# NOTE: in production, pass a real key_func (e.g. by IP or user id)
limiter = Limiter(key_func=lambda: "none")

# Celery factory: do NOT create a running celery at import time (we initialize with app)
def make_celery(app=None):
    """
    Create and configure a Celery instance bound to Flask app config values.
    Call like:
      celery = make_celery(app)
    """
    celery = Celery(app.import_name if app else __name__)
    cfg = {}
    if app is not None:
        celery.conf.update(
            broker_url=app.config.get("CELERY_BROKER_URL"),
            result_backend=app.config.get("CELERY_RESULT_BACKEND"),
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
        )
    return celery

def sentry_init(app):
    # simple stub: if SENTRY_DSN present, initialize Sentry (optional import)
    try:
        dsn = app.config.get("SENTRY_DSN")
        if dsn:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            sentry_sdk.init(dsn=dsn, integrations=[FlaskIntegration()])
            logger.info("Sentry initialized")
    except Exception:
        logger.exception("Sentry initialization failed (optional)")

