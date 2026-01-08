# Backend Architecture

Overview of the Flask backend architecture for The Dreamer's Cave.

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | Flask | 3.0+ |
| Database | MySQL | 8.x |
| DB Driver | mysql-connector-python | 8.2+ |
| Auth | Flask-Login + PyJWT | Latest |
| Task Queue | Celery + Redis | 5.3+ |
| CORS | Flask-CORS | 4.0+ |

## Directory Structure

```
backend/
├── app/
│   ├── __init__.py       # Flask app factory
│   ├── config.py         # Configuration classes
│   │
│   ├── models/           # Database model classes
│   │   └── *.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api/          # Public API endpoints (/api/v1/*)
│   │   │   ├── __init__.py
│   │   │   └── health.py
│   │   └── admin/        # Admin API endpoints (/api/v1/admin/*)
│   │       └── __init__.py
│   │
│   ├── services/         # Business logic layer
│   │   └── *.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── db.py         # Database connection pool
│   │   └── responses.py  # Standard API responses
│   │
│   └── tasks/            # Celery async tasks
│       └── *.py
│
├── migrations/           # Database migrations
├── tests/                # Unit tests
├── requirements.txt      # Python dependencies
├── wsgi.py               # WSGI entry point
└── .env                  # Environment variables
```

## Application Factory

The app uses Flask's application factory pattern for flexibility and testing.

**File:** `backend/app/__init__.py`

```python
from flask import Flask

def create_app(config_class=None):
    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app, ...)

    # Initialize database pool
    with app.app_context():
        init_pool(app)

    # Register blueprints
    from app.routes.api import register_api_routes
    register_api_routes(app)

    # Register error handlers
    register_error_handlers(app)

    return app
```

## Configuration

**File:** `backend/app/config.py`

Three configuration classes:

| Class | FLASK_ENV | Use Case |
|-------|-----------|----------|
| DevelopmentConfig | development | Local development |
| ProductionConfig | production | Production server |
| TestingConfig | testing | Unit tests |

Environment variables are loaded from `.env` via python-dotenv.

## Database Layer

**File:** `backend/app/utils/db.py`

Uses MySQL connection pooling with mysql-connector-python (NO SQLAlchemy).

### Connection Pool

```python
from mysql.connector import pooling

_pool = pooling.MySQLConnectionPool(
    pool_name="tdc_pool",
    pool_size=10,
    host=config['DB_HOST'],
    database=config['DB_NAME'],
    ...
)
```

### Query Helpers

| Function | Description |
|----------|-------------|
| `get_cursor()` | Context manager for cursor with auto-commit/rollback |
| `fetch_one(query, params)` | Execute query, return single row |
| `fetch_all(query, params)` | Execute query, return all rows |
| `execute(query, params)` | Execute INSERT/UPDATE/DELETE |
| `execute_many(query, params_list)` | Batch operations |

### Usage Example

```python
from app.utils.db import fetch_one, fetch_all, execute

# Fetch single row
user = fetch_one(
    "SELECT * FROM users WHERE id = %s",
    (user_id,)
)

# Fetch multiple rows
locations = fetch_all(
    "SELECT * FROM locations WHERE is_active = %s ORDER BY sort_order",
    (True,)
)

# Insert and get ID
new_id = execute(
    "INSERT INTO users (email, username) VALUES (%s, %s)",
    (email, username)
)
```

## API Response Format

**File:** `backend/app/utils/responses.py`

All API responses follow a consistent format:

### Success Response

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "pagination": { ... }
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": "Error message",
  "errors": {
    "field": ["validation error"]
  }
}
```

### Response Helpers

| Function | HTTP Status | Use Case |
|----------|-------------|----------|
| `success(data)` | 200 | Successful GET/PUT |
| `created(data)` | 201 | Successful POST |
| `no_content()` | 204 | Successful DELETE |
| `paginated(items, page, per_page, total)` | 200 | List with pagination |
| `bad_request(message)` | 400 | Invalid request |
| `unauthorized(message)` | 401 | Authentication required |
| `forbidden(message)` | 403 | Permission denied |
| `not_found(message)` | 404 | Resource not found |
| `server_error(message)` | 500 | Internal error |

## Blueprints

Routes are organized using Flask blueprints:

| Blueprint | URL Prefix | Description |
|-----------|------------|-------------|
| api | /api/v1 | Public API routes |
| health | /api/v1/health | Health check endpoints |
| admin | /api/v1/admin | Admin-only routes |

### Registration

```python
# In app/routes/api/__init__.py
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

def register_api_routes(app):
    from app.routes.api import health
    api_bp.register_blueprint(health.bp)
    app.register_blueprint(api_bp)
```

## Error Handling

Global error handlers are registered in the app factory:

| HTTP Code | Handler | Response |
|-----------|---------|----------|
| 400 | handle_400 | Bad request |
| 401 | handle_401 | Unauthorized |
| 403 | handle_403 | Forbidden |
| 404 | handle_404 | Not found |
| 405 | handle_405 | Method not allowed |
| 500 | handle_500 | Server error |
| Exception | handle_exception | Unexpected errors |

## CORS Configuration

CORS is configured to allow requests from:

- `http://localhost:5173` (Vite default)
- `http://localhost:3000`
- `https://thedreamerscave.club`
- `https://www.thedreamerscave.club`

Allowed methods: GET, POST, PUT, PATCH, DELETE, OPTIONS

## Entry Points

### Development

```bash
flask run --host=0.0.0.0 --port=9500
```

### Production (Gunicorn)

```bash
gunicorn -w 4 -b 0.0.0.0:9500 wsgi:app
```

**File:** `backend/wsgi.py`

```python
from app import create_app
app = create_app()
```

## Security Considerations

1. **SQL Injection Prevention**: Always use parameterized queries
2. **CORS**: Restricted to specific origins
3. **Environment Variables**: Secrets never in code
4. **Error Messages**: Generic messages in production
5. **Input Validation**: Validate all user input (TODO: implement validators)
