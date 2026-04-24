# Changelog

All notable changes to The Dreamer's Cave website project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2026-04-24] — Phase 2 (Nuxt 4 core configuration)

Infrastructure-only phase. No user-visible surface yet — the output of this
phase is a production-capable Nuxt 4 runtime, the BFF plumbing for auth, the
location theming substrate, and the testing harness that phases 3+ will build
against.

### Added

#### Frontend runtime

- `frontend/nuxt.config.ts` — Nuxt 4 canonical config: `compatibilityDate:
  '2026-04-01'`, `future.compatibilityVersion: 4`, `routeRules` matrix
  (SSG / ISR swr=300/3600 / SSR / SPA by route), Nitro `devProxy` to Flask on
  `:9502`, runtimeConfig for `flaskUrl` + `cookieSecret` + public
  `apiBase` + `siteUrl`, dev server on `:9503`.
- `frontend/app/assets/css/main.css` — Tailwind v4 CSS-first config. Single
  `@import "tailwindcss";`, `@theme` block mapping `--color-*` tokens to
  `--tdc-*` CSS vars, `@layer base` with `:root` defaults and per-location
  overrides for **8 locations** (`dreamerscave`, `dreamvision`, `evanescence`,
  `livemagic`, `thelounge`, `arquipelago`, `noahsark`, `jazzclub`). Palettes
  grouped by mood (Cosmic/Tech, Hybrid, Warm/Intimate). Two remaining venues
  tracked in TECH_DEBT as TD-008.
- `frontend/app/plugins/gsap.client.ts` — client-only GSAP + ScrollTrigger
  registration, provides `$gsap` and `$ScrollTrigger` to the app.
- `frontend/app/plugins/lenis.client.ts` — client-only Lenis smooth-scroll,
  synced with `gsap.ticker.add()` (single RAF loop), stopped on
  `/admin/*` and `/dashboard/*`.
- `frontend/app/types/{api,user,location,event}.ts` — shared TypeScript
  interfaces (`ApiResponse<T>`, `ApiError`, `User`, `UserRole`, `Location`,
  `LocationMood`, `Event`, `EventStatus`, `AuthResponse`) for consumption by
  composables and server routes in later phases.

#### Nuxt BFF (hybrid auth plumbing)

- `frontend/server/middleware/auth-forward.ts` — runs on every request,
  reads `tdc_access` HttpOnly cookie, stamps
  `event.context.flaskHeaders = { Authorization: 'Bearer <jwt>' }` for
  downstream `flaskFetch` calls.
- `frontend/server/utils/flask-client.ts` — `flaskFetch(url, event, options)`
  wraps `$fetch` with `baseURL` from runtime config and auto-forwards
  `flaskHeaders` stamped by the middleware. Caller headers win on conflict.
- `frontend/server/utils/cookies.ts` — canonical auth-cookie primitives:
  `TDC_ACCESS_COOKIE` / `TDC_REFRESH_COOKIE` / TTL constants + path,
  `setAccessCookie` (15 min, SameSite=Lax, Path=/), `setRefreshCookie`
  (7 days, SameSite=Strict, Path=/api/auth), `clearAuthCookies`
  (path-aware delete on both), `getRefreshToken`. `secure` flag gated on
  `NODE_ENV === 'production'`.

#### Testing

- `frontend/vitest.config.ts` — `defineVitestConfig` from
  `@nuxt/test-utils/config`, `happy-dom` environment, globals enabled,
  spec discovery under `tests/**/*.test.ts`.
- `frontend/tests/unit/flask-client.test.ts` (3 tests) — header forwarding,
  baseURL threading, caller-header precedence.
- `frontend/tests/unit/auth-forward.test.ts` (3 tests) — cookie read, guest
  path, exact header casing / prefix contract with Flask.
- `frontend/tests/unit/cookies.test.ts` (9 tests) — constants, both
  setters (including `secure` flag per environment), path-aware delete,
  refresh-token getter.
- `frontend/package.json` scripts — `test` (vitest run) and `test:watch`.
- `frontend/.nuxtrc` — `setups.@nuxt/test-utils="4.0.2"` (auto-generated
  pin by `@nuxt/test-utils`, commit-safe).

#### Configuration

- `frontend/.env.example` — documents `NUXT_FLASK_URL`, `NUXT_COOKIE_SECRET`,
  `NUXT_PUBLIC_SITE_URL`, `NUXT_PUBLIC_API_BASE`. No secrets in repo;
  `NUXT_COOKIE_SECRET` production value generated via
  `openssl rand -hex 64`.

### Changed

- `frontend/app/assets/css/main.css` — superseded the Task 2.1 stub
  (`@import "tailwindcss";` one-liner) with the full theme token file
  described above. Closes TD-006.
- `frontend/server/middleware/auth-forward.ts` — retrofitted to import
  `TDC_ACCESS_COOKIE` from `server/utils/cookies.ts` rather than hardcoding
  the string, and to use the resilient globalThis-first / h3-fallback
  import pattern described in the implementation note.
- `docs/TECH_DEBT.md` — TD-006 (Tailwind v4 CSS-first rework) closed
  against this phase's commit. TD-008 (remaining 2 location palettes) and
  TD-009 (`flask-client.ts` globalThis-only — prod Nitro safety
  unverified) opened.

### Infrastructure

- `typescript@^6.0.3` added as explicit `devDependency` (previously
  transitive). Closes TD-001.
- `@tailwindcss/vite@^4.2.4` added as explicit `dependency`; the Nuxt 4
  `@nuxtjs/tailwindcss` module is NOT used (incompatible with v4).
- `@nuxt/test-utils@^4.0.2`, `vitest@^4.1.5`, `happy-dom@^20.9.0`,
  `@playwright/test@^1.59.1` installed as `devDependencies`.

### Security

- Auth cookies set `httpOnly: true`, `secure: NODE_ENV==='production'`;
  `tdc_access` scoped to `/` with `SameSite=Lax`; `tdc_refresh` scoped to
  `/api/auth` with `SameSite=Strict`. Refresh token is therefore never
  transmitted to arbitrary page renders and is blocked from CSRF-style
  cross-site sends. Verified against spec §8.2 contract.
- Production build audited: zero leaks of `NUXT_COOKIE_SECRET`,
  `flaskUrl`, or other server-only values into the client bundle. Zero
  leaks of client-only libraries (`gsap.registerPlugin`, `new Lenis`,
  `tdc_access` cookie name) into SSR HTML.

### Verification

- `nuxt build`: 13 s, `.output/` 46.7 MB total, client bundle 452 KB,
  all 8 location palettes present in compiled CSS.
- Prod node server boots on `:9501` in ~1 s. HTTP 200 on `/`, `/it/`,
  localized disallow on `/robots.txt`, `/sitemap.xml` returns 307
  (nginx will finalize the canonical redirect in prod).
- Unit test suite: **15 tests** (flask-client ×3, auth-forward ×3,
  cookies ×9), all green via `npm test`.

**Spec:** `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md`
**Plan:** `docs/superpowers/plans/2026-04-23-nuxt-integration.md`
**Commits:** atomic Phase 2 commit (SHA to be filled in by controller
after commit).

---

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

### Planned (Phase 3+)
- i18n content loading (locale JSON + DB-backed translations) — Phase 3
- Design-system consolidation (`docs/DESIGN.md`) — end of Phase 4 (TD-007)
- User auth flows wired end-to-end (login/register/refresh/me + Pinia user
  store) — Phase 4
- Location management API + SSG pages with per-location theming — Phase 5
- Event management API + ISR event pages — Phase 5
- Artist profiles API — Phase 5
- Blog / News API + on-demand ISR revalidation — Phase 5
- Admin dashboard (SPA, ssr: false) — Phase 6
- Google Calendar integration — Phase 7
- Facebook posting integration — Phase 7
- Patreon webhooks — Phase 7
- Second Life in-world API — Phase 7
