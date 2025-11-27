# app/celery_app.py
from . import create_app
from .extensions import make_celery

# Create Flask app
app = create_app()

# Create Celery bound to Flask app
celery = make_celery(app)
