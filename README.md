# The Dreamer's Cave - Virtual Music Club Website

Website for The Dreamer's Cave, a virtual music club in Second Life established in 2019.

**Domain:** thedreamerscave.club
**Motto:** "You Can See The Music"

## Quick Start

```bash
# Start development servers (backend + frontend)
./dev.sh start

# Check status
./dev.sh status

# Stop servers
./dev.sh stop
```

**Development URLs:**
- Backend API: http://localhost:9500
- Frontend: http://localhost:9501

## Project Structure

```
tdcweb/
├── backend/              # Flask REST API
│   ├── app/
│   │   ├── __init__.py   # App factory
│   │   ├── config.py     # Configuration
│   │   ├── models/       # Database models
│   │   ├── routes/       # API endpoints
│   │   │   ├── api/      # Public API (/api/v1/*)
│   │   │   └── admin/    # Admin API
│   │   ├── services/     # Business logic
│   │   ├── utils/        # Helpers (db, responses)
│   │   └── tasks/        # Celery async tasks
│   ├── migrations/
│   ├── tests/
│   └── wsgi.py           # WSGI entry point
│
├── frontend/             # Vue.js 3 SPA
│   ├── src/
│   │   ├── assets/       # Static assets
│   │   ├── components/   # Vue components
│   │   ├── composables/  # Composition API hooks
│   │   ├── stores/       # Pinia stores
│   │   ├── views/        # Page components
│   │   ├── router/       # Vue Router config
│   │   ├── i18n/         # Translations (EN, IT, FR, ES)
│   │   └── styles/       # CSS/Tailwind
│   └── public/
│
├── docs/                 # Documentation
│   ├── api/              # API reference
│   ├── backend/          # Backend architecture
│   ├── frontend/         # Frontend guides
│   ├── deployment/       # Setup guides
│   └── plans/            # Project plans
│
├── dev.sh                # Development server manager
└── CLAUDE.md             # AI assistant instructions
```

## Technology Stack

### Backend
| Component | Technology |
|-----------|------------|
| Framework | Python 3.11+ / Flask |
| Database | MySQL 8.x (mysql-connector-python) |
| Auth | JWT + OAuth (Google, Discord, Facebook) |
| Task Queue | Celery + Redis |
| API Format | RESTful JSON |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | Vue.js 3 (Composition API) |
| Build Tool | Vite |
| Styling | Tailwind CSS |
| Animations | GSAP + ScrollTrigger + Lenis |
| State | Pinia |
| i18n | Vue I18n (EN, IT, FR, ES) |

## Development Server Manager

The `dev.sh` script provides unified management of development servers.

### Commands

```bash
./dev.sh start              # Start all (detached)
./dev.sh start backend      # Start backend only
./dev.sh start backend -a   # Start backend (attached/foreground)
./dev.sh stop               # Stop all services
./dev.sh restart            # Restart all services
./dev.sh status             # Show service status
./dev.sh logs backend       # Follow backend logs
./dev.sh logs frontend      # Follow frontend logs
```

### Ports

| Service | Port | URL |
|---------|------|-----|
| Backend | 9500 | http://localhost:9500 |
| Frontend | 9501 | http://localhost:9501 |

## API Endpoints

### Health Check

| Endpoint | Description |
|----------|-------------|
| GET `/api/v1/health` | Basic health check |
| GET `/api/v1/health/db` | Database connectivity |
| GET `/api/v1/health/full` | Full system health |

Example:
```bash
curl http://localhost:9500/api/v1/health
```

Response:
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

## Manual Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- MySQL 8.x
- Redis

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
flask run --port=9500
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with API URL
npm run dev -- --port 9501
```

## Features

- Immersive landing page with Apple-style scroll animations
- Location showcases with unique visual themes (10+ venues)
- Event calendar with Google Calendar sync
- Artist profiles and gallery
- Blog/News system with WYSIWYG editor
- User registration with OAuth support
- Patreon integration for exclusive content
- Facebook auto-posting for events
- Second Life API for in-world displays
- Multilingual support (EN, IT, FR, ES)
- Admin dashboard for content management

## Documentation

| Document | Description |
|----------|-------------|
| [Development Setup](docs/deployment/development.md) | Local environment setup |
| [Backend Architecture](docs/backend/architecture.md) | Flask app structure |
| [Health API](docs/api/health.md) | Health check endpoints |
| [Project Plan](docs/plans/pdp-v2.md) | Full development plan |

## Environment Variables

### Backend (.env)

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key
DB_HOST=localhost
DB_NAME=tdcweb
DB_USER=tdcweb
DB_PASSWORD=tdcweb
```

### Frontend (.env.local)

```env
VITE_API_URL=http://localhost:9500/api/v1
```

## License

Proprietary - All rights reserved.

---

*The Dreamer's Cave - "You Can See The Music"*
