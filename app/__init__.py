# app/__init__.py
import logging
import pkgutil
import importlib
from flask import Flask
from .config import get_config
from .extensions import db, cache, migrate, limiter, make_celery, sentry_init

# optional helpers (not required)
try:
    from .observability.prom import init_metrics
except Exception:
    init_metrics = None

try:
    from .logging_config import configure_logging
except Exception:
    configure_logging = None


def register_resource_blueprints(app):
    import app.resources as resources_pkg
    package_path = resources_pkg.__path__

    for _, module_name, _ in pkgutil.iter_modules(package_path):
        full_name = f"app.resources.{module_name}"
        try:
            module = importlib.import_module(full_name)
        except Exception as e:
            app.logger.exception(f"Failed importing resource module {full_name}: {e}")
            continue

        blp = getattr(module, "blp", None)
        if blp is not None:
            try:
                app.register_blueprint(blp)  # root-level routes
                app.logger.info(f"Registered blueprint: {full_name}.blp")
            except Exception as e:
                app.logger.exception(f"Failed registering blueprint {full_name}.blp: {e}")
        else:
            app.logger.debug(f"No 'blp' found in {full_name}; skipping.")


def create_app():
    # structured logging early (optional)
    if configure_logging:
        try:
            configure_logging()
        except Exception:
            logging.exception("configure_logging() failed")

    app = Flask(__name__, static_folder=None)
    
    # Register custom JSON provider
    from app.json_provider import NumpyJSONProvider
    app.json = NumpyJSONProvider(app)

    cfg = get_config()
    app.config.from_object(cfg)

    # Initialize celery (so tasks can see config). We keep celery object local to module app.celery_app
       # after loading config
    from app.extensions import make_celery
    # create and attach celery (so other modules can import app.celery_app.celery)
    try:
        # create a celery instance attached to this app (not strictly required for web worker,
        # but makes celery configuration available)
        celery = make_celery(app)
        # Optionally attach celery to app.extensions for easier access: app.extensions['celery'] = celery
        app.extensions = getattr(app, "extensions", {})
        app.extensions["celery"] = celery
    except Exception:
        app.logger.exception("Failed to initialize celery")

    # init extensions
    try:
        db.init_app(app)
    except Exception:
        app.logger.exception("db.init_app failed")

    try:
        cache.init_app(app)
    except Exception:
        app.logger.exception("cache.init_app failed")

    try:
        migrate.init_app(app, db)
    except Exception:
        app.logger.exception("migrate.init_app failed")

    try:
        limiter.init_app(app)
    except Exception:
        app.logger.exception("limiter.init_app failed")

    # init sentry if configured (non-fatal)
    try:
        sentry_init(app)
    except Exception:
        app.logger.exception("sentry_init failed or missing")

    # init prometheus metrics if available
    if init_metrics:
        try:
            init_metrics(app)
        except Exception:
            app.logger.exception("init_metrics failed")

    # register blueprints
    register_resource_blueprints(app)

    @app.route("/")
    def index():
        return {"status": "ok"}

    return app
