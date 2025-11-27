import os
from functools import lru_cache

class BaseConfig:
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = False
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///data.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Caching
    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")  # SimpleCache for local dev; use RedisCache in prod
    CACHE_REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", 300))

    # Celery / Broker
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

    # Rate limiter storage (flask-limiter)
    RATELIMIT_STORAGE_URL = os.getenv("RATELIMIT_STORAGE_URL", None)

    # Market / keys
    IEX_API_TOKEN = os.getenv("IEX_API_TOKEN", "")
    ALPACA_KEY = os.getenv("ALPACA_KEY", "")
    ALPACA_SECRET = os.getenv("ALPACA_SECRET", "")
    ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

    # Observability
    SENTRY_DSN = os.getenv("SENTRY_DSN", None)

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = "development"

class TestingConfig(BaseConfig):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = "production"

@lru_cache()
def get_config():
    env = os.getenv("FLASK_ENV", "production")
    if env == "development":
        return DevelopmentConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return ProductionConfig()
