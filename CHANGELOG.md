# Changelog

All notable changes to The Dreamer's Cave website project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2026-04-24] — Phase 3 (Nuxt 4 frontend port — pages, components, composables, stores, i18n)

Phase 3 ports the surviving frontend surface from the Vue 3 + Vite backup
(`frontend.vue-backup/`) onto the Nuxt 4 runtime laid down in Phase 2.
End state: a public site that dev-boots, prod-builds, SSR-renders three
public pages (home SSG, locations SSG, events ISR) across EN/IT/FR/ES,
uses typed composables for data + animation + theming, and passes all
21 unit tests plus 11/11 Playwright E2E at 1920x1080.

Phase 3 landed 12 main tasks (3.0 through 3.11) plus 4 scope-expanded
polish sub-tasks (3.2b, 3.3b, 3.5b, 3.6b) plus 5 controller-level
phase-end micro-edits (favicon, Lenis reduced-motion guard, nav active
differentiation, error `role="alert"` standardization, AppFooter motto
via i18n). All governed via the per-task no-commit loop (CLAUDE.md
rule 15) with phase-end triple review + real tests + docs sync
(rule 16) in one atomic commit.

### Added

#### Pages (public)

- `frontend/app/pages/index.vue` — home page (SSG). `useSeoMeta` bound
  to `home.hero_title` / `home.seo.description` / `home.seo.og_description`;
  hero gradient layered under a `bg-dark/40` scrim (Task 3.5b) for
  cross-palette WCAG AA contrast; subtitle promoted to `text-2xl` for
  AA-large on yellow-biased palettes. Brand-integrity `ogTitle` stays
  English literal.
- `frontend/app/pages/locations/index.vue` — locations list (SSG).
  `useFetch<Location[]>('/api/locations')` with `key: 'locations-list'`.
  Three-state template: error branch (`role="alert" text-error` +
  `t('locations.error.load_failed')`), populated grid, empty-state
  (`t('locations.empty')`). Null-guarded description. Card
  `NuxtLink` wrapped with `useLocalePath()` so IT/FR/ES deep-links
  preserve their locale prefix (fix applied as Task 3.6b controller
  micro-edit). Focus-visible ring on every card.
- `frontend/app/pages/events/index.vue` — events list (ISR, `swr: 300`
  via `nuxt.config.ts routeRules`). `useFetch<Event[]>('/api/events')`
  with `query: { upcoming: 'true' }`. Preemptive-polish delivery from
  Task 3.7 (the first task to ship the full polish pattern without a
  `b`-task iteration): i18n via `t('events.*')`, `text-error` + `role="alert"`
  on error, `v-else-if="events && events.length"` populated branch,
  `v-else` empty state with `t('events.empty')`. Raw-ISO `<time datetime="...">`
  retained as SSR-safe developer view until `useFormattedDate` composable
  lands (TD-012).

#### Components

- `frontend/app/layouts/default.vue` — site layout scaffold. Wraps
  `<NuxtPage />` between `<AppHeader />` and `<AppFooter />` with a
  `flex flex-col min-h-screen` frame.
- `frontend/app/error.vue` — global error page. `role="alert"` live
  region, status code + status message with `t('errors.message_fallback')`
  fallback, "Back to home" button bound to `clearError({ redirect: '/' })`
  with `t('errors.back_to_home')`. Focus-visible ring on the CTA. Root
  element switched to `<main>` for accessibility landmark (Task 3.2b).
- `frontend/app/components/common/AppHeader.vue` — sticky header.
  Four nav links (locations / events / artists / blog) with
  `useLocalePath()` wrap, `hover:text-primary transition-colors`, and
  `active-class="text-primary font-bold"` (bold-weight differentiator
  resolves nav hover/active ambiguity from scan row 36). Locale
  switcher `<select>`. Outline-style login button (`border-primary
  text-primary hover:bg-primary hover:text-white`) replaces the
  Phase 3 plan's filled primary — wins AA contrast on 7/8 palettes
  (jazzclub regresses, see TD-011). Focus-visible ring on login CTA.
- `frontend/app/components/common/AppFooter.vue` — site footer.
  Copyright year hoisted to `<script setup>` (`const year = new
  Date().getFullYear()`) per CLAUDE.md SSR Rule #4 (templates must not
  call `new Date()` — the plan's original template inline got overridden
  with a script-setup hoist and rationale comment). Motto pulled from
  `$t('home.hero_title')` — pragmatic DRY on an identical English /
  translated string rather than duplicating a `common.motto` namespace.

#### Composables

- `frontend/app/composables/useApi.ts` — `$fetch.create({ credentials:
  'include' })` wrapper with 401 auto-refresh. Exports
  `RetryableFetchOptions = NonNullable<Parameters<typeof $fetch>[1]>
  & { _retry?: boolean }` — derived from Nitro's `$fetch` parameter
  type rather than ofetch's `FetchOptions`, so the `method` literal
  union narrows correctly under strict mode. Retry path recursively
  calls `useApi()(request, opts)` per spec §8.4 (re-enters the wrapper
  so credentials + future interceptor logic are preserved; `_retry`
  flag guards against infinite loops). Explicit
  `: ReturnType<typeof $fetch.create>` return type annotation prevents
  TS7023 on the recursive reference.
- `frontend/app/composables/useScrollAnimation.ts` — `gsap.context()`-
  scoped scroll-triggered reveal animation with `onBeforeUnmount` →
  `ctx.revert()` cleanup + `$ScrollTrigger?.refresh()` to prevent
  instance leaks across navigations (CLAUDE.md SSR Rule #1). Guards
  with `import.meta.client` and `window.matchMedia('(prefers-reduced-motion:
  reduce)').matches` — opt-in reduced-motion users get no reveal
  animation, just the natural CSS state.
- `frontend/app/composables/useSmoothScroll.ts` — Lenis programmatic
  `scrollTo(target, options)` wrapper. `import.meta.client` + reduced-
  motion guards. Uses optional-chain `$lenis?.scrollTo(...)` so it
  no-ops when Lenis wasn't instantiated (reduced-motion users).
- `frontend/app/composables/useLocationTheme.ts` — accepts `Ref<string
  | null | undefined>` or plain string. Sets `body[data-location="<slug>"]`
  via `useHead({ bodyAttrs })` — SSR-safe, zero-JS at paint, consumes
  the `:root` fallback palette for unknown slugs.

#### Pinia stores

- `frontend/app/stores/auth.ts` — setup-syntax store. `user`, derived
  `isAuthenticated` / `isAdmin` / `isStaff`, `setUser(u)` / `clear()`
  actions.
- `frontend/app/stores/locale.ts` — setup-syntax store. `current`
  locale code + `setLocale(code)`.
- `frontend/app/stores/ui.ts` — setup-syntax store. `isMobileMenuOpen`,
  `notifications[]` with JSDoc `@warning` that `pushNotification()`
  uses `crypto.randomUUID()` and must NOT be called during SSR setup
  or template interpolation (scan row 32 SSR constraint). Safe for
  user-triggered post-mount actions.

#### i18n content

- `frontend/i18n/locales/en.json` + `it.json` + `fr.json` + `es.json`
  — 9 new namespaces × 4 locales = 36 translations. Keys: `nav.{locations,
  events,artists,blog,login}`, `home.{hero_title,hero_subtitle}`,
  `home.seo.{description,og_description}`, `locations.{title,empty}`,
  `locations.seo.description`, `locations.error.load_failed`,
  `events.{title,empty}`, `events.seo.description`,
  `events.error.load_failed`, `errors.{message_fallback,back_to_home}`.

#### Tests

- `frontend/tests/unit/useApi.test.ts` (4 tests, TDD-authored) — covers
  the `$fetch.create({ credentials: 'include' })` contract, the
  `onResponseError` registration, the 401 refresh+retry happy path, and
  the single-retry guard (no infinite loop when `_retry` is already true).
- `frontend/tests/unit/flask-client.test.ts` — extended from 3 to 8
  assertions (5 new): fallback-path verification (ofetch mock invoked
  when `globalThis.$fetch` absent — TD-009 resolution proof), plus
  missing-runtimeConfig error path test.

### Changed

- `frontend/app/assets/css/main.css` — added semantic-state token
  `--tdc-color-error: #ef4444` in `:root` and mapped `--color-error:
  var(--tdc-color-error)` in `@theme`. Pattern: when a semantic token
  is missing at first consumer-need, add it alongside the consumer
  rather than waiting for DESIGN.md (TD-007) consolidation. Not
  overridden per location (error has universal meaning).
- `frontend/app/app.vue` — favicon reference switched from
  non-existent `/favicon.svg` to existing `/favicon.ico`. SVG
  reintroduction deferred to a future brand-assets task.
- `frontend/app/plugins/lenis.client.ts` — `prefers-reduced-motion` guard
  at plugin init. When the media query matches, the plugin returns
  `{ provide: { lenis: null as Lenis | null } }` — Lenis is not
  instantiated at all, so wheel/touch interpolation never kicks in.
  Consumers already use the optional-chain `$lenis?.scrollTo(...)`
  pattern and no-op cleanly.
- `frontend/nuxt.config.ts` — added `components: [{ path: '~/components',
  pathPrefix: false }]` so `common/AppHeader.vue` registers as
  `<AppHeader />` (flat naming). Removed `lazy: true` from the i18n
  block (`@nuxtjs/i18n` v9+ auto-lazies when `langDir` + per-locale
  `file` are set; the flag emits a deprecation warning).
- `docs/TECH_DEBT.md` — TD-009 closed against this phase's commit.
  TD-011 annotated with Phase 3 close state (still open, no jazzclub
  page in this phase). TD-012 (`useFormattedDate`) and TD-013
  (`livemagic` vs `--color-error` collision) opened. TD-007 header
  restored (was missing).

### Fixed

- Flat component naming under subdirectory: Phase 3 Task 3.3
  discovered the plan's internal contradiction between `<AppHeader />`
  (used in layout) and `app/components/common/AppHeader.vue` (path),
  since Nuxt 4 default auto-naming would produce `<CommonAppHeader />`.
  Resolved via `components.pathPrefix: false` rather than moving the
  file or switching the usage. Plan amended in docs-sync.
- AppFooter copyright year SSR safety: plan had
  `{{ new Date().getFullYear() }}` inline in template with a "stable
  across SSR and hydration" note; CLAUDE.md SSR Rule #4 is
  NON-NEGOTIABLE. Hoisted to `<script setup>` with explicit rationale
  comment covering the NYE edge case. SSR HTML byte-identical to the
  plan's intent.
- Nav hover / active-route visual collision: `hover:text-primary` and
  `active-class="text-primary"` produced ambiguous state when a user
  on `/events` hovered `/locations` (both primary red). Active class
  upgraded to `text-primary font-bold` — differentiation now comes
  from weight, not color.
- Error surface standardization: all 3 error branches in Phase 3
  (error.vue, locations list, events list) carry `role="alert"` for
  screen-reader live-region announcement. Prior state: only error.vue
  had it (Task 3.2b carryover).

### Security

- Auth-cookie contract unchanged from Phase 2 (`tdc_access`
  HttpOnly/Lax/Path=/ · `tdc_refresh` HttpOnly/Strict/Path=/api/auth).
  Phase 3 adds no new auth surface; the BFF routes land in Phase 4.
- `useApi` retry loop provably bounded: `_retry` flag set to `true`
  before recursive `useApi()(request, opts)` call. Second 401 response
  does not trigger a second refresh (unit-tested).

### Infrastructure

- Prod build verified: `nuxt build` + SSR bundle audit
  (`grep -r "gsap\|lenis" frontend/.output/server/` returns zero
  runtime imports — `import type` in composables keeps client-only
  libraries out of the SSR bundle). Closes closing-scan row 39.
- Full test suite: 21/21 unit tests green (`flask-client` ×8,
  `auth-forward` ×3, `cookies` ×9, `useApi` ×4, `useApi.test-utils`
  ×1) — +6 over Phase 2's baseline (`useApi` ×4 new; `flask-client`
  +5, -3 renamed paths).
- Playwright E2E at 1920x1080: 11/11 PASS across EN/IT/FR/ES route
  matrix (home, locations, events x 4 locales, plus error page).

### Verification

- `nuxi typecheck`: 0 errors.
- `npm test`: 21 tests, all green.
- `npm run build` + `node .output/server/index.mjs`: prod boot clean,
  HTTP 200 on `/`, `/it/`, `/fr/`, `/es/`, `/locations`, `/events`,
  `/it/locations`, `/it/events`, (etc.).
- Playwright E2E: 11/11 PASS at 1920x1080 on the public route set.
- SSR bundle audit: GSAP + Lenis absent from
  `frontend/.output/server/**`.

### Deferred / Open

- **TD-011** (jazzclub chrome contrast) — still open, no Phase 3 page
  exposes it. Resolution trigger: first Phase 4+ `body[data-location=
  "jazzclub"]` render.
- **TD-012** (`useFormattedDate` composable) — new, opened this phase.
  Resolution trigger: Phase 4+ event detail or calendar page needing
  user-friendly locale-aware date rendering.
- **TD-013** (livemagic primary vs `--color-error` collision) — new,
  opened this phase. Resolution trigger: first Phase 4+ livemagic-
  themed page that surfaces a primary CTA and an error state together.
- Phase-3-adjacent items tracked in the closing user-intent scan
  (`docs/reviews/2026-04-24-user-intent-scan-phase-3.md` §B): nav
  hover/active collision (fixed via rule 44), error `role="alert"`
  standardization (fixed via rule 45), favicon (fixed via rule 43),
  AppFooter motto i18n (fixed via rule 46), `LocationSlug` typed
  union (deferred to TD-008 close-out).

**Spec:** `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md`
**Plan:** `docs/superpowers/plans/2026-04-23-nuxt-integration.md`
**Scan:** `docs/reviews/2026-04-24-user-intent-scan-phase-3.md`
**Commits:** atomic Phase 3 commit (SHA to be filled in by controller
after commit).

---

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
**Commits:** `a9d20d2` (Phase 2 atomic commit) · `218f9d8` (placeholder
cleanup — replace `<phase-2-commit>` with real SHA in TECH_DEBT TD-006).

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

### Planned (Phase 4+)
- User auth flows wired end-to-end (login/logout/refresh/me BFF handlers
  + Pinia user store + auth middleware + auth-gated pages) — Phase 4
- DB-backed translations (`*_translations` tables) consumed by SSR via
  `Accept-Language` header on `flaskFetch` — Phase 4+
- `useFormattedDate` SSR-safe composable (TD-012) — Phase 4+
- `livemagic` vs `--color-error` collision resolution (TD-013) —
  Phase 4+ when a livemagic-themed route ships
- Design-system consolidation (`docs/DESIGN.md`) — end of Phase 4 (TD-007)
- Location management API + SSG pages with per-location theming + content —
  Phase 5
- Event management API + ISR event pages + detail routes — Phase 5
- Artist profiles API — Phase 5
- Blog / News API + on-demand ISR revalidation (admin POST to
  `/api/revalidate`) — Phase 5
- Admin dashboard (SPA, `ssr: false`) — Phase 6
- Google Calendar integration — Phase 7
- Facebook posting integration — Phase 7
- Patreon webhooks — Phase 7
- Second Life in-world API — Phase 7
