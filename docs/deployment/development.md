# Development Environment Setup

Guide for setting up the TDC development environment.

## Prerequisites

- Python 3.11+
- Node.js 18+
- MySQL 8.x
- Redis (for Celery tasks)
- Git

## Quick Start

The fastest way to get started is using the `dev.sh` script:

```bash
# Clone the repository
git clone <repository-url>
cd tdcweb

# Start all development servers
./dev.sh start

# Check status
./dev.sh status
```

## Development Server Manager (dev.sh)

A unified script to manage frontend and backend development servers.

### Commands

| Command | Description |
|---------|-------------|
| `./dev.sh start` | Start all services (detached) |
| `./dev.sh stop` | Stop all services |
| `./dev.sh restart` | Restart all services |
| `./dev.sh status` | Show service status |
| `./dev.sh logs <service>` | Follow service logs |

### Services

| Service | Port | Description |
|---------|------|-------------|
| `backend` | 9500 | Flask REST API |
| `frontend` | 9501 | Vue.js dev server |

### Options

| Option | Description |
|--------|-------------|
| `-a`, `--attached` | Run in foreground (single service only) |

### Examples

```bash
# Start everything in background
./dev.sh start

# Start only backend in foreground (for debugging)
./dev.sh start backend -a

# Restart frontend only
./dev.sh restart frontend

# Follow backend logs
./dev.sh logs backend

# Stop everything
./dev.sh stop
```

### Log Files

- Backend: `.logs/backend.log`
- Frontend: `.logs/frontend.log`

### PID Files

Process IDs are stored in `.pids/` directory for service management.

## Manual Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run development server
flask run --host=0.0.0.0 --port=9500
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with API URL

# Run development server
npm run dev -- --host 0.0.0.0 --port 9501
```

## Environment Configuration

### Backend (.env)

```env
# Flask
FLASK_APP=wsgi.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=tdcweb
DB_USER=tdcweb
DB_PASSWORD=tdcweb

# Redis
REDIS_URL=redis://localhost:6379/0
```

### Frontend (.env.local)

```env
VITE_API_URL=http://localhost:9500/api/v1
VITE_APP_TITLE=The Dreamer's Cave
```

## Database Setup

1. Create the database:

```sql
CREATE DATABASE tdcweb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tdcweb'@'localhost' IDENTIFIED BY 'tdcweb';
GRANT ALL PRIVILEGES ON tdcweb.* TO 'tdcweb'@'localhost';
FLUSH PRIVILEGES;
```

2. Run migrations (when available):

```bash
cd backend
flask db upgrade
```

## Verifying the Setup

### Backend Health Check

```bash
curl http://localhost:9500/api/v1/health
```

Expected response:
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "version": "0.1.0",
    "timestamp": "2025-01-08T12:00:00.000Z"
  }
}
```

### Database Health Check

```bash
curl http://localhost:9500/api/v1/health/db
```

Expected response:
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "database": "connected",
    "timestamp": "2025-01-08T12:00:00.000Z"
  }
}
```

## Troubleshooting

### Port Already in Use

If you see "Address already in use" errors, check what's using the port:

```bash
lsof -i :9500  # Check backend port
lsof -i :9501  # Check frontend port
```

### Database Connection Failed

1. Verify MySQL is running: `systemctl status mysql`
2. Check credentials in `.env`
3. Test connection: `mysql -u tdcweb -p tdcweb`

### Frontend Not Loading

1. Check if backend is running: `./dev.sh status`
2. Verify API URL in frontend `.env.local`
3. Check browser console for CORS errors

## IDE Configuration

### VS Code Extensions

Recommended extensions for this project:

- Python (ms-python.python)
- Vetur or Volar (Vue.js support)
- Tailwind CSS IntelliSense
- ESLint
- Prettier

### VS Code Settings

```json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[vue]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```
