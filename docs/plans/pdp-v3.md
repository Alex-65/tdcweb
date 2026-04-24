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
| Web server | Nginx | Reverse proxy + static assets |
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

Both backend and Nuxt bind to `127.0.0.1` in prod; only nginx reaches them.

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
| `/api/**` (other) | Proxied to Flask | nginx (prod), Nitro devProxy (dev) |

**On-demand revalidation**: admin save → client POSTs `/api/revalidate { path }` → Nitro clears cache for the path → next visitor gets fresh content.

**SEO**: `useSeoMeta` on every public page, `useSchemaOrg` for rich results (Place / Event / MusicGroup / Article / BlogPosting), `@nuxtjs/sitemap` with DB-backed dynamic entries, `@nuxtjs/robots` with disallow list for `/dashboard`, `/admin`, `/api/auth` (localized paths auto-expanded).

---

## 5. SSR Architecture (Hybrid BFF)

```
                                 ┌────────────────────────────────┐
  [Browser]  ──►  :443 nginx  ──►│ /_nuxt/, /assets → static disk │
                                 │ /api/auth/**    → :9501 Nuxt   │
                                 │ /api/revalidate → :9501 Nuxt   │
                                 │ /api/**         → :9500 Flask  │
                                 │ /               → :9501 Nuxt   │
                                 └────────────────────────────────┘
                                           │
                        Nuxt SSR server-to-server → Flask :9500
                        (bypasses nginx, loopback; carries Bearer
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
| **3** | Port the public-facing Vue surface to Nuxt: app.vue + layout + error page + AppHeader + AppFooter + 3 public pages (home SSG, locations SSG, events ISR) + 4 composables (useApi, useScrollAnimation, useSmoothScroll, useLocationTheme) + 3 Pinia stores (auth/locale/ui) + 4 i18n locale JSON files (EN/IT/FR/ES) | ✅ Complete (this commit) |
| **4** | Server-side auth flows (login/logout/refresh/me) + SPA auth-gated routes (dashboard, profile, favorites, notifications) | 📋 Next |
| **5** | Docs + agent/skill updates for Nuxt 4 (some already done as prep work); finalize `pdp-v3.md` as source of truth | 🟡 In progress (this doc counts) |
| **6** | Nginx + systemd production config + deploy workflow | 📋 Planned |
| **7** | Phase-end smoke / E2E / Core Web Vitals verification | 📋 Planned |

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

- **Logs**: Flask via `logger.info(f"[module] ...")`, Nuxt Nitro via standard Node stdout, nginx access/error logs, MySQL slow-query log.
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
