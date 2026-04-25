# Changelog

All notable changes to The Dreamer's Cave website project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Phase 6 (Production deployment artifacts)] -- 2026-04-25

Phase 6 lands the production deployment plumbing for the Nuxt 4 + Flask 3
stack on mioh1 (Apache + systemd). No application code changed; Phase 6
is a configuration + documentation phase. Production deploy itself is
operator-driven and follows the runbook authored here.

### Added

- `apache/thedreamerscave-prod.conf` -- production Apache vhost adapted
  from the dev vhost (`dev-thedreamerscave.conf`) and the plan's nginx
  template. TLS via unified-cert (16-domain SAN, auto-renewed). Routing
  split mirrors the dev setup: `/api/auth/**` and `/api/revalidate` to
  Nuxt :9501 (BFF, sets HttpOnly cookies); other `/api/**` to Flask
  :9500; `/_nuxt/` and `/favicon.ico` served as static disk; `/trullo`
  preserved as legacy passthrough; everything else to Nuxt SSR.
- `deploy/systemd/tdcweb-frontend.service` -- Nuxt SSR node systemd
  unit. Loads required env vars from `/etc/tdcweb/frontend.env`
  (NUXT_FLASK_URL, NUXT_COOKIE_SECRET, NUXT_PUBLIC_SITE_URL,
  NUXT_PUBLIC_API_BASE). Runs as `www-data`, port `127.0.0.1:9501`,
  hardened (NoNewPrivileges, ProtectSystem=strict, ReadWritePaths
  scoped to `.output/`).
- `deploy/systemd/tdcweb-backend.service` -- gunicorn-hosted Flask
  backend systemd unit. Loads `/etc/tdcweb/backend.env` with required
  SECRET_KEY + JWT_SECRET_KEY (ProductionConfig fails loud if missing
  per Phase 4 holistic-review HIGH fix). Runs as `www-data`, port
  `127.0.0.1:9500`, 4 workers x 8 threads.
- `docs/deployment/production.md` -- end-to-end production runbook:
  topology, prerequisites, secret provisioning, first-time install
  (code + venv + npm build + systemd + Apache vhost swap + smoke
  tests), re-deploy procedure, rollback, observability, cert renewal,
  known gotchas. Sections 3.1 + 3.2 codify the SSR env-var contract.

### Changed

- `.claude/agents/tdc-frontend-expert.md` -- three lingering "nginx"
  references (lines 59, 192, 673) replaced with Apache references to
  match production reality. Hand-off table and SSR-loopback paragraph
  now match `pdp-v3.md` and CLAUDE.md.
- `.claude/skills/tdc-docs/SKILL.md` -- "Vue.js 3 SPA" stack drift
  (line 42, 65) updated to the Nuxt 4 stack: app/ layer directory tree,
  Nitro server BFF, Tailwind v4 CSS-first, vee-validate+zod,
  `@nuxtjs/i18n` and `@nuxtjs/seo`. Aligns with the Phase 5 skill
  rewrites and Phase 4 patterns.
- `docs/TECH_DEBT.md` -- TD-014 (NUXT_FLASK_URL deployment runbook)
  moved to Closed items. Closing artifact: section 3.2 of
  `docs/deployment/production.md` plus the systemd unit
  `EnvironmentFile=` directive.

### Verification

- vitest 73/73 (no code changed; sanity rerun)
- pytest 46/46 (no code changed; sanity rerun)
- `grep nginx .claude/agents/tdc-frontend-expert.md` -> empty
- `grep 'Vue.js 3' .claude/skills/tdc-docs/SKILL.md` -> empty
- Apache `apache2ctl -t` validation deferred to deploy host (sudo not
  available in dev session)

### Deferred / out-of-scope

- Actual production deployment (operator-driven, runbook is the
  contract). Phase 7 will provide post-deploy smoke + Core Web Vitals
  verification.
- Strict CSP policy: Phase 6 vhost ships permissive CSP (Nuxt emits
  some inline scripts in payload). A strict policy lands in a future
  hardening pass once the inline-script surface is measured.

## [Phase 5 (Documentation + skill catch-up)] -- 2026-04-25

Phase 5 was scoped to documentation and skill maintenance. No application
code changed in this commit. Three of the four originally-planned
deliverables (5.1, 5.2, 5.3) had been pre-shipped during earlier phases;
Phase 5 closes the loop on the remainder so all authoritative TDC docs
and skills now describe the Nuxt 4 stack consistently.

### Changed

- `docs/plans/pdp-v3.md` -- Feature Roadmap synced: Phase 4 marked
  complete (commit `8fcc73c`, with Phase 4B parallel note); Phase 5
  marked complete (this commit); Phase 6 promoted to Next. Phase 4
  highlights section added (BFF auth chain, `useApiFetch`, `useAuth`,
  three route guards with pure helpers, Phase 4B parallel backend
  buildout, phase-end fixes for `routeRules.proxy` / `ProductionConfig`
  strict env / `flaskFetch` resilient pattern, opened TECH_DEBT
  TD-014 / TD-015 / TD-016 / TD-017, 119 total test cases). Phase 5
  highlights section added.
- `.claude/skills/tdc-frontend/SKILL.md` -- rewritten end-to-end for
  Nuxt 4: `app/` layer file structure, `useApiFetch` /
  `useFetch` / `$fetch` / `useRequestFetch` decision table, the seven
  SSR client-only rules, pure-helper extraction pattern, location
  theming via `useHead({ bodyAttrs })`, vee-validate + zod, BFF
  handler patterns, `routeRules.proxy` (NOT `nitro.devProxy`) for dev
  Flask routing. Down from 1636 to ~620 lines.
- `.claude/skills/tdc-testing/SKILL.md` -- rewritten for the current
  stack: vitest + `@nuxt/test-utils` + happy-dom (frontend) and
  pytest 9.x with real-MySQL fixtures (backend, no DB mocks per
  CLAUDE.md). Encodes bare-auto-import gotcha (server vs app code),
  the pure-helper extraction-over-`mockNuxtImport` rule, conftest
  fixture catalogue (`fresh_user`, `staff_user`, `admin_user`,
  `make_location`, `make_event` with auto-cleanup), Playwright at
  1920x1080. Down from 1539 to ~580 lines.
- `.claude/agents/tdc-frontend-expert.md` -- audit-only edits: added a
  "Phase 4 Patterns" section covering `useApiFetch` envelope adapter,
  `useAuth` with `useRequestFetch` for SSR cookies, three route guards
  with pure helpers, BFF handler catalogue, `flaskFetch` resilient
  pattern, `routeRules.proxy` vs `nitro.devProxy` precedence rule, and
  the pure-helper extraction TDC convention. Inline drift fixes:
  Tailwind reference corrected to `@tailwindcss/vite` (was
  `@nuxtjs/tailwindcss`); prod proxy reference corrected to Apache
  `mod_proxy_http` (was `nginx`).

### Tech Debt

- **TD-004 closed**: legacy `@studio-freight/lenis` references removed
  from both skill files. Verification:
  `grep -rn '@studio-freight/lenis' .claude/skills/` returns only one
  intentional "NOT `@studio-freight/lenis`" warning line in the
  rewritten `tdc-frontend/SKILL.md` (no usages, no imports).
  `pdp-v2.md` retained as-is (historical / WONTFIX per the original
  entry).

## [Phase 4 (Nuxt BFF auth) + 4B (Backend buildout)] -- 2026-04-25

Phase 4 wires end-to-end authentication: the Nuxt BFF (login / logout /
refresh / me handlers + admin-gated revalidate endpoint), the client
auth composable, and three route guards (auth / admin / staff). Phase
4B was injected mid-phase when recon discovered the Flask backend was
still at MVP-stub stage (only `/api/health` existed) and the BFF
handlers had nothing real to talk to. 4B built the User model, JWT
emission, bcrypt, auth decorators, three blueprints (auth /
locations / events), and a complete pytest suite against a real MySQL
test database (CLAUDE.md no-DB-mock rule). Phase 4 frontend then
resumed and closed the chain with real integration smoke.

End state: vitest 73/73, pytest 46/46, full E2E auth chain (login ->
me -> revalidate -> logout) verified via curl with Flask + MySQL +
Apache dev vhost. Working tree committed atomically per CLAUDE.md
rule 16(e).

### Added

#### Backend (Phase 4B)

- `backend/app/models/user.py` -- User model with bcrypt password
  verification, role accessor, `to_dict()` envelope-friendly dump.
  No SQLAlchemy: parameterized queries through `mysql-connector-python`
  via `app/utils/db.py`.
- `backend/app/utils/jwt_helpers.py` -- JWT emission and validation
  helpers. Access TTL 15 min, refresh TTL 7 d, HS256, `JWT_SECRET_KEY`
  loaded from env. `JWT_SECRET_KEY` made REQUIRED at app boot (HIGH
  blocker fix during phase-end review): missing var raises immediately
  rather than silently emitting tokens signed with a placeholder.
- `backend/app/utils/auth_decorators.py` -- `@jwt_required` decorator
  reads `Authorization: Bearer <jwt>` (capital B, single space, exact
  casing per playbook §11.3 contract), validates, attaches user row to
  `flask.g.current_user`. `@role_required('admin')` / `@role_required('staff')`
  layered on top.
- `backend/app/routes/api/auth.py` -- four endpoints:
  - `POST /api/auth/login` -- email + password validation, returns
    `{ success: true, data: { access, refresh, user } }`.
  - `POST /api/auth/logout` -- token-side no-op (cookies cleared by BFF),
    returns `{ success: true, data: { message: ... } }`.
  - `POST /api/auth/refresh` -- consumes Bearer refresh, rotates pair,
    returns `{ success: true, data: { access, refresh } }`.
  - `GET /api/auth/me` -- returns `{ success: true, data: User.to_dict() }`.
- `backend/app/routes/api/locations.py` -- read endpoints
  (`GET /api/locations`, `GET /api/locations/<slug>`).
- `backend/app/routes/api/events.py` -- read endpoints
  (`GET /api/events`, `GET /api/events/<id>`) with `upcoming` query
  filter. NULL `location_id` coerced to `0` -- TS types currently
  declare `number`; flagged TD-017.
- `backend/tests/test_foundation.py` (5 cases), `test_auth.py` (18),
  `test_locations.py` (10), `test_events.py` (12). 45 cases against
  real MySQL test schema (`tdcweb_test`) with conftest-managed session
  lifecycle and full state cleanup. CLAUDE.md no-DB-mock rule observed.
- `backend/app/routes/api/__init__.py` -- blueprint URL prefix dropped
  from `/api/v1` to `/api` (pre-flight controller alignment, scan row
  14). The `v1` prefix was scaffolding leftover that contradicted
  spec/plan/CLAUDE.md/pdp-v3 and the BFF expectation.

#### Frontend BFF (Phase 4 Tasks 4.1-4.3)

- `frontend/server/api/auth/login.post.ts` -- TDD-authored. zod
  validation of body, calls Flask, unwraps envelope, sets both cookies,
  returns `{ user }`.
- `frontend/server/api/auth/logout.post.ts` -- forwards to Flask
  (try/catch fallback), clears both cookies regardless.
- `frontend/server/api/auth/refresh.post.ts` -- pulls refresh token from
  cookie, calls Flask with `Authorization: Bearer <refresh>`, rotates
  pair.
- `frontend/server/api/auth/me.get.ts` -- gates on
  `event.context.flaskHeaders` defined, calls Flask, unwraps envelope.
- `frontend/server/api/revalidate.post.ts` -- admin-gated on-demand SSR
  cache invalidation. Path validation (no `..`, no `//`, max 500 chars,
  must start with `/`). Cache-key format derived from Nitro source
  (`cache:nitro:routes:_:<escapedPathname>.<hash>.json`) -- earlier
  spec/plan drafts had the prefix wrong; reconciled at this phase's
  docs-sync.

#### Frontend client (Phase 4 Task 4.4)

- `frontend/app/composables/useAuth.ts` -- thin wrapper over
  `useAuthStore`, exposes `user / isAuthenticated / isAdmin / isStaff`
  plus `fetchMe / login / logout`. Decision logic extracted into pure
  `buildAuthOps(store, fetcher)` for testability. Uses
  `useRequestFetch()` for SSR cookie-forwarding (raw `$fetch` does NOT
  forward incoming-request cookies to internal Nitro routes during SSR;
  authenticated users would loop back to login on every middleware
  pass).
- `frontend/app/utils/auth-guard.ts` -- pure helpers
  (`buildLoginRedirect`, `decideAuthOutcome`, `decideAdminOutcome`,
  `decideStaffOutcome`) consumed by the three route middlewares.
  `auth-guard.test.ts` exercises every branch.
- `frontend/app/middleware/auth.ts` / `admin.ts` / `staff.ts` -- thin
  wire-ups of auto-imports to the pure helpers. Bounce guests to
  `/auth/login?redirect=<encoded>`. Open-redirect validation in the
  login page itself is tracked as TD-015.
- `frontend/app/composables/useApiFetch.ts` -- envelope-unwrapping
  `useFetch` wrapper. `unwrapEnvelope<T>` + `resolveApiBaseURL(isServer,
  flaskUrl)` extracted as pure helpers (12 vitest cases). SSR baseURL
  set to `useRuntimeConfig().flaskUrl` because Vite devProxy is a
  dev-server middleware that does NOT intercept Nitro's internal SSR
  `$fetch`. Read pages (`/locations`, `/events`) retrofitted to consume
  the envelope-aware composable.

#### Tests

- Frontend vitest 73/73 (Phase 4 added: login-handler 2, useAuth 14,
  useApi 4 carryover, auth-guard cases, useApiFetch 12, plus existing
  flask-client / auth-forward / cookies). All green.
- Backend pytest 46/46 (foundation 5 + auth 18 + locations 10 + events
  12 + integration 1). All green against real MySQL.
- E2E auth chain verified by curl: login -> me -> revalidate -> logout
  through Apache dev vhost (`dev.thedreamerscave.club`) with HTTP basic
  auth, BFF cookies, Flask back-end, MySQL persistence.

### Changed

- `frontend/nuxt.config.ts` -- removed `nitro.devProxy` block. Replaced
  with per-prefix `routeRules.proxy` entries for the read endpoints
  (`/api/locations`, `/api/events`, `/api/health`, etc.). Reason: Nitro's
  `devProxy` registers as h3 middleware BEFORE the worker that hosts
  `server/api/*` routes, so a catch-all `/api` rule silently swallowed
  the BFF. `routeRules.proxy` is integrated with the route registry --
  static server routes win. Phase 6 Apache vhost is the prod analog.
- `frontend/server/utils/flask-client.ts` -- added `nitropack/runtime`
  module-level fallback for `useRuntimeConfig`. The Phase 3 TD-009
  closure assumed `useRuntimeConfig` would be on `globalThis` in real
  Nitro context; in dev/prod it is rewritten by the bundler to a
  `#imports` binding (NOT placed on globalThis). Pattern now mirrors
  `auth-forward.ts` and `cookies.ts`: globalThis stub (tests) ->
  imported helper (Nitro) -> explicit throw.
- `frontend/app/types/api.ts` -- envelope contract tightened. `ApiResponse<T>`
  has `success: true` discriminant; new `ApiErrorResponse` has
  `success: false`. BFF unwraps `.data` consistently.
- `frontend/app/pages/locations/index.vue` and
  `frontend/app/pages/events/index.vue` -- migrated from raw
  `useFetch<T[]>` (which iterated the envelope object as if it were the
  array) to `useApiFetch<T[]>`.
- `docs/TECH_DEBT.md` -- TD-014 / TD-015 / TD-016 / TD-017 opened with
  resolution triggers.

### Fixed

- **JWT_SECRET_KEY HIGH blocker (phase-end triple review)**: Flask
  emitted tokens signed with a default placeholder when the env var
  was unset, silently. Fixed by raising at app boot. Aligns with
  CLAUDE.md security rule 6.
- **BFF/Flask envelope contract drift (scan row 15)**: backend Flask
  used `responses.success(data)` envelope `{success, data}` per project
  convention; BFF Tasks 4.1-4.2 (already shipped uncommitted) read flat
  shape (`response.access`). Independently both sides passed unit
  tests because no integration test crossed the boundary; browser login
  would have set undefined cookies. BFF retrofitted to unwrap `.data`.
- **Nitro devProxy swallowing BFF routes**: see Changed -> nuxt.config.ts.
- **Vite devProxy not intercepting SSR $fetch**: see Added ->
  useApiFetch.ts. SSR baseURL set explicitly from runtime config.
- **useRuntimeConfig not on globalThis in real Nitro context**: see
  Changed -> flask-client.ts.
- **`/api/v1` -> `/api` prefix realignment**: README, CHANGELOG (this
  file), `docs/api/health.md`, `docs/deployment/development.md`, and
  CLAUDE.md project-structure inventory all reference the new prefix.

### Security

- `JWT_SECRET_KEY` now REQUIRED at boot. No silent placeholder.
- Refresh token rotation verified end-to-end by integration smoke
  (every refresh issues a new refresh).
- Cookie contract from Phase 2 unchanged: `tdc_access` HttpOnly Lax
  Path=/, `tdc_refresh` HttpOnly Strict Path=/api/auth.
- bcrypt password verification (12-round cost) per CLAUDE.md security
  rule 5.
- Admin gate on `/api/revalidate` -- 401 (no/invalid Bearer) vs 403
  (logged in but role != admin) disambiguated only by status code, not
  by body.
- Path validation on revalidate body: rejects `..` (traversal), `//`
  (ambiguous routing), >500 chars, missing leading `/`.

### Tests

- vitest 73/73 (frontend); pytest 46/46 (backend).
- Real-MySQL fixtures throughout backend tests; conftest restores DB
  state between sessions. State cleanup verified at phase end.
- Full E2E auth chain via curl with Apache dev vhost
  (`dev.thedreamerscave.club`).

### Infrastructure

- Apache dev vhost set up mid-Phase-4 per user decision: HTTP -> HTTPS
  redirect + Let's Encrypt cert + HTTP basic auth (`tdctest`) +
  ProxyPass to Nuxt :9503 (Nuxt internal routing handles `/api/auth`,
  `/api/revalidate`, with `routeRules.proxy` to Flask :9502 for other
  `/api`). Cert stays separate from `unified-cert` for now.
- New test database `tdcweb_test`, schema-replicated from `tdcweb_dev`,
  managed by pytest conftest fixtures.

### Verification

- `nuxi typecheck`: 0 errors.
- `npm test`: 73/73.
- `pytest`: 46/46 against real MySQL.
- E2E auth chain: login -> me -> revalidate -> logout via curl on
  `https://dev.thedreamerscave.club/`, all 200/204 with correct cookie
  semantics.
- DB state restored to clean baseline post-tests.

### Deferred / Open

- **TD-014** (`NUXT_FLASK_URL` deployment runbook): resolution trigger
  is Phase 6 systemd unit drafting.
- **TD-015** (login-page open-redirect validation): trigger is first
  task creating `app/pages/auth/login.vue`.
- **TD-016** (BFF handler unit-test coverage for logout/refresh/me):
  trigger is first refactor of any of the three handlers.
- **TD-017** (events.location_id NULL coerced to 0): trigger is first
  task admitting nullable-venue events.
- **TD-007** (`docs/DESIGN.md` consolidation): scheduled for end of
  Phase 4 per its own resolution trigger; deferred to a dedicated
  design pass.
- **TD-011** (jazzclub palette chrome contrast): trigger is first
  jazzclub-themed page; no Phase 4 page sets `[data-location="jazzclub"]`.
- **TD-012** (`useFormattedDate`): trigger is first user-friendly date
  rendering surface.
- **TD-013** (livemagic vs `--color-error` collision): trigger is
  first livemagic-themed page surfacing both a primary CTA and an
  error.

**Spec:** `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md`
**Plan:** `docs/superpowers/plans/2026-04-23-nuxt-integration.md`
**Scan:** `docs/reviews/2026-04-25-user-intent-scan-phase-4.md`
**Commits:** atomic Phase 4 commit (SHA to be filled in by controller
after commit).

---

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
  - `GET /api/health` - Basic health check
  - `GET /api/health/db` - Database connectivity check
  - `GET /api/health/full` - Full system health check
  - (Originally shipped at `/api/v1/*`; prefix dropped to `/api/*`
    pre-flight before Phase 4B.2 -- the `v1` was scaffolding leftover
    contradicting spec/plan/CLAUDE.md. Endpoint paths above reflect the
    as-built state.)
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
