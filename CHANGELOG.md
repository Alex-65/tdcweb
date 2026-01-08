# Changelog

All notable changes to The Dreamer's Cave website project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-08

### Added

#### Backend Infrastructure
- Flask application factory pattern (`backend/app/__init__.py`)
- Configuration management with environment-based classes (`backend/app/config.py`)
  - DevelopmentConfig, ProductionConfig, TestingConfig
  - Environment variables loaded from `.env`
- MySQL connection pooling with mysql-connector-python (`backend/app/utils/db.py`)
  - `get_cursor()` context manager with auto-commit/rollback
  - Helper functions: `fetch_one()`, `fetch_all()`, `execute()`, `execute_many()`
  - Connection pool with configurable size
- Standard API response format (`backend/app/utils/responses.py`)
  - Success responses: `success()`, `created()`, `no_content()`, `paginated()`
  - Error responses: `bad_request()`, `unauthorized()`, `forbidden()`, `not_found()`, `server_error()`
- Health check endpoints (`backend/app/routes/api/health.py`)
  - `GET /api/v1/health` - Basic health check
  - `GET /api/v1/health/db` - Database connectivity check
  - `GET /api/v1/health/full` - Full system health check
- WSGI entry point for Gunicorn (`backend/wsgi.py`)
- CORS configuration for development and production origins

#### Development Tools
- Development server manager script (`dev.sh`)
  - Start/stop/restart/status commands
  - Support for backend and frontend services
  - Detached (background) and attached (foreground) modes
  - Log file management in `.logs/`
  - PID file management in `.pids/`
  - Backend on port 9500, Frontend on port 9501

#### Documentation
- Development environment setup guide (`docs/deployment/development.md`)
- Backend architecture documentation (`docs/backend/architecture.md`)
- Health check API reference (`docs/api/health.md`)
- Updated README.md with quick start guide
- Created documentation directory structure:
  - `docs/api/` - API documentation
  - `docs/backend/` - Backend guides
  - `docs/frontend/` - Frontend guides
  - `docs/deployment/` - Deployment guides
  - `docs/database/` - Database documentation
  - `docs/integrations/` - External integrations
  - `docs/i18n/` - Internationalization

#### Configuration
- Backend environment file (`.env`) with development defaults
- Python virtual environment setup in `backend/venv/`

### Technical Notes

- **No SQLAlchemy**: Project uses mysql-connector-python directly for better control
- **App Factory Pattern**: Enables testing and multiple configurations
- **Blueprint Architecture**: Routes organized by domain (api, admin)
- **Connection Pooling**: Efficient database connection management
- **Standard Response Format**: Consistent JSON structure across all endpoints

---

## [Unreleased]

### Planned
- User authentication (JWT + OAuth)
- Location management API
- Event management API
- Artist profiles API
- Blog/News API
- Admin dashboard endpoints
- Frontend Vue.js application
- GSAP scroll animations
- Location theming system
- Google Calendar integration
- Facebook posting integration
- Patreon webhooks
- Second Life API
