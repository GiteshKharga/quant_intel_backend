# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_migrate import Migrate
from flask_limiter import Limiter
from celery import Celery

db = SQLAlchemy()
cache = Cache()
migrate = Migrate()
# in production you should pass a real key func (per-user)
limiter = Limiter(key_func=lambda: "none")

def make_celery(app):
    """
    Create and configure a Celery object attached to the Flask app.
    Returns the celery instance.
    """
    celery = Celery(
        app.import_name,
        broker=app.config.get("CELERY_BROKER_URL"),
        backend=app.config.get("CELERY_RESULT_BACKEND"),
    )
    # Pass flask config into celery
    celery.conf.update(app.config.get("CELERY", {}) or {})
    celery.conf.broker_url = app.config.get("CELERY_BROKER_URL")
    celery.conf.result_backend = app.config.get("CELERY_RESULT_BACKEND")
    celery.Task = ContextTask = _make_celery_task(app, celery)
    return celery

def _make_celery_task(app, celery):
    """
    Create a Celery task base class that runs tasks inside Flask app_context.
    """
    from celery import Task
    class ContextTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return Task.__call__(self, *args, **kwargs)
    return ContextTask

def sentry_init(app):
    # Placeholder for Sentry init in production
    # e.g. import sentry_sdk; sentry_sdk.init(dsn=app.config.get("SENTRY_DSN"), integrations=[...])
    return None
