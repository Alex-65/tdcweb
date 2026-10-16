# Project Development Plan (PDP) v3.0
# The Dreamer's Cave — Virtual Music Club Website

**Version:** 3.0
**Date:** 2026-04-24
**Domain:** thedreamerscave.club
**Hosting:** mioh1 (Hetzner Frankfurt, Ubuntu)
**Supersedes:** `docs/plans/pdp-v2.md` (kept as historical reference — do not edit)

---

## 0. What changed vs v2

v2 described a Vue 3 + Vite SPA. In April 2026 we pivoted to **Nuxt 4** to gain per-route rendering (SSG/ISR/SSR/SPA), native SEO tooling, and a thin server-side BFF for auth cookies. The product scope is unchanged; only the frontend runtime and deployment topology change.

The architectural decisions behind the pivot live in `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md`. The bite-sized implementation plan lives in `docs/superpowers/plans/2026-04-23-nuxt-integration.md`. This document is the product-level plan — read the spec/plan for engineering detail.

---

## 1. Executive Summary

The Dreamer's Cave is a virtual music club in Second Life, established in 2019. The club spans two adjacent sims (capacity 200+ concurrent visitors), features 10+ themed locations with custom-developed multimedia technology that synchronizes visual effects with live music. The motto is **"You Can See The Music"**.

This PDP drives the public website that:
- Showcases the club's visual identity and 10+ themed venues
- Delivers an immersive Apple-style landing experience
- Manages events with Google Calendar integration
- Automates social posting (Facebook)
- Supports a Patreon-based revenue model with exclusive content
- Offers user registration with personalized notifications (EN / IT / FR / ES)
- Serves as an API endpoint for in-world Second Life displays

---

## 2. Technology Stack

### 2.1 Backend (unchanged from v2)

| Component | Technology | Notes |
|---|---|---|
| Framework | Python 3.11+ / Flask | RESTful API |
| Database | MySQL 8.x via `mysql-connector-python` | **NO SQLAlchemy** (project rule) |
| Auth emit | Flask + JWT (access 15 min, refresh 7 d, rotation on use) | Issued to the Nuxt BFF |
| OAuth providers | Authlib — Google, Discord, Facebook | |
| Email | SMTP (self-hosted iRedMail) | |
| Task queue | Celery + Redis | Async jobs (email, social posting) |
| Caching | Redis | Session + query cache |

### 2.2 Frontend (new in v3)

| Component | Technology | Notes |
|---|---|---|
| Meta-framework | **Nuxt 4** (`app/` layer, `compatibilityVersion: 4`) | |
| UI | Vue 3 Composition API, `<script setup lang="ts">` | |
| Language | **TypeScript (strict)** | `typescript.strict: true` |
| Build | Vite under Nuxt | HMR + ESM + tree-shaking |
| Styling | Tailwind CSS **v4 CSS-first config** via `@tailwindcss/vite` | No `tailwind.config.ts` at root |
| Theme tokens | CSS variables per location (`[data-location="<slug>"]`), `@theme` block in `main.css` | Zero-JS at paint |
| Animations | GSAP + ScrollTrigger + Lenis | `.client.ts` plugins only |
| State | Pinia via `@pinia/nuxt` | Stores: auth / locale / ui |
| i18n | `@nuxtjs/i18n` — `prefix_except_default` (EN / `/it/` / `/fr/` / `/es/`) | Cookie-based detection on root |
| SEO | `@nuxtjs/seo` + `@nuxtjs/sitemap` + `@nuxtjs/robots` | `useSeoMeta`, `useSchemaOrg` |
| Image | `@nuxt/image` (`<NuxtImg>` auto avif/webp) | |
| Icons | `lucide-vue-next` — named imports only | |
| Rich text | `@tiptap/vue-3` | Admin only, `<ClientOnly>`-wrapped |
| Forms | `vee-validate` + `zod` via `toTypedSchema` | Same schema client + server (`readValidatedBody`) |
| Utilities | `@vueuse/nuxt` | |

### 2.3 Authentication transport

| Component | Technology | Notes |
|---|---|---|
| Cookie (access) | `tdc_access` — HttpOnly, `Secure` prod, SameSite=Lax, Path=`/`, TTL 15 min | |
| Cookie (refresh) | `tdc_refresh` — HttpOnly, `Secure` prod, SameSite=Strict, Path=`/api/auth`, TTL 7 d, rotated | |
| Nuxt BFF | `frontend/server/api/auth/**` + `frontend/server/api/revalidate` | Issues/clears cookies; all other `/api/**` pass through to Flask |
| Forwarding | `frontend/server/middleware/auth-forward.ts` | Reads cookie → stamps `event.context.flaskHeaders = { Authorization: 'Bearer <jwt>' }` |
| Flask client | `frontend/server/utils/flask-client.ts` — `flaskFetch(url, event, options?)` | Merges flaskHeaders into every outbound call |

### 2.4 Infrastructure

| Component | Technology | Notes |
|---|---|---|
| Server | Ubuntu 22.04 | mioh1 @ Hetzner Frankfurt |
| Web server | Apache (`mod_proxy_http`, `mod_rewrite`, `mod_headers`) | Reverse proxy + static assets |
| SSL | Let's Encrypt (certbot) | Auto-renewal |
| Backend runtime | Gunicorn + systemd (`tdcweb-backend.service`) | `:9500` prod |
| Frontend runtime | Node + systemd (`tdcweb-frontend.service`) | `nuxt build` → `node .output/server/index.mjs`, `:9501` prod |

### 2.5 Testing

| Layer | Tool |
|---|---|
| Frontend unit / component | vitest + `@nuxt/test-utils` + happy-dom |
| Frontend E2E | Playwright (1920x1080 — CLAUDE.md rule) |
| Backend unit | pytest |
| Integration | pytest + real MySQL (no DB mocking per project convention) |

### 2.6 Port allocation

| | Dev | Prod |
|---|---|---|
| Flask | `:9502` | `:9500` (gunicorn, systemd) |
| Nuxt | `:9503` (`nuxi dev`) | `:9501` (node, systemd) |
| MySQL | `:3306` | `:3306` |

Both backend and Nuxt bind to `127.0.0.1` in prod; only Apache reaches them.

---

## 3. Database Schema

Unchanged from v2 — see `docs/plans/pdp-v2.md` §3 for the core tables (users, oauth_accounts, password_reset_tokens, locations, events, artists, blog_posts, favorites, notifications, etc.).

Any schema change in v3 era is captured via migrations under `backend/migrations/` and documented in `docs/database/schema.md` + `docs/database/migrations.md`.

User roles: `user` / `staff` / `admin` (plus `guest` = unauthenticated visitor, no DB row).

---

## 4. Rendering Strategy

Per-route via `routeRules` in `frontend/nuxt.config.ts`:

| Route pattern | Strategy | TTL / Notes |
|---|---|---|
| `/`, `/about`, `/contact` | **SSG** (`prerender: true`) | Build-time, rarely changes |
| `/locations`, `/locations/**` | **SSG** + on-demand revalidate | 10 venues, admin-edited |
| `/artists`, `/artists/**` | **SSG** + on-demand revalidate | Few changes |
| `/events`, `/events/**` | **ISR** (`swr: 300`) | 5 min stale-while-revalidate |
| `/blog`, `/blog/**` | **ISR** (`swr: 3600`) + on-demand | 1 h + instant-publish via revalidate |
| `/auth/login`, `/auth/register`, `/auth/callback/**` | **SSR** (no cache) | Dynamic per session |
| `/dashboard/**`, `/admin/**` | **SPA** (`ssr: false`) | Auth-gated, no SEO value |
| `/api/auth/**`, `/api/revalidate` | Nitro server routes (BFF) | Handled by Nuxt node |
| `/api/**` (other) | Proxied to Flask | Apache `mod_proxy_http` (prod), Nitro devProxy (dev) |

**On-demand revalidation**: admin save → client POSTs `/api/revalidate { path }` → Nitro clears cache for the path → next visitor gets fresh content.

**SEO**: `useSeoMeta` on every public page, `useSchemaOrg` for rich results (Place / Event / MusicGroup / Article / BlogPosting), `@nuxtjs/sitemap` with DB-backed dynamic entries, `@nuxtjs/robots` with disallow list for `/dashboard`, `/admin`, `/api/auth` (localized paths auto-expanded).

---

## 5. SSR Architecture (Hybrid BFF)

```
                                 ┌────────────────────────────────┐
  [Browser]  ──►  :443 Apache ──►│ /_nuxt/, /assets → static disk │
                                 │ /api/auth/**    → :9501 Nuxt   │
                                 │ /api/revalidate → :9501 Nuxt   │
                                 │ /api/**         → :9500 Flask  │
                                 │ /               → :9501 Nuxt   │
                                 └────────────────────────────────┘
                                           │
                        Nuxt SSR server-to-server → Flask :9500
                        (bypasses Apache, loopback; carries Bearer
                         from event.context.flaskHeaders)
```

- Only `/api/auth/**` and `/api/revalidate` go through Nuxt server routes; everything else passes straight to Flask.
- Auth tokens live exclusively in HttpOnly cookies; never in `localStorage` / `sessionStorage` / response bodies.
- SSR data fetches use relative `/api/...` paths which Nuxt's server resolves to Flask internally at render time.

See `docs/frontend/nuxt-playbook.md` §11 for code patterns and `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md` §8 for the full architecture rationale.

---

## 6. Location Theming System

10+ themed venues grouped into three moods per CLAUDE.md:
- **Cosmic / Tech** — DreamersCave, DreamVision, Evanescence
- **Hybrid** — LiveMagic, The Lounge
- **Warm / Intimate** — Arquipélago, Noah's Ark, Jazz Club

Each venue has its own CSS-variable palette declared under `[data-location="<slug>"]` in `frontend/app/assets/css/main.css`. Tailwind tokens (`primary`, `secondary`, `accent`, `dark`, `surface`, `hero-gradient`) are indirected through `var(--tdc-*)` so switching locations means swapping the `body[data-location]` attribute — no utility regeneration, zero JS at paint.

The `useLocationTheme(slug)` composable uses `useHead({ bodyAttrs })` so the attribute is set server-side during SSR and flows into the first HTML paint. No flash.

2 of the 10+ venues do not yet have designed palettes — tracked as `TD-008` in `docs/TECH_DEBT.md`. Pages for those venues fall back to the `:root` default palette.

---

## 7. Feature Roadmap

The feature list is unchanged from v2 §11. The implementation phasing is re-cadenced around Nuxt migration phases:

| Phase | Scope | Status |
|---|---|---|
| **1** | Nuxt scaffold + Nuxt modules + runtime / test deps | ✅ Complete (commits `8be146c`, `0cb13ce`, `2091253`, `3b6aa99`, `dbebfc4`) |
| **2** | Core configuration + BFF plumbing + theme substrate + test harness | ✅ Complete (commit `a9d20d2`) |
| **3** | Port the public-facing Vue surface to Nuxt: app.vue + layout + error page + AppHeader + AppFooter + 3 public pages (home SSG, locations SSG, events ISR) + 4 composables (useApi, useScrollAnimation, useSmoothScroll, useLocationTheme) + 3 Pinia stores (auth/locale/ui) + 4 i18n locale JSON files (EN/IT/FR/ES) | ✅ Complete (commit `724d5f1`) |
| **4** | Server-side auth flows (login/logout/refresh/me) + SPA auth-gated routes (dashboard, profile, favorites, notifications) | ✅ Complete (commit `8fcc73c`) -- BFF auth + backend buildout (4B parallel) |
| **5** | Docs + agent/skill updates for Nuxt 4 (some already done as prep work); finalize `pdp-v3.md` as source of truth | ✅ Complete (this commit) |
| **6** | Apache vhost (`mod_proxy_http`) + systemd production config + deploy workflow | ✅ Complete (commit `62e2f34`) -- TD-014 closed |
| **7** | Phase-end smoke / E2E / Core Web Vitals verification | ✅ Complete (this commit) |

### Phase 3 highlights (2026-04-24)

Phase 3 landed as 12 main tasks (3.0 through 3.11) plus 4 polish
sub-tasks (3.2b, 3.3b, 3.5b, 3.6b) plus 2 typecheck-batch passes and
5 controller-level phase-end micro-edits, all committed atomically.

- **TD-009 closed** preemptively as Task 3.0 (`flask-client.ts`
  resilient-pattern rewrite).
- **TD-011 opened** (jazzclub palette chrome contrast regression
  from the outline-login refactor, deferred to first jazzclub route).
- **TD-012 opened** (`useFormattedDate` SSR-safe composable, driven
  by Phase 4+ event detail / calendar needs).
- **TD-013 opened** (`livemagic` primary collides with `--color-error`
  semantic token, deferred to first livemagic route).
- **New semantic token** `--color-error` added to `main.css`
  `@theme` + `:root`. Pattern codified in playbook §14.5: add tokens
  alongside first consumer, don't wait for design-system consolidation.
- **Preemptive-polish 7-point pattern** formalized in playbook §23.1
  after Task 3.7 shipped polished from the first commit (zero
  reviewer-blocking findings).
- **Three-layer reduced-motion discipline** (Lenis plugin + two
  composables) per playbook §9.
- **Flat component naming via `components.pathPrefix: false`** in
  `nuxt.config.ts` to honour the plan's `<AppHeader />` (not
  `<CommonAppHeader />`) while keeping the `common/` subdirectory.
- 21/21 unit tests + 11/11 Playwright E2E (1920x1080) PASS; prod build
  + SSR bundle audit confirm `gsap`/`lenis` absent from server chunks.

### Phase 4 highlights (2026-04-25)

Phase 4 wired the end-to-end auth chain (BFF + composable + guards) and
ran in parallel with Phase 4B, which built the Flask backend out from
the MVP `/api/health` stub to a production-shaped surface (User model,
JWT, auth decorators, three blueprints, full pytest suite on real
MySQL). Closing commit: `8fcc73c`.

- **BFF auth chain**: `server/api/auth/login.post.ts`,
  `logout.post.ts`, `refresh.post.ts`, `me.get.ts` -- HttpOnly cookies
  (`tdc_access` 15 min Lax / `tdc_refresh` 7 d Strict Path=/api/auth,
  rotated on use); zod-validated inputs; envelope-aware Flask calls.
- **`/api/revalidate`**: admin-gated on-demand SSR cache invalidation
  with hardened path validation (no `..`, no `//`, max 500 chars) and
  the correct Nitro cache-key format
  `cache:nitro:routes:_:<escapedPathname>.<hash>.json`.
- **`useApiFetch<T>` envelope adapter**: unwraps Flask
  `{success: true, data: T}` to `T` via `unwrapEnvelope`; SSR baseURL
  split via `resolveApiBaseURL(isServer, flaskUrl)` (loud-fail when
  `NUXT_FLASK_URL` missing in SSR -- TD-014).
- **`useAuth` composable + `auth`/`admin`/`staff` middleware**: pure-
  helper extraction (`buildAuthOps`, `decideAuthOutcome`,
  `decideAdminOutcome`, `decideStaffOutcome`, `buildLoginRedirect`)
  separates testable decision logic from Nuxt auto-import wrapping.
  SSR cookie forwarding handled via `useRequestFetch()`.
- **Phase 4B parallel**: `User` model (bcrypt cost 12), JWT helpers
  (PyJWT 2.10+ str-sub canonicalization), `@jwt_required` /
  `@role_required` decorators, three blueprints (auth / locations /
  events) -- 46 pytest cases on real MySQL `tdcweb_test` schema, no
  mocks per CLAUDE.md.
- **Phase-end fixes (working tree, controller-applied)**:
  - `nitro.devProxy` catch-all replaced by `routeRules.proxy` for
    Flask routing in dev -- precedence ordering matters; `routeRules`
    correctly defers `/api/auth/**` and `/api/revalidate` to Nitro.
  - `ProductionConfig` made strict: `SECRET_KEY` and `JWT_SECRET_KEY`
    raise on missing env (no placeholder fallback in prod path).
  - `flaskFetch` made resilient: `nitropack/runtime` fallback for
    `useRuntimeConfig` plus stub-first dispatch (matches the
    `auth-forward.ts` / `cookies.ts` resilient pattern from Phase 3).
- **TECH_DEBT opened**: TD-014 (`NUXT_FLASK_URL` deployment runbook,
  Phase 6 trigger), TD-015 (login open-redirect validator, login-page
  task trigger), TD-016 (BFF handler unit tests for logout/refresh/me),
  TD-017 (`events.location_id` NULL coercion).
- **Tests**: 73 vitest + 46 pytest = 119 cases total. Full E2E auth
  chain (login -> me -> revalidate -> logout) verified via curl with
  Flask + MySQL + Apache dev vhost.

### Phase 5 highlights (2026-04-25)

Phase 5 was scoped to documentation + skill catch-up. Three of four
deliverables (5.1, 5.2, 5.3) had been pre-shipped as prep work during
earlier phases; Phase 5 closes the loop on the remainder so all
authoritative docs and skills now describe the Nuxt 4 stack
consistently.

- **TD-004 closed**: legacy `@studio-freight/lenis` references removed
  from both skill files. `pdp-v2.md` retained as historical (intentional
  WONTFIX per the original entry).
- **`pdp-v3.md` synced**: roadmap reflects Phase 4 close (`8fcc73c`)
  and Phase 5 close; Phase 4 highlights section codifies the BFF /
  Phase 4B / phase-end-fixes story.
- **`.claude/skills/tdc-frontend/SKILL.md` rewritten**: Vue 3 SPA
  contents replaced by Nuxt 4 -- `app/` layer file structure,
  `useApiFetch` / `useFetch` / `$fetch` / `useRequestFetch` decision
  table, the seven SSR client-only rules, pure-helper extraction
  pattern, location theming via `useHead({ bodyAttrs })`,
  vee-validate + zod + `useSeoMeta` snippets. Down from 1636 lines.
- **`.claude/skills/tdc-testing/SKILL.md` rewritten**: vitest +
  `@nuxt/test-utils` + happy-dom (frontend) and pytest with
  real-MySQL fixtures (backend) replace the pre-Nuxt content. Encodes
  the bare-auto-import gotcha (server vs app code), the pure-helper
  extraction-over-mockNuxtImport rule, the no-DB-mock convention, and
  the conftest fixture catalogue (`fresh_user`, `staff_user`,
  `admin_user`, `make_location`, `make_event`). Down from 1539 lines.
- **`tdc-frontend-expert.md` audited**: see audit verdict in commit
  log; Phase 4 patterns (`useApiFetch`, `useAuth`, route guards, BFF
  handlers, `flaskFetch`, `routeRules.proxy`, pure-helper extraction)
  all confirmed present or added as a "Phase 4 patterns" section.

### Phase 6 highlights (2026-04-25)

Phase 6 lands the production deployment artifacts. Adapted from the
plan's nginx template to Apache (`mod_proxy_http`) per CLAUDE.md and
user direction; vhost mirrors the dev vhost (`dev-thedreamerscave.conf`)
that already proves the routing split works in practice.

- **`apache/thedreamerscave-prod.conf`**: Nuxt-aware production vhost.
  TLS via `unified-cert` (16-domain SAN). Routing split: `/api/auth/**`
  and `/api/revalidate` to Nuxt :9501 (BFF, sets HttpOnly cookies);
  other `/api/**` to Flask :9500; `/_nuxt/`, `/favicon.ico` static
  disk; `/trullo` legacy passthrough; everything else to Nuxt SSR.
- **`deploy/systemd/tdcweb-frontend.service`**: node SSR unit.
  EnvironmentFile `/etc/tdcweb/frontend.env` (NUXT_FLASK_URL,
  NUXT_COOKIE_SECRET, NUXT_PUBLIC_SITE_URL). Hardened with
  `NoNewPrivileges`, `ProtectSystem=strict`, `ReadWritePaths` scoped
  to `.output/`.
- **`deploy/systemd/tdcweb-backend.service`**: gunicorn unit.
  EnvironmentFile `/etc/tdcweb/backend.env` with required `SECRET_KEY`
  and `JWT_SECRET_KEY` (ProductionConfig fails loud if missing per
  Phase 4 holistic-review HIGH fix). 4 workers x 8 threads.
- **`docs/deployment/production.md`**: end-to-end runbook (topology,
  prerequisites, secret provisioning, first-time install, re-deploy,
  rollback, observability, cert renewal, known gotchas).
- **TD-014 closed**: NUXT_FLASK_URL deployment runbook gap. Closing
  artifact: runbook sections 3.2 + 9.
- **Phase 5 carry-over docs drift fixed**: 3 nginx mentions in
  `tdc-frontend-expert.md` and "Vue.js 3 SPA" in `tdc-docs SKILL.md`.

### Phase 7 highlights (2026-04-25) -- migration DoD

Phase 7 verified the Definition of Done for the Nuxt 4 migration. No
application code changed; this phase is observational with a final
production-build smoke.

- **7.1 / 7.2 SSR + SPA segregation**: dev landing renders "You Can
  See The Music" (3 occurrences); `/dashboard` (`ssr: false`) is empty
  SPA shell with no auth content in the HTML payload.
- **7.3 BFF login round-trip**: Nitro returns 401 on bad creds with
  CSP / X-Frame-Options security headers (Nitro origin), confirming
  the BFF chain is hit (not Flask via devProxy bypass). Full happy-
  path was already verified during Phase 4 end-of-phase smoke
  (login -> me -> revalidate -> logout chain on real MySQL with
  cookie rotation).
- **7.4 production build + node preview**: `npx nuxt build` succeeds
  with output 48MB (sharp binaries for `linux-x64` bundled by
  `@nuxt/image`). Node preview on `:9501` (matches systemd unit)
  serves landing + `/it` Italian motto + `/api/auth/me` BFF +
  `/sitemap_index.xml` (4 sub-sitemaps). Build artifacts gitignored.
- **7.5 full unit suite**: vitest 73/73 + pytest 46/46 = 119 cases
  green (sanity rerun; no code changed).
- **7.6 i18n**: Italian root `/it` renders with `lang="it-IT"` +
  "Puoi vedere la musica" (3 occurrences). EN/IT/FR/ES locales all
  load via `@nuxtjs/i18n` lazy JSON.
- **7.7 cleanup + handoff**: working tree clean, `.output/` and
  `.nuxt/` gitignored, all phases marked complete in the roadmap
  table above. Next steps live below in the Feature Roadmap section.

Migration totals across phases 1-7: see CHANGELOG for the running
ledger. The Nuxt 4 migration as scoped by this plan is complete;
feature pages (locations/:slug detail, events/:id, artists, blog,
auth UI, admin panel) are out of scope for this migration and will
land as separate spec + plan pairs.

Feature areas (each will become one or more spec + plan pairs under `docs/superpowers/`):
- Landing page with Apple-style scroll storytelling (GSAP + ScrollTrigger + Lenis)
- Locations catalogue (10+ venues) with per-location theming
- Events calendar with Google Calendar sync (staff + public calendars)
- Artists directory with Schema.org MusicGroup markup
- Blog (SSG / ISR with admin on-demand revalidate, TipTap editor)
- User accounts: register, login (email + OAuth), profile, favorites, notifications
- Admin panel: user management, event / location / artist / blog CRUD, integrations
- Patreon integration: webhook, supporter badge, exclusive content
- Facebook posting automation (Celery + page/group APIs)
- Second Life in-world API endpoints (public, read-only, JSON)
- i18n end-to-end: UI strings + DB-backed translations (`*_translations` tables)

---

## 8. Agents and workflow

TDC uses a 27-agent ecosystem (see `CLAUDE.md` §Intelligent Agent System) grouped into:
- **Core development** (7): database, API, frontend, backend, auth, integration, documentation experts
- **Review Guardians** (3): `tdc-code-reviewer`, `tdc-design-enforcer`, `tdc-design-system-enforcer` — enforce CLAUDE.md rules 15–18 (per-task + phase-end review, docs sync, tech-debt discipline)
- **Testing & Quality** (5): testing-expert + visual / E2E / browser-performance / accessibility testers
- **Specialized Support** (6): security, performance, UX, network, troubleshooting, problem-isolator
- **Coordination** (2): orchestrator, problem-isolator
- **Advisory System** (5): architecture / security / performance / risk / coordinator — for complex decision resolution

Development cadence, per CLAUDE.md rule 16: **phase-end commit protocol** — working tree accumulates per-task work (no per-task commits); at phase boundary we run triple review (code-reviewer + design-system-enforcer), real tests (E2E / build / security), state cleanup, documentation sync (`tdc-documentation-expert`), then atomic commit(s) of code + docs together.

---

## 9. Security & Compliance

- **GDPR**: every collect/store of personal data requires explicit consent; audit logs for admin actions; retention policies; user-initiated data deletion. No HIPAA (not applicable to a music-club site).
- **Auth**: JWT HttpOnly cookies (never in JS-readable storage), SameSite=Lax on access / Strict on refresh, rotation, short access TTL.
- **CSRF**: SameSite cookies + Origin-header validation on mutating endpoints. No separate CSRF token cookie.
- **Input validation**: `zod` schemas at every boundary (client form, server route, Flask endpoint). `readValidatedBody` on Nuxt server routes; Flask uses matching validators.
- **SQL**: parameterized queries only (`mysql-connector-python %s` placeholders). No f-string / `.format()` SQL construction.
- **XSS**: no `v-html` on user input; Tailwind v4 compiled CSS only (no runtime `<style>` injection).
- **Secrets**: all in `.env` (gitignored), never in `nuxt.config.ts` non-`public` blocks leaked to client bundle. Grep-verified zero secret leaks in the Phase 2 client bundle.

---

## 10. Observability & Operations

- **Logs**: Flask via `logger.info(f"[module] ...")`, Nuxt Nitro via standard Node stdout, Apache access/error logs (`/var/log/apache2/`), MySQL slow-query log.
- **Healthchecks**: `GET /api/health` on Flask, root `/` on Nuxt.
- **Backups**: nightly MySQL dumps (retention per GDPR).
- **Deploy**: `git push` to production branch → manual `npm run build` + `systemctl restart tdcweb-frontend tdcweb-backend` on mioh1.

---

## 11. Out of Scope (this document)

- Engineering-level architectural detail — see `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md`.
- Bite-sized implementation tasks — see `docs/superpowers/plans/2026-04-23-nuxt-integration.md`.
- Tech-debt register — `docs/TECH_DEBT.md`.
- Frontend patterns + code recipes — `docs/frontend/nuxt-playbook.md`.
- Visual identity consolidated source (in planning) — `docs/DESIGN.md` (TD-007, due end of Phase 4).
- Deployment runbook — `docs/deployment/production.md` (created during Phase 6).

---

## 12. References

- **Historical**: `docs/plans/pdp-v2.md` (Vue+Vite era — do not edit)
- **Spec**: `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md`
- **Plan**: `docs/superpowers/plans/2026-04-23-nuxt-integration.md`
- **Playbook**: `docs/frontend/nuxt-playbook.md`
- **Tech Debt**: `docs/TECH_DEBT.md`
- **Changelog**: `CHANGELOG.md`
- **Project rules**: `CLAUDE.md` (always-loaded by every Claude session)
- **Dev setup**: `docs/deployment/development.md`
