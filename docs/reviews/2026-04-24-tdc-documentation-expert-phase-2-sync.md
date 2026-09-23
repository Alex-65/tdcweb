# Phase 2 — Documentation Sync Review

**Reviewer:** `tdc-documentation-expert`
**Timestamp:** 2026-04-24
**Last doc-sync commit:** `fefe316`
**Phase:** 2 — Nuxt 4 core configuration

## Scope analyzed

- Commits included: working tree (uncommitted — per rule 16 phase-level
  commit policy), reviewed against `fefe316..WT`.
- Files changed in scope: 14 (3 modified tracked + 11 new untracked,
  excluding `frontend.vue-backup/`, root `package-lock.json`, `.output/`,
  `.nuxt/`).

## Impact-matrix coverage

| Code change | Docs updated |
|---|---|
| `frontend/nuxt.config.ts` (Phase 1, re-checked) | CLAUDE.md stack table (already current) |
| `frontend/app/assets/css/main.css` Tailwind v4 rework | `nuxt-playbook.md` §14 (rewritten) · CLAUDE.md Location Theming (rewritten) · TECH_DEBT TD-006 closed · TD-008 opened |
| Server utils (`flask-client.ts`, `cookies.ts`) + middleware retrofit | `nuxt-playbook.md` §11 (rewritten to resilient pattern) · CHANGELOG Phase 2 entry · TECH_DEBT TD-009 opened |
| New plugins (`gsap.client.ts`, `lenis.client.ts`) | CLAUDE.md Animation System (rewritten) · CHANGELOG |
| New types under `app/types/*.ts` | CHANGELOG |
| New `.env.example` (env var names) | `docs/deployment/development.md` (rewritten) · README.md (rewritten) · CHANGELOG |
| New vitest infra + 15 tests | CHANGELOG · `docs/deployment/development.md` troubleshooting section |
| `typescript@^6` explicit devDep | TECH_DEBT TD-001 already closed (Phase 1) |
| `@tailwindcss/vite@^4` explicit dep | CHANGELOG · `nuxt-playbook.md` §14.1 |

## Files updated

- `CLAUDE.md` — agent count 24 → 27, project structure refreshed to
  Nuxt 4 layout (`app/`, `server/`, `i18n/locales/`), i18n section
  rewritten for `@nuxtjs/i18n` (was still saying `vue-i18n` + `frontend/src/i18n/`),
  Animation System example rewritten for client-only plugin pattern
  (was showing composable constructing `new Lenis()` — contradicts SSR
  rules), Location Theming example rewritten to current `--tdc-*`
  indirection + slug convention, Last Updated date refreshed.
- `README.md` — full rewrite. Was stuck in Vue + Vite era (`frontend/src/*`,
  `VITE_API_URL`, ports 9500/9501 labelled as dev).
- `CHANGELOG.md` — new Phase 2 entry (top-of-file, per keep-a-changelog).
  `[Unreleased].Planned` pruned of items Phase 2 delivered or phased to
  later, mapped remaining items to their target phases.
- `docs/frontend/nuxt-playbook.md` — §1.1 no longer lists `tailwind.config.ts`,
  §1.3 `nuxt.config.ts` example removes `@nuxtjs/tailwindcss` and adds
  `vite.plugins: [tailwindcss()]`, §11.3–§11.5 rewritten to match the
  real resilient globalThis-first-then-fallback pattern with
  implementation-note callout and TD-009 warning, §14.1–§14.2 rewritten
  for Tailwind v4 CSS-first config.
- `docs/deployment/development.md` — full rewrite. Was still Vue+Vite era.
  Now documents Nuxt 4 dev at `:9503`, Flask dev at `:9502`, the four
  `NUXT_*` env vars, vitest + test:watch, Tailwind v4 troubleshooting,
  globalThis/h3 test-stub pattern note.
- `docs/TECH_DEBT.md` — inspected; no corrections needed. TD-006 has
  `<phase-2-commit>` placeholder; per protocol the controller replaces
  it with the real SHA post-commit. TD-008 and TD-009 are well-formed.

## Files created

- `docs/reviews/2026-04-24-tdc-documentation-expert-phase-2-sync.md` —
  this artifact (first entry in the `docs/reviews/` tree). Going forward
  every phase-end sync leaves one here; per-task reviews from
  `tdc-code-reviewer` and `tdc-design-system-enforcer` will land here too.

## Files NOT updated (intentional)

- `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md` and
  `docs/superpowers/plans/2026-04-23-nuxt-integration.md` — these are
  historical brainstorm artifacts from Phase 1; the Phase 2 execution
  diverged on (a) Tailwind v4 CSS-first vs v3 module, (b) globalThis
  resilient pattern for h3 auto-imports. Per project convention (cf.
  `pdp-v2.md`) specs and plans are NOT retroactively edited — the
  CHANGELOG captures divergence.
- `docs/plans/pdp-v2.md` — historical by rule.
- `.claude/skills/tdc-frontend/SKILL.md`, `.claude/skills/tdc-testing/SKILL.md`
  — scheduled for rewrite in Phase 5 per TD-004 and the skill inventory.
  Lingering `@studio-freight/lenis` references there are already tracked.
- `docs/api/health.md`, `docs/backend/architecture.md` — untouched by
  Phase 2.

## CLAUDE.md drift detected and corrected

| Item | Before | Corrected to |
|---|---|---|
| Agent count | "24 Agents" (line 280 header) | "27 Agents" (actual `.claude/agents/` count) |
| Project Structure | `frontend/src/components/**`, `frontend/src/i18n/`, `frontend/src/styles/` (Vue+Vite era) | Nuxt 4 `app/` layer, `server/` BFF, `i18n/locales/`, types, plugins |
| i18n System | Said `/frontend/src/i18n/` + implied `vue-i18n` | `@nuxtjs/i18n` strategy `prefix_except_default`, `frontend/i18n/locales/`, detection order |
| Animation System composable | Showed `import Lenis from 'lenis'` then `new Lenis()` inside a composable — violates SSR Client-Only Rule #2 | Replaced with the real `.client.ts` plugin pattern + cleanup via `gsap.context()` / `ctx.revert()` |
| Location Theming example | `--color-primary` directly, no indirection, no slug-convention note | `--tdc-color-*` → `var(--color-*)` indirection through `@theme`, slug convention noted, TD-008 cross-ref |
| Last Updated | "January 2025" | "2026-04-24 (Phase 2 — Nuxt 4 core configuration)" |

No CLAUDE.md **rule** drifted — governance rules are stable. Corrections
were all to stack-reality sections.

## Findings for TECH_DEBT (none new)

Nothing new from the doc sync itself. TD-008 and TD-009 were already
opened by the per-task reviews in Phase 2. TD-006 was closed inline;
the `<phase-2-commit>` placeholder stays until the controller commits
and rewrites it with the real SHA.

## Link integrity

Spot-checked links inserted or updated:

- `docs/TECH_DEBT.md` references → file exists ✓
- `docs/frontend/nuxt-playbook.md` references (from CLAUDE.md, README.md,
  dev.md) → file exists ✓, sections referenced still exist after edits
  (§1.1, §1.3, §8–9, §11.3–§11.5, §14) ✓
- `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md` → exists ✓
- `docs/superpowers/plans/2026-04-23-nuxt-integration.md` → exists ✓
- `docs/plans/pdp-v2.md` → exists ✓
- `docs/plans/pdp-v3.md` → NOT yet created (Phase 5). README and CLAUDE.md
  describe it as "future" so no broken link.
- `docs/api/health.md`, `docs/backend/architecture.md` → exist ✓
- `docs/deployment/development.md` → rewritten in this sync ✓
- No dead links introduced.

## Stack-reference lint

Grepped the living docs for drift markers:

- `Vue + Vite` / `Vue.js 3 SPA` / `Vue 3 SPA` in living docs (CLAUDE.md,
  README.md, nuxt-playbook.md, development.md, TECH_DEBT.md) → 0 hits
  after sync ✓
- `frontend/src/` in living docs → 0 hits after sync ✓
- `@studio-freight/lenis` in living docs → 0 hits; only lingering
  references are in `docs/plans/pdp-v2.md` (historical, do not edit),
  `.claude/skills/tdc-frontend/SKILL.md` and `.claude/skills/tdc-testing/SKILL.md`
  (TD-004, scheduled for Phase 5 rewrite) ✓
- `@nuxtjs/tailwindcss` in living docs → 0 positive uses after sync
  (only mentions are negative "do NOT use — conflicts with v4") ✓
- `VITE_API_URL` in living docs → 0 hits after sync ✓

## Ready for controller commit

**Stage:**

```
git add \
  CHANGELOG.md \
  CLAUDE.md \
  README.md \
  docs/TECH_DEBT.md \
  docs/deployment/development.md \
  docs/frontend/nuxt-playbook.md \
  docs/reviews/2026-04-24-tdc-documentation-expert-phase-2-sync.md \
  frontend/.env.example \
  frontend/.nuxtrc \
  frontend/app/assets/css/main.css \
  frontend/app/plugins/gsap.client.ts \
  frontend/app/plugins/lenis.client.ts \
  frontend/app/types/api.ts \
  frontend/app/types/event.ts \
  frontend/app/types/location.ts \
  frontend/app/types/user.ts \
  frontend/package.json \
  frontend/server/middleware/auth-forward.ts \
  frontend/server/utils/cookies.ts \
  frontend/server/utils/flask-client.ts \
  frontend/tests/unit/auth-forward.test.ts \
  frontend/tests/unit/cookies.test.ts \
  frontend/tests/unit/flask-client.test.ts \
  frontend/vitest.config.ts
```

**Do NOT stage:**

- `frontend.vue-backup/` — historical local backup (untracked, intentional)
- root `package.json` / `package-lock.json` — pre-existing untracked,
  not touched by Phase 2
- `.output/`, `.nuxt/` — gitignored build artifacts

**Suggested commit message:**

```
feat(nuxt): Phase 2 — core configuration, BFF plumbing, Tailwind v4, test harness

Delivers the production-capable Nuxt 4 runtime, hybrid BFF auth
infrastructure, location-theming substrate, and vitest test harness that
Phases 3+ build against. No user-visible surface yet — infrastructure only.

Frontend runtime:
- nuxt.config.ts: routeRules matrix (SSG / ISR swr=300/3600 / SSR / SPA),
  Nitro devProxy to Flask :9502, runtimeConfig for flaskUrl/cookieSecret
  /apiBase/siteUrl, dev server :9503, TypeScript strict.
- app/assets/css/main.css: Tailwind v4 CSS-first config (@theme + --tdc-*
  indirection) with 8 location palettes grouped by mood. Closes TD-006.
- app/plugins/gsap.client.ts + lenis.client.ts: client-only, single RAF
  ticker, Lenis stopped on /admin/* and /dashboard/*.
- app/types/{api,user,location,event}.ts: shared TS interfaces.

Nuxt BFF (hybrid auth plumbing):
- server/middleware/auth-forward.ts: reads tdc_access cookie, stamps
  event.context.flaskHeaders with Bearer JWT.
- server/utils/flask-client.ts: flaskFetch wraps $fetch with baseURL +
  flaskHeaders forwarding. (TD-009 tracks prod Nitro globalThis risk.)
- server/utils/cookies.ts: TDC_ACCESS_COOKIE/TDC_REFRESH_COOKIE constants,
  setters with HttpOnly + Secure(prod) + SameSite + Path scoping,
  path-aware clearer, refresh-token getter.

Testing:
- vitest.config.ts + @nuxt/test-utils + happy-dom.
- 15 unit tests (flask-client ×3, auth-forward ×3, cookies ×9), all green.
- Resilient globalThis-first / h3-fallback pattern in auth-forward and
  cookies; flask-client tracked as TD-009 for Phase 4 verification.
- npm scripts: test, test:watch.

Stack additions: typescript@^6 explicit (closes TD-001),
@tailwindcss/vite@^4, @nuxt/test-utils@^4, vitest@^4, happy-dom@^20,
@playwright/test@^1.59.

Docs: CHANGELOG Phase 2 entry; README.md rewritten for Nuxt 4 reality;
CLAUDE.md agent count (24→27), project structure, i18n and animation
sections, Location Theming example refreshed; nuxt-playbook §11 + §14
rewritten for resilient BFF pattern and Tailwind v4 CSS-first config;
development.md rewritten for Nuxt 4 dev workflow; phase-2 doc-sync
review artifact under docs/reviews/.

Tech debt: closes TD-001 (typescript explicit), TD-006 (Tailwind v4
rework); opens TD-008 (2 location palettes missing), TD-009 (flask-client
globalThis-only — prod Nitro verification needed in Phase 4).

Verification:
- nuxt build: 13s, .output 46.7 MB, client bundle 452 KB, all 8 palettes
  in compiled CSS.
- Prod server boots on :9501 in ~1s; 200 on /, /it/, /robots.txt, 307
  on /sitemap.xml.
- Zero secret leaks in client bundle; zero SSR exclusion leaks in SSR HTML.
- 15/15 vitest unit tests green.

Spec:  docs/superpowers/specs/2026-04-23-nuxt-integration-design.md
Plan:  docs/superpowers/plans/2026-04-23-nuxt-integration.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

**Post-commit:**

1. Controller replaces `<phase-2-commit>` placeholder in
   `docs/TECH_DEBT.md` (TD-006 "Closed" line) with the real commit SHA
   and amends the atomic commit — OR lands a trivial follow-up, per
   phase-end protocol preference.
2. Controller appends the commit SHA under "Controller commit SHA" in
   this review artifact (line currently left blank).
3. Push happens only with explicit user authorization.

## Workflow documentation line

### Documentation Sync (phase 2)
- Timestamp: 2026-04-24
- Files updated: 6 (CLAUDE.md, README.md, CHANGELOG.md, docs/frontend/nuxt-playbook.md, docs/deployment/development.md, docs/TECH_DEBT.md [no content change, validated only])
- Files created: 1 (this review artifact)
- Drift items: 6 (all in CLAUDE.md, all corrected inline)
- Controller commit SHA: _(filled in by controller after commit)_
