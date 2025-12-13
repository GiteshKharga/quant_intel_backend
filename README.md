# QuantIntel Backend

A Flask-based quantitative intelligence backend providing market analysis, risk assessment, and trading APIs.

## Features

- **Market Weather Analysis**: Real-time market sentiment and technical indicators
- **Danger Zone Detection**: Risk assessment and volatility analysis
- **Trading Integration**: Alpaca paper trading support
- **Regime Detection**: Market regime classification engine
- **Background Workers**: Celery-based async task processing
- **Caching**: Redis-powered response caching
- **Monitoring**: Prometheus metrics and Sentry error tracking

## Tech Stack

- **Backend**: Flask with flask-smorest (OpenAPI)
- **Database**: PostgreSQL (production) / SQLite (development)
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **Server**: Gunicorn (production)
- **Containerization**: Docker & Docker Compose

## Quick Start

### Prerequisites

- Python 3.11+
- Redis (for caching/Celery)
- PostgreSQL (production) or SQLite (development)

### Local Development

1. **Clone and setup environment**:
   ```bash
   git clone <repository-url>
   cd quant_intel_backend
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run the development server**:
   ```bash
   set FLASK_DEBUG=true  # Windows
   # export FLASK_DEBUG=true  # Linux/Mac
   python run.py
   ```

4. **Access the API**:
   - Health check: http://localhost:8000/health
   - Root: http://localhost:8000/

### Docker Development

```bash
# Build and start all services
docker compose up --build

# Run in background
docker compose up -d

# View logs
docker compose logs -f web

# Stop services
docker compose down
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root status check |
| `/health` | GET | Health check |
| `/market/weather?symbol=AAPL` | GET | Market weather analysis |
| `/market/danger-zones?symbol=AAPL` | GET | Danger zone detection |

## Environment Variables

See [.env.example](.env.example) for all available configuration options.

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | `your-secret-key-here` |
| `DATABASE_URL` | Database connection string | `postgresql+psycopg2://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `production` |
| `FLASK_DEBUG` | Enable debug mode | `false` |
| `CACHE_TYPE` | Cache backend | `SimpleCache` |
| `SENTRY_DSN` | Sentry error tracking | (none) |

## Testing

```bash
# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=app
```

## Production Deployment

### Docker (Recommended)

1. Update `.env` with production values
2. Build and deploy:
   ```bash
   docker compose up -d --build
   ```

### Manual Deployment

```bash
# Install production dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn "app:create_app()" -w 4 -b 0.0.0.0:8000 --timeout 120
```

### Nginx Configuration

See [deployments/nginx/nginx.conf](deployments/nginx/nginx.conf) for SSL proxy configuration.

## Database Migrations

```bash
# Initialize migrations (first time)
flask db init

# Create migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade
```

## License

MIT License
