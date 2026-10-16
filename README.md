# The Dreamer's Cave — Virtual Music Club Website

Website for The Dreamer's Cave, a virtual music club in Second Life established in 2019.

- **Domain:** [thedreamerscave.club](https://thedreamerscave.club)
- **Motto:** "You Can See The Music"

## Quick Start

The repository ships with a `dev.sh` helper that manages both processes.

```bash
# Start backend (Flask) + frontend (Nuxt 4)
./dev.sh start

# Check status
./dev.sh status

# Stop all services
./dev.sh stop
```

**Development URLs:**

- Flask API: <http://localhost:9502>
- Nuxt frontend: <http://localhost:9503>

The Nuxt dev server proxies `/api/**` to Flask via Nitro's `devProxy` — in
development the browser only talks to Nuxt on `:9503`.

## Project Structure

```
tdcweb/
├── backend/                  # Flask REST API (Python 3.11+)
│   ├── app/
│   │   ├── __init__.py       # App factory
│   │   ├── config.py         # Environment-based config classes
│   │   ├── models/           # MySQL table bindings (mysql-connector-python)
│   │   ├── routes/
│   │   │   ├── api/          # Public REST API (/api/*)
│   │   │   └── admin/        # Admin-only endpoints
│   │   ├── services/         # Business logic
│   │   ├── utils/            # db, responses, decorators, validators
│   │   └── tasks/            # Celery async tasks
│   ├── migrations/
│   ├── tests/                # pytest
│   └── wsgi.py
│
├── frontend/                 # Nuxt 4 + Vue 3 + TypeScript (strict)
│   ├── app/                  # Nuxt 4 `app/` layer
│   │   ├── app.vue
│   │   ├── error.vue         # Global error page (a11y landmark + role=alert)
│   │   ├── layouts/          # default.vue (AppHeader + slot + AppFooter)
│   │   ├── pages/            # index.vue · locations/index.vue · events/index.vue
│   │   ├── assets/css/       # main.css (Tailwind v4 @theme + location vars + --color-error)
│   │   ├── components/       # common/AppHeader.vue · common/AppFooter.vue
│   │   ├── composables/      # useApi · useApiFetch · useAuth · useScrollAnimation · useSmoothScroll · useLocationTheme
│   │   ├── middleware/       # auth.ts · admin.ts · staff.ts (route guards, Phase 4)
│   │   ├── plugins/          # gsap.client.ts, lenis.client.ts (reduced-motion aware)
│   │   ├── stores/           # auth.ts · locale.ts · ui.ts (Pinia setup syntax)
│   │   ├── types/            # Shared TS types (api, user, location, event)
│   │   └── utils/            # auth-guard.ts (pure helpers; Nuxt auto-imports app/utils/)
│   ├── server/               # Nitro server routes (hybrid BFF)
│   │   ├── middleware/       # auth-forward.ts
│   │   └── utils/            # cookies.ts · flask-client.ts (resilient pattern, TD-009 closed)
│   ├── i18n/locales/         # en.json · it.json · fr.json · es.json (nav/home/locations/events/errors)
│   ├── tests/                # vitest unit (21 specs) · Playwright E2E (11 at 1920x1080)
│   ├── nuxt.config.ts
│   ├── vitest.config.ts
│   ├── .env.example
│   └── package.json
│
├── docs/
│   ├── TECH_DEBT.md          # Technical debt register (rule 18)
│   ├── api/                  # REST API reference
│   ├── backend/              # Flask architecture guides
│   ├── database/             # Schema / migrations
│   ├── deployment/           # Dev + prod runbooks
│   ├── frontend/             # nuxt-playbook.md (frontend reference)
│   ├── i18n/
│   ├── integrations/
│   ├── plans/                # pdp-v2.md (historical), pdp-v3.md (current)
│   └── superpowers/          # Phase-specific specs and implementation plans
│
├── apache/                   # Production Apache vhost config (Phase 6)
├── .claude/
│   ├── agents/               # 27 domain agents (tdc-*)
│   └── skills/               # CLI skills (tdc-docs, tdc-backend, etc.)
├── dev.sh                    # Unified dev-server manager
├── CLAUDE.md                 # AI assistant project law
├── CHANGELOG.md
└── README.md
```

## Technology Stack

### Backend

| Component | Technology |
|-----------|------------|
| Framework | Python 3.11+ / Flask |
| Database | MySQL 8.x via `mysql-connector-python` (no SQLAlchemy) |
| Auth | JWT (HttpOnly cookies) + OAuth2 (Google, Discord, Facebook) |
| Task Queue | Celery + Redis |
| API Format | RESTful JSON |

### Frontend

| Component | Technology |
|-----------|------------|
| Meta-framework | Nuxt 4 (`app/` layer, `compatibilityVersion: 4`) |
| UI | Vue 3 Composition API, `<script setup lang="ts">` |
| TypeScript | 6.x, strict mode |
| Styling | Tailwind CSS v4 via `@tailwindcss/vite` (CSS-first `@theme` config) |
| Animations | GSAP 3 + ScrollTrigger + Lenis 1.3 (client-only `.client.ts` plugins) |
| State | Pinia + `@pinia/nuxt` |
| i18n | `@nuxtjs/i18n` (`prefix_except_default`: EN default, `/it/ /fr/ /es/`) |
| SEO | `@nuxtjs/seo` + sitemap + robots (`useSeoMeta`, `useSchemaOrg`) |
| Image | `@nuxt/image` (`<NuxtImg>`, auto avif/webp) |
| Forms | vee-validate + zod |
| Rich text | `@tiptap/vue-3` (admin-only, `<ClientOnly>`-wrapped) |
| BFF | Nuxt `server/api/auth/**` + `server/api/revalidate` |
| Testing | vitest + `@nuxt/test-utils` + happy-dom (unit) · Playwright 1920x1080 (E2E) |

## Development Server Manager

```bash
./dev.sh start              # Start backend + frontend (detached)
./dev.sh start backend      # Start backend only
./dev.sh start backend -a   # Start backend in foreground
./dev.sh stop               # Stop all
./dev.sh restart            # Restart all
./dev.sh status             # Show service status
./dev.sh logs backend       # Follow backend logs
./dev.sh logs frontend      # Follow frontend logs
```

### Ports

| Environment | Flask | Nuxt |
|-------------|-------|------|
| Development | 9502  | 9503 |
| Production  | 9500  | 9501 |

## API Endpoints

### Health check (Flask, public)

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Basic health check |
| `GET /api/health/db` | Database connectivity |
| `GET /api/health/full` | Full system health |

```bash
curl http://localhost:9502/api/health
```

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

Full API documentation — including authentication, location, event,
and admin endpoints — ships alongside the features that define them.

## Manual Setup

### Prerequisites

- Python 3.11+
- Node.js 20+ (Nuxt 4 minimum)
- MySQL 8.x
- Redis (Celery)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # Edit DB credentials / secrets
flask run --port=9502           # Dev port
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env            # Edit NUXT_FLASK_URL etc.
npm run dev                     # Nuxt dev on :9503 (set in nuxt.config.ts)
```

### Testing

```bash
cd frontend
npm test                        # vitest, one-shot
npm run test:watch              # vitest, watch mode
```

## Features (delivered + planned)

- Public landing page with locale-aware SEO (delivered — Phase 3; `pages/index.vue`, SSG, hero scrim + i18n-bound meta)
- Public locations list (delivered — Phase 3; `pages/locations/index.vue`, SSG, three-state template with localized empty + error)
- Public events list (delivered — Phase 3; `pages/events/index.vue`, ISR `swr: 300`, preemptive-polish pattern from §23.1 of the playbook)
- 10+ themed location palettes (in progress — 8/10 palettes live in `app/assets/css/main.css`; TD-008 tracks the remaining 2)
- Semantic `--color-error` token + `text-error` utility (delivered — Phase 3 Task 3.6b)
- `useApi()` composable with 401 auto-refresh + typed retry marker (delivered — Phase 3 Task 3.8, TDD-authored)
- `useScrollAnimation` + `useSmoothScroll` + `useLocationTheme` composables (delivered — Phase 3 Tasks 3.10-3.11, reduced-motion aware)
- Pinia stores: auth / locale / ui (delivered — Phase 3 Task 3.9; `ui.pushNotification` SSR-unsafe, playbook §10.6)
- i18n content EN/IT/FR/ES — nav / home / home.seo / locations / events / errors namespaces (delivered — Phase 3 Task 3.4)
- Immersive landing page with GSAP scroll animations (planned, Phase 5)
- Event calendar with Google Calendar sync (Phase 7)
- Artist profiles and gallery (Phase 5)
- Blog / News system with TipTap editor (Phase 5)
- User registration with OAuth + login/logout/refresh/me BFF (Phase 4)
- Auth-gated dashboard / admin SPA routes (Phases 4 and 6)
- Patreon integration for exclusive content (Phase 7)
- Facebook auto-posting for events (Phase 7)
- Second Life in-world API (Phase 7)

## Documentation

| Document | Description |
|----------|-------------|
| [CLAUDE.md](CLAUDE.md) | AI assistant project law (rules, agent inventory, stack) |
| [CHANGELOG.md](CHANGELOG.md) | Phase-by-phase change history |
| [docs/TECH_DEBT.md](docs/TECH_DEBT.md) | Tech debt register |
| [docs/frontend/nuxt-playbook.md](docs/frontend/nuxt-playbook.md) | Nuxt 4 frontend reference |
| [docs/backend/architecture.md](docs/backend/architecture.md) | Flask architecture |
| [docs/deployment/development.md](docs/deployment/development.md) | Local dev setup |
| [docs/api/health.md](docs/api/health.md) | Health check endpoints |
| [docs/plans/pdp-v2.md](docs/plans/pdp-v2.md) | Historical project plan (Vue + Vite era) |
| [docs/superpowers/specs/](docs/superpowers/specs/) | Per-phase architectural specs |
| [docs/superpowers/plans/](docs/superpowers/plans/) | Per-phase task-level plans |

## Environment Variables

### Backend `backend/.env`

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DB_HOST=localhost
DB_NAME=tdcweb
DB_USER=tdcweb
DB_PASSWORD=tdcweb
REDIS_URL=redis://localhost:6379/0
```

### Frontend `frontend/.env`

```env
# Flask URL used by Nuxt SSR (server-to-server, bypasses Apache).
NUXT_FLASK_URL=http://localhost:9502

# Cookie signing secret. Generate with: openssl rand -hex 64
NUXT_COOKIE_SECRET=change-me-in-production

# Public site URL (canonical links, OpenGraph, sitemap).
NUXT_PUBLIC_SITE_URL=http://localhost:9503

# API base path as seen by the browser (Apache/proxy-resolved).
NUXT_PUBLIC_API_BASE=/api
```

## License

Proprietary — all rights reserved.

---

*The Dreamer's Cave — "You Can See The Music"*
