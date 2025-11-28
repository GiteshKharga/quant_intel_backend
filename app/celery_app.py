# app/celery_app.py
from app import create_app
from app.extensions import make_celery

_app = create_app()
celery = make_celery(_app)

# import task modules here to register tasks (avoid circular imports)
# from app.tasks import fetch  # example
