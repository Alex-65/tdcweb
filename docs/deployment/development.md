# Development Environment Setup

Local setup for the TDC Nuxt 4 + Flask stack.

## Prerequisites

- **Python 3.11+** — Flask backend
- **Node.js 20+** — Nuxt 4 minimum runtime
- **MySQL 8.x** — primary database
- **Redis** — Celery broker + ISR cache (later phases)
- **Git**

## Quick start

```bash
git clone <repository-url>
cd tdcweb

# Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                     # edit DB creds / secrets

# Frontend
cd ../frontend && npm install
cp .env.example .env                     # edit NUXT_* vars

# Run both
cd .. && ./dev.sh start
./dev.sh status
```

## Ports

| Environment | Flask  | Nuxt   |
|-------------|--------|--------|
| Development | `9502` | `9503` |
| Production  | `9500` | `9501` |

In dev, the Nuxt dev server proxies `/api/**` to Flask via Nitro's
`devProxy` (configured in `frontend/nuxt.config.ts`). The browser only
ever talks to Nuxt on `:9503` — direct hits to `:9502` work but are
not the expected request path.

## `dev.sh` — unified dev-server manager

```bash
./dev.sh start                # Start backend + frontend (detached)
./dev.sh start backend        # Start backend only
./dev.sh start backend -a     # Start backend in foreground (debug)
./dev.sh restart frontend     # Restart frontend only
./dev.sh stop                 # Stop everything
./dev.sh status               # Show per-service status
./dev.sh logs backend         # Follow backend log
./dev.sh logs frontend        # Follow frontend log
```

**Log files:** `.logs/backend.log`, `.logs/frontend.log`
**PID files:** `.pids/`

## Environment configuration

### Backend — `backend/.env`

```env
FLASK_APP=wsgi.py
FLASK_ENV=development
SECRET_KEY=your-secret-key            # flask session signing
JWT_SECRET_KEY=your-jwt-secret        # JWT HS256 signing (must match Nuxt-side if shared)

# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=tdcweb
DB_USER=tdcweb
DB_PASSWORD=tdcweb

# Redis / Celery
REDIS_URL=redis://localhost:6379/0
```

### Frontend — `frontend/.env`

Copy from `frontend/.env.example`. All Nuxt runtime vars use the `NUXT_`
prefix — the old `VITE_*` names from the Vue+Vite era are obsolete.

```env
# Flask URL used by Nuxt SSR (server-to-server, bypasses nginx).
NUXT_FLASK_URL=http://localhost:9502

# Cookie signing secret for the H3 cookie module.
# Generate a 64-char hex secret with:  openssl rand -hex 64
NUXT_COOKIE_SECRET=change-me-in-production

# Public site URL for canonical links, Open Graph, sitemap.
NUXT_PUBLIC_SITE_URL=http://localhost:9503

# API base path as seen by the browser (resolved by nginx in prod,
# by Nitro devProxy in dev).
NUXT_PUBLIC_API_BASE=/api
```

**Do not commit real secrets.** `frontend/.env.example` is committed;
`frontend/.env` is local and gitignored.

## Database setup

```sql
CREATE DATABASE tdcweb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tdcweb'@'localhost' IDENTIFIED BY 'tdcweb';
GRANT ALL PRIVILEGES ON tdcweb.* TO 'tdcweb'@'localhost';
FLUSH PRIVILEGES;
```

Migrations (as they come online):

```bash
cd backend && source venv/bin/activate
flask db upgrade
```

## Verifying the setup

### Flask health

```bash
curl http://localhost:9502/api/health
```

```json
{ "success": true, "data": { "status": "ok", "version": "0.1.0", "timestamp": "…" } }
```

### Flask DB connectivity

```bash
curl http://localhost:9502/api/health/db
```

### Nuxt landing page (SSR)

```bash
curl -I http://localhost:9503/
# → HTTP/1.1 200 OK
```

### Nuxt → Flask proxy (dev)

```bash
curl http://localhost:9503/api/health   # served by Flask via Nitro devProxy
```

## Frontend tooling

```bash
cd frontend

npm run dev                    # Nuxt dev on :9503 (HMR, devtools, devProxy to Flask)
npm run build                  # Production build to .output/
npm run preview                # Serve the built prod output locally
npm run generate               # Static site generate (SSG only)
npm test                       # vitest, one-shot
npm run test:watch             # vitest, watch mode
```

## Troubleshooting

### Port already in use

```bash
lsof -i :9502                   # backend dev
lsof -i :9503                   # frontend dev
```

`./dev.sh stop` before retrying `./dev.sh start`.

### Database connection failed

1. Verify MySQL is running: `systemctl status mysql`
2. Check credentials in `backend/.env`
3. Test the credentials directly:
   ```bash
   mysql -u tdcweb -p tdcweb
   ```

### Nuxt build fails on Tailwind

TDC uses **Tailwind v4** wired via `@tailwindcss/vite` in `nuxt.config.ts`.
There is **no** `tailwind.config.ts` at project root — tokens live in
`frontend/app/assets/css/main.css` via `@theme`. If you see
`PostCSS plugin has moved to separate package`, it means someone
re-introduced `@nuxtjs/tailwindcss` (a v3 module that is incompatible
with v4 hoisted by `@nuxt/ui` / `nuxt-og-image`). Remove it.
See `docs/TECH_DEBT.md` TD-006 for historical context.

### Vitest cannot resolve `$fetch` / `defineEventHandler` / `getCookie`

Expected. TDC's server utilities import the h3 functions explicitly AND
check `globalThis` for test stubs. Tests install the stub **before
importing the module** (see `frontend/tests/unit/*.test.ts` for the
pattern). Nitro's prod bundle does not universally expose h3 auto-
imports on `globalThis` — this is by design, not a bug.

### Frontend not loading

1. Check service status: `./dev.sh status`
2. Verify Flask is reachable from Nuxt's perspective:
   ```bash
   curl $NUXT_FLASK_URL/api/health
   ```
3. Check browser console for CORS or mixed-content errors.

## IDE setup

### Recommended VS Code extensions

- **Volar** (`Vue.volar`) — Vue 3 / Nuxt 4 TypeScript support
- **Tailwind CSS IntelliSense** (`bradlc.vscode-tailwindcss`) — v4 auto-completion
- **ESLint**
- **Python** (`ms-python.python`)

### VS Code workspace settings

```json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "typescript.tsdk": "frontend/node_modules/typescript/lib",
  "editor.formatOnSave": true,
  "[python]": { "editor.defaultFormatter": "ms-python.black-formatter" },
  "[vue]":    { "editor.defaultFormatter": "Vue.volar" },
  "[typescript]": { "editor.defaultFormatter": "esbenp.prettier-vscode" }
}
```

Volar handles `<script setup lang="ts">` with strict TypeScript (per
`nuxt.config.ts` `typescript.strict: true`). Type-check is off during
dev HMR for speed; run `npx nuxi typecheck` in CI or manually when you
want the full check.

## Related docs

- `README.md` — project overview and quick start
- `CLAUDE.md` — AI assistant project law (rules, stack, agent inventory)
- `docs/frontend/nuxt-playbook.md` — full Nuxt 4 frontend reference
- `docs/backend/architecture.md` — Flask architecture
- `docs/TECH_DEBT.md` — open tech-debt items
