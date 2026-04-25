# TDC Technical Debt Register

**Philosophy:** Fix everything immediately whenever possible. This file
exists for items that genuinely cannot be fixed right now — not as a
buffer for deferred work.

**Rules of use:**
1. An item lands here only after an honest attempt to fix it failed
   (blocked by upstream, blocked by scope, blocked by another phase).
2. Every item has: **why it's here, what resolves it, priority, source
   (commit/phase/task that introduced or discovered it)**.
3. Every item has a **resolution trigger** — the specific condition
   that tells us it's ready to close. "Eventually" is not a trigger.
4. When a resolution trigger fires, we fix the item and move it to
   "Closed" with the resolving commit SHA.
5. This file is reviewed **at the start of every phase** and **as part
   of the phase-end triple review** (CLAUDE.md rule 16).
6. If an item sits open for 3+ phases without its trigger firing, it
   gets re-evaluated: either escalate to fix, or close as WONTFIX with
   explicit reasoning.

**Priority scale:**
- 🔴 **HIGH** — affects correctness, security, or user-facing behavior
- 🟡 **MEDIUM** — affects developer ergonomics, performance margins,
  or consistency that will compound if untouched
- 🟢 **LOW** — cosmetic, documentation, or nice-to-have

---

## Open items

### 🟢 TD-003 · `zod` pinned to v3 due to `@vee-validate/zod` peer

- **Source:** Task 1.4 (commit 2091253, 2026-04-23)
- **Issue:** Installed `zod@^3.25.76` because `@vee-validate/zod@4.15.1`
  requires `zod@^3.24.0`. Zod v4 is available and satisfies our own
  usage, but the peer range on the adapter blocks us.
- **Why it's open:** pinning v3 is the correct current choice. Upgrade
  path depends on `@vee-validate/zod` publishing a release that accepts
  `zod@^4`.
- **Impact:** low. Zod v3 is stable and feature-complete for TDC needs.
- **Resolution trigger:** `@vee-validate/zod` publishes a version whose
  peer range includes `zod@^4`. Check quarterly or when a new
  `vee-validate` major lands.
- **Close when:** `zod@^4` is in `frontend/package.json` and all form
  schemas still pass tests.

### 🟢 TD-008 · 2 location palettes missing from `main.css`

- **Source:** Task 2.3 (uncommitted in working tree, 2026-04-23)
- **Issue:** The spec and project description mention "10+ themed
  locations" but only 8 palettes are defined in
  `frontend/app/assets/css/main.css`: DreamersCave, DreamVision,
  Evanescence, LiveMagic, TheLounge, Arquipelago, NoahsArk, JazzClub.
  The authoritative sources (spec §10, nuxt-playbook §14,
  tdc-frontend-expert) enumerate the same 8.
- **Why it's open:** the remaining 2+ locations haven't been catalogued
  with slugs and palettes yet. Requires a product decision (which
  venues, what mood group, what colors) before palettes can be defined.
  Inline comment in `main.css` (lines 45-47) flags this.
- **Impact:** low. Pages for non-catalogued locations will fall back to
  the `:root` default palette. No visual breakage — just no unique
  identity for those venues until palettes are added.
- **Resolution trigger:** product-level input on the remaining
  location slugs + colour direction. Typically falls out of a design
  pass on the full location catalogue.
- **Close when:** `main.css` has a `[data-location="<slug>"]` block
  for every slug present in the `locations` table (query DB, compare
  with blocks in the CSS), with contrast-verified palettes.

---

### 🟡 TD-011 · Jazzclub palette fails chrome contrast after outline-login refactor

- **Source:** Task 3.3b (working tree, 2026-04-24). User-approved option (b) accept + log.
- **Current state (Phase 3 close, 2026-04-24):** still open. No Phase 3 page
  sets `body[data-location="jazzclub"]`, so user-visible impact is zero for
  this commit. Resolution remains deferred per user decision.
- **Issue:** The outline-style login button introduced by Task 3.3b (DS-3 fix) uses
  `text-primary` against `bg-dark` (#0c1222) in the resting state. The jazzclub
  palette defines `--tdc-color-primary: #92400e` (amber-800). Contrast ratio
  against bg-dark is 2.72:1, below WCAG 1.4.3 AA normal text (4.5:1) AND below
  1.4.11 non-text (3:1). This is a regression specific to jazzclub: the previous
  filled style (text-white on bg-primary) passed at 6.86:1 for this palette.
  The same regression affects the nav links' hover and active states (also
  text-primary on bg-dark) for jazzclub.
  7/8 palettes are NET-IMPROVED by the outline refactor; jazzclub is the only
  regression.
- **Why it's open:** The outline refactor was a strict win on 7 palettes
  (including all the worst filled-style offenders) and only regressed the one
  palette that was best under filled. The jazzclub location route
  (`/locations/jazzclub`) does not exist yet — it lands in Phase 4+ territory
  — so real user-visible impact is bounded to the period between now and when
  the page goes live. User chose to accept the regression now and revisit when
  jazzclub routes land.
- **Impact:** medium. Login CTA and nav chrome become unreadable for keyboard/
  screen-reader users on any page rendered under `body[data-location="jazzclub"]`.
  No such page exists yet; impact materializes at first jazzclub route.
- **Resolution trigger:** first Phase 4+ page that sets
  `body[data-location="jazzclub"]`. At that point the contrast must be fixed,
  not deferred further.
- **Close when:** text-primary against bg-dark for jazzclub meets at least
  WCAG 1.4.11 non-text (3:1) AND preferably 1.4.3 AA normal (4.5:1). Candidate
  approaches documented during Phase 3 Task 3.3b review:
  - (a) Lighten jazzclub primary (e.g. `#b45309` amber-700 → ~3.7:1, `#ea580c`
    orange-600 → ~5.0:1, `#f59e0b` amber-500 → ~10:1). Requires product
    sign-off on shifted warm-tone identity.
  - (c) Introduce a separate `--tdc-color-chrome` token per palette so hero /
    accent colors stay brand-faithful while chrome CTAs get a guaranteed-AA
    sibling.
  - (d) Swap jazzclub's chrome to `--tdc-color-accent` (#14b8a6 teal, ~7:1) —
    but teal is off-mood for a jazz venue. Sub-optimal.

---

### 🟢 TD-012 · `useFormattedDate` SSR-safe composable missing

- **Source:** Phase 3 closing scan row 38 (2026-04-24). Surfaced by Task 3.7
  (events list) rendering raw ISO 8601 in `<time>{{ event.starts_at }}</time>`.
- **Issue:** TDC has no helper for rendering DB-provided ISO 8601 timestamps
  (e.g. `"2026-05-15T20:00:00Z"`) in a locale-aware, user-friendly form
  (e.g. `"15 May 2026, 20:00"` for EN, `"15 maggio 2026, 20:00"` for IT).
  The naïve approach — `{{ new Date(iso).toLocaleString(locale) }}` inside a
  template — violates CLAUDE.md § SSR Client-Only Rules #4 (both `new Date()`
  from an ISO without explicit TZ and `.toLocaleString()` with the host's
  Intl data diverge between server and client and cause hydration mismatch).
  The safe shape is a composable: `useFormattedDate(iso, locale)` that either
  (a) runs at SSR time with a fixed `timeZone: 'UTC'` + the Nuxt `locale`,
  producing the same string server- and client-side, OR (b) uses a ref+onMounted
  pattern with a stable SSR fallback.
- **Why it's open:** Phase 3 pages only render raw ISO (events list is the
  single consumer). Developer-readable, not ideal for end users, but not a
  regression: no prior human-formatted rendering existed. Phase 4+ event
  detail and calendar pages drive the concrete need.
- **Impact:** low for now (one page, developer-shaped text). Escalates to
  medium once event detail + calendar pages ship and locale-aware
  formatting becomes a UX expectation.
- **Resolution trigger:** first Phase 4+ page that needs user-friendly date
  rendering (event detail page is the most likely driver). At that point,
  implement `frontend/app/composables/useFormattedDate.ts` + unit tests for
  SSR/client parity across EN/IT/FR/ES.
- **Close when:** `useFormattedDate(iso, locale)` exists under
  `frontend/app/composables/`, has vitest coverage proving identical output
  server-side and client-side for a fixed locale, and is adopted on every
  date-rendering surface (grep `toLocaleString` and raw-ISO `<time>` should
  return only test fixtures).

---

### 🟡 TD-013 · `livemagic` primary collides with `--color-error` semantic token

- **Source:** Phase 3 closing scan row 26, Task 3.6b design-system review.
- **Issue:** The new semantic-state token `--tdc-color-error: #ef4444` (added
  in Task 3.6b to make `text-error` / `bg-error` utilities available) collides
  with `[data-location="livemagic"] { --tdc-color-primary: #ef4444 }`. On any
  livemagic-themed page (Phase 4+), error messages rendered with `text-error`
  and primary CTAs rendered with `text-primary` produce identical RGB output.
  Users lose the semantic distinction between "this is the brand action" and
  "this is an error". Phase 3 impact: zero (no Phase 3 page sets
  `body[data-location="livemagic"]`; `:root` palette uses the same red for
  both tokens but there is no livemagic page yet to expose the collision
  visually).
- **Why it's open:** no Phase 3 page surfaces the collision. Fixing requires
  a product-informed choice between candidate resolutions, each with
  tradeoffs; forcing the decision mid-phase would be premature.
- **Impact:** medium. On a livemagic-themed page, a red error badge next to
  a red primary CTA is visually ambiguous. WCAG doesn't fail per se
  (both meet contrast) but the UX regression is real.
- **Resolution trigger:** first Phase 4+ page that sets
  `body[data-location="livemagic"]` AND surfaces both a primary CTA and an
  error state on the same viewport (e.g. auth pages under a livemagic theme,
  or any livemagic-themed form).
- **Close when:** primary CTA and error state are visually distinguishable on
  livemagic-themed pages. Candidate resolutions documented during review:
  - (a) Darken `--tdc-color-error` to `#dc2626` (red-600) globally. Still red,
    still conventional, unambiguous next to livemagic's `#ef4444` primary.
  - (b) Give error states a container surface instead of relying on text color
    alone (`bg-error/10 border border-error text-error`) so differentiation
    comes from shape+ground, not color alone. Scales to all palettes.
  - (c) Shift livemagic primary away from `#ef4444` (e.g. deeper orange
    `#ea580c`). Requires brand sign-off.

---

### 🟢 TD-007 · `docs/DESIGN.md` consolidated visual identity missing

- **Source:** tdc-design-system-enforcer agent creation (2026-04-23).
- **Issue:** TDC does not have a single authoritative visual-identity
  document. The design system currently lives fragmented across:
  - `CLAUDE.md` (Technology Stack + Location Theming + SSR rules)
  - `docs/frontend/nuxt-playbook.md` §14 (Tailwind + theming)
  - `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md` §9.6, §10
  - `.claude/agents/tdc-frontend-expert.md` (Quick Snippets, Location Theming)
  - `frontend/app/assets/css/main.css` (CSS vars when Task 2.3 lands)
- **Why it's open:** writing a full design system now would require
  product-level decisions (typography scale beyond Inter, spacing scale,
  full per-location palettes with contrast verification, motion tokens)
  that haven't been made yet. Premature consolidation risks locking in
  placeholders.
- **Impact:** medium. `tdc-design-system-enforcer` has to re-read
  fragmented sources every review. A consolidated doc would be faster
  and clearer. Gap scales as the project grows.
- **Resolution trigger:** by end of Phase 4 implementation, enough UI
  will exist to codify the full system. Alternatively, when the user
  invests a dedicated design pass to lock tokens/scales.
- **Close when:** `docs/DESIGN.md` exists with: full token table,
  10 per-location palettes with contrast checks, typography scale,
  spacing scale, motion tokens, component catalogue. The enforcer agent
  is updated to point at `docs/DESIGN.md` as its single source of truth.

---

### 🟡 TD-015 · Login page must validate `?redirect=` param against open-redirect

- **Source:** Task 4.4 (working tree, 2026-04-25). Code review LOW finding flagged for follow-up at login-page implementation time.
- **Issue:** The three route guards (`auth`/`admin`/`staff`) bounce unauthenticated users to `/auth/login?redirect=<encodeURIComponent(to.fullPath)>`. The redirect target is sourced from Vue Router's `to.fullPath`, which is always a relative path (Vue Router refuses absolute URLs as routes), so the guard side is safe. However, the LOGIN PAGE itself (not yet built) will have to read the `redirect` query param and `navigateTo` to it after a successful login. If the login page accepts the param without validation, an attacker could craft `/auth/login?redirect=https://evil.example/phish` and the post-login handler would happily redirect users off-site -- classic open-redirect (CWE-601). Phishing vector: a TDC-themed link arrives in email, user clicks, lands on real `/auth/login`, logs in legitimately, then gets bounced to attacker domain that mimics TDC and harvests further data.
- **Why it's open:** the login page is a future task (Phase 4 only built the BFF + composable + guards, not UI pages). Pre-emptively writing the validator now without the page would land orphan code.
- **Impact:** medium. Zero impact today (no login page consumes the redirect). Materializes the moment the login page reads the param. Easy to forget if not tracked.
- **Resolution trigger:** first task that creates `app/pages/auth/login.vue` (or wherever the login form lives). At that point, the post-login redirect handler MUST: parse the param via `URLSearchParams`, reject anything not matching `^/(?!/)` (relative path with single leading slash, no protocol-relative `//evil.com`), default to `/` on rejection, and ideally log the rejection for security observability.
- **Close when:** the login page implements the validation, has a vitest unit test that asserts rejection of `https://...`, `//evil.com`, `javascript:...`, and acceptance of legit relative paths like `/dashboard`, `/dashboard?tab=x`. Mention the validator helper in `docs/frontend/nuxt-playbook.md` § auth.

---

### 🟢 TD-016 · BFF auth handlers (logout/refresh/me) lack direct unit-test coverage

- **Source:** Phase 4 holistic review (working tree, 2026-04-25). MEDIUM forward-looking finding.
- **Issue:** Three of the four BFF auth handlers ship without dedicated vitest unit specs:
  - `frontend/server/api/auth/logout.post.ts` -- has try/catch fallback that clears cookies even if the Flask call throws; not asserted.
  - `frontend/server/api/auth/refresh.post.ts` -- extracts the refresh cookie, calls Flask, rotates cookies; rotation logic not asserted at unit level.
  - `frontend/server/api/auth/me.get.ts` -- gates on `event.context.flaskHeaders` being defined; the gate is not asserted.
  Login (`login.post.ts`) does have a test (`tests/unit/login-handler.test.ts`). Indirect coverage exists at two layers: backend pytest exercises Flask `/api/auth/*` end-to-end with real MySQL, and `useAuth.test.ts` mocks the fetcher so the composable's interaction with each route is verified. But the BFF wiring itself (cookie-set/clear sequencing, error fallthrough behavior, header gate) has no dedicated unit assertion.
- **Why it's open:** Phase 4 phase-end real tests (Playwright E2E for the full login -> me -> refresh -> logout chain) cover this transitively; adding three more handler-level specs at phase end wasn't a blocker for shipping the code. Logging here so the gap is visible if any of those handlers gets touched again.
- **Impact:** low. A regression in any of the three handlers would surface immediately in E2E. No silent-failure path identified.
- **Resolution trigger:** first refactor or behavior change to any of the three handlers, OR phase that introduces a new BFF auth concept (registration, password reset). At that point, mirror the `login-handler.test.ts` pattern: typed-globalThis stubs for `flaskFetch`/cookie helpers, assert handler returns expected shape, assert side effects (cookie set/clear) called with correct args.
- **Close when:** `tests/unit/{logout,refresh,me}-handler.test.ts` exist with at minimum one happy-path + one failure-path assertion each, and total vitest count grew accordingly.

---

### 🟢 TD-017 · `events.location_id` NULL coerced to 0 (type alignment)

- **Source:** Phase 4B.3 + holistic review (working tree, 2026-04-25). LOW finding.
- **Issue:** `backend/app/routes/api/events.py:111` coerces a NULL `location_id` to `0` before serializing to JSON. The DB schema permits NULL (events without an assigned venue, e.g. tentative future events). Frontend TS types currently declare `location_id: number`, which forced the coercion. Two consequences: (a) callers reading `event.location_id === 0` cannot distinguish "no venue assigned" from "venue with id 0" (which doesn't exist today, so accidental collision is unlikely but the semantics are wrong), (b) inline comment claims a TECH_DEBT entry exists for this -- this entry is that one.
- **Why it's open:** Phase 4B was scoped to read endpoints; expanding event types to admit nullable location was beyond scope. Frontend pages only display location_id transitively (via location-name lookup), so the coercion is invisible to current users.
- **Impact:** low. Cosmetic + semantic correctness. No data corruption.
- **Resolution trigger:** first task that adds an event-creation form OR an event-without-venue UX (e.g. "tentative" event states), OR any frontend code that needs to branch on "has venue vs. no venue".
- **Close when:** TS types updated to `location_id: number | null`, backend stops coercing, frontend grep `event.location_id === 0` returns nothing, and at least one test asserts the NULL pass-through.

---

### 🟢 TD-005 · Transitive deprecation warnings in npm

- **Source:** Tasks 1.3 and 1.4
- **Issue:** npm emits deprecation warnings for transitive packages we
  cannot directly control:
  - `inflight@1.0.6` (via build tools)
  - `glob@7.2.3` (via build tools)
  - `@koa/router@12.0.2` (via build tools)
  - `vue-i18n@10.x` (pulled by `@nuxtjs/i18n@10.2.4` — upstream hasn't
    bumped yet)
- **Why it's open:** transitive, not actionable from our `package.json`.
  Requires upstream modules to update their own dependencies.
- **Impact:** none functional, deprecation warnings in install output.
- **Resolution trigger:** monitor during module upgrades. When we bump
  `@nuxtjs/i18n` to a version that uses `vue-i18n@^11`, close that
  line item.
- **Close when:** a run of `npm install` in `frontend/` completes with
  zero deprecation warnings, OR we explicitly WONTFIX with reasoning.

---

## Closed items

### 🟡 TD-014 · `NUXT_FLASK_URL` SSR-side requirement not yet documented in deployment runbook

- **Source:** Task 4B.4 (working tree, 2026-04-25). Code review HIGH/MEDIUM fix round.
- **Issue:** `frontend/app/composables/useApiFetch.ts` introduced `resolveApiBaseURL(isServer, flaskUrl)` which throws on SSR if `runtimeConfig.flaskUrl` is empty/undefined. This is intentional (loud-fail beats silent 404 for every page that uses the composable), but the operational requirement -- "the SSR Node process MUST have `NUXT_FLASK_URL` set in its environment" -- was not codified in any deployment runbook.
- **Why it was open:** Phase 6 owns deployment (Apache vhosts, systemd units, prod env files). Documenting in `docs/deployment/` ahead of Phase 6 would have produced a stub doc; folding it into the Phase 6 deliverable was the clean fit.
- **Resolution trigger fired:** Phase 6 deployment runbook authored (2026-04-25).
- **Closed:** 2026-04-25 · Phase 6 atomic commit `62e2f34` -- `docs/deployment/production.md` codifies the SSR env-var contract in section 3.2 (`/etc/tdcweb/frontend.env`) listing `NUXT_FLASK_URL`, `NUXT_COOKIE_SECRET`, `NUXT_PUBLIC_SITE_URL`, `NUXT_PUBLIC_API_BASE`. The systemd unit at `deploy/systemd/tdcweb-frontend.service` references the env file via `EnvironmentFile=/etc/tdcweb/frontend.env`. Section 9 "Known gotchas" calls out the loud-fail behavior so on-call engineers can diagnose a misconfig in seconds.

---

### 🟢 TD-004 · Legacy `@studio-freight/lenis` references in 3 files

- **Source:** Task 1.4 (commit 2091253, 2026-04-23)
- **Issue:** The Lenis package was renamed from `@studio-freight/lenis`
  to `lenis`. We updated `CLAUDE.md`, the spec, the plan, and the
  playbook. Three non-authoritative files still referenced the old name:
  - `docs/plans/pdp-v2.md` (historical document — intentionally not
    updated per "v2 stays as historical reference")
  - `.claude/skills/tdc-frontend/SKILL.md` (old Vue+Vite skill,
    scheduled for full rewrite in Phase 5)
  - `.claude/skills/tdc-testing/SKILL.md` (testing skill, scheduled for
    review in Phase 5)
- **Why it was open:** `pdp-v2.md` is historical by design (do not edit);
  the two skill files were scheduled for a broader rewrite that would
  naturally incorporate the fix.
- **Resolution trigger fired:** Phase 5 skill rewrite (2026-04-25).
- **Closed:** 2026-04-25 · Phase 5 atomic commit `f685f5d` —
  `.claude/skills/tdc-frontend/SKILL.md` rewritten end-to-end for the
  Nuxt 4 stack; `.claude/skills/tdc-testing/SKILL.md` rewritten for
  vitest + `@nuxt/test-utils` + happy-dom (frontend) and pytest with
  real-MySQL fixtures (backend). `pdp-v2.md` left as-is (historical /
  WONTFIX, per the original entry's note). Verification:
  `grep -rn '@studio-freight/lenis' .claude/skills/` returns only one
  intentional "NOT `@studio-freight/lenis`" warning line in
  `tdc-frontend/SKILL.md` (no usages, no imports). All real usages
  removed.

### 🟡 TD-009 · `flask-client.ts` uses globalThis-only pattern — prod Nitro safety unverified

- **Source:** Task 2.7 review (2026-04-24) surfaced the risk.
- **Issue:** `frontend/server/utils/flask-client.ts` (Task 2.6) read
  `$fetch` and `useRuntimeConfig` exclusively from `globalThis` via
  helper functions. Task 2.7 proved that Nitro's prod bundle does NOT
  universally expose h3 auto-imports on `globalThis` — `getCookie` lives
  as a regular module binding in `.nuxt/dev/index.mjs:5736`. By analogy,
  `$fetch` and `useRuntimeConfig` could be module bindings in the prod
  bundle too, so the first SSR request that called `flaskFetch` would
  have risked `TypeError: $fetch is not a function`.
- **Why it was open:** unit tests passed because they installed
  globalThis stubs, hiding the flaw. Prod-safety verification required
  a real SSR hit or a preemptive rewrite.
- **Resolution trigger fired:** user approved option (A) — preemptive
  resilient-pattern rewrite — on 2026-04-24. Executed as Phase 3
  **Task 3.0** (inserted before Task 3.1).
- **Close when:** `flaskFetch` rewritten with stub-first + explicit
  fallback pattern matching `auth-forward.ts` and `cookies.ts`.
- **Closed:** 2026-04-24 · Phase 3 atomic commit `554a4a4`
  (Task 3.0) — `frontend/server/utils/flask-client.ts` rewritten:
  `$fetch` resolved via `globalThis` stub first, falling back to the
  `ofetch` `$fetch` import at module-eval time; `useRuntimeConfig`
  resolved via `globalThis` with an explicit `throw new Error(...)`
  when absent (no clean module fallback exists). Test coverage
  extended from 3 to 8 assertions: the original 3 happy-path tests
  plus a fallback-path test (globalThis $fetch deleted → ofetch mock
  invoked) plus a missing-runtimeConfig error test. Typecheck 0
  errors, test suite 8/8 on flask-client, 21/21 overall for the phase.

### 🟡 TD-001 · TypeScript not explicit in devDependencies

- **Source:** Phase 1 triple review (2026-04-23)
- **Issue:** `frontend/package.json` has no explicit `typescript`
  devDependency. TypeScript 6.0.3 is present transitively via
  `@nuxtjs/i18n`, `@nuxt/ui`, `nuxt` itself. `tsc` works via `npx`.
- **Why it's open:** functional now, but a transitive version is a
  ticking bomb — any module bump could shift the resolved TS version
  silently.
- **Impact:** medium. No immediate breakage. Risk of inconsistent TS
  errors across dev environments over time.
- **Resolution trigger:** Task 2.1 (core nuxt.config.ts + tsconfig.json
  setup). Add `npm install -D typescript@^6` at that step.
- **Close when:** `typescript` appears as a direct `devDependency` in
  `frontend/package.json`.
- **Closed:** 2026-04-23 · commit f585874 (Task 2.1) — installed
  `typescript@^6.0.3` as explicit `devDependency` in
  `frontend/package.json`.

### 🟡 TD-002 · `compatibilityDate` is scaffold default

- **Source:** Phase 1 triple review (2026-04-23)
- **Issue:** `frontend/nuxt.config.ts` was created by `nuxi init` with
  `compatibilityDate: '2025-07-15'`. The migration spec/plan specifies
  `'2026-04-01'` to opt into current Nuxt 4.x runtime behavior.
- **Why it's open:** will be rewritten as part of the full
  `nuxt.config.ts` replacement in Task 2.1.
- **Impact:** low. Some Nuxt 4 features shipped after 2025-07-15 may
  not be fully enabled until the date bumps.
- **Resolution trigger:** Task 2.1 — the new `nuxt.config.ts` block
  in the plan uses `'2026-04-01'`.
- **Close when:** `grep compatibilityDate frontend/nuxt.config.ts`
  shows `'2026-04-01'` (or later).
- **Closed:** 2026-04-23 · commit f585874 (Task 2.1) — full
  `nuxt.config.ts` rewrite landed with `compatibilityDate: '2026-04-01'`.

### 🟡 TD-006 · Task 2.3 plan needs rework for Tailwind v4 (CSS-first config)

- **Source:** Task 2.1 follow-up fix (2026-04-23), discovered at dev-boot smoke test.
- **Issue:** The plan prescribes a `tailwind.config.ts` (Tailwind v3
  pattern) wired via `@nuxtjs/tailwindcss`. But `@nuxt/ui` and
  `nuxt-og-image` (transitively pulled by `@nuxtjs/seo`) drag in
  `tailwindcss@4.x`. `@nuxtjs/tailwindcss@6` doesn't support v4 → dev
  boot fails with "PostCSS plugin has moved to separate package."
- **Fix applied inline:** Removed `@nuxtjs/tailwindcss` module, added
  `@tailwindcss/vite` as explicit dependency, wired Vite plugin in
  `nuxt.config.ts`, created stub `app/assets/css/main.css` with
  `@import "tailwindcss";`. Dev boots clean, `/` returns 200.
- **Why it's open:** the implementation plan's Task 2.3 still describes
  v3 setup (`tailwind.config.ts`, @nuxtjs/tailwindcss, `tailwind.config`
  export, JS theme tokens). When we reach Task 2.3, we need to
  reformulate the steps:
  - Replace `tailwind.config.ts` creation with Tailwind v4 `@theme`
    block inside `main.css` (CSS-first tokens).
  - Use `@import "tailwindcss";` (already in the stub).
  - Location CSS vars (`[data-location="..."]`) move under `@layer base`
    in the same file.
  - No separate Tailwind JS config unless we explicitly need a `@config
    "./tailwind.config.js";` directive (not required for our tokens).
- **Impact:** medium. The current `main.css` is a single-line stub. Task
  2.3 must produce the full theme/tokens file. If we follow the plan
  verbatim we'll re-introduce the v3 conflict.
- **Resolution trigger:** Task 2.3 execution — update plan pre-flight,
  then execute the v4-shaped version.
- **Close when:** Task 2.3 lands with a `main.css` that includes all TDC
  theme tokens + all 10 location CSS var blocks, dev server boots,
  build succeeds, and no `tailwind.config.ts` exists at project root.
- **Closed:** 2026-04-23 · commit a9d20d2 (Task 2.3) — main.css
  rewritten with Tailwind v4 CSS-first config: @import "tailwindcss";
  + @theme block with color/font tokens indirected through CSS vars;
  + @layer base with :root defaults and 8 per-location blocks grouped by mood
  (Cosmic/Tech, Hybrid, Warm/Intimate). No `tailwind.config.ts` created.
  Dev server boots cleanly; CSS served includes `--tdc-color-primary`.

### 🟢 TD-010 · Root-level `package.json` + `package-lock.json` — purpose undetermined

- **Source:** discovered during Phase 2 end-of-phase working-tree audit (2026-04-24).
- **Issue:** `/data1/tdcweb-dev/package.json` (55 bytes) and
  `/data1/tdcweb-dev/package-lock.json` (~37 KB), plus a ~14 MB
  `node_modules/`, existed at the repo root — all created 2026-01-11,
  untracked, never committed. Single `"eslint": "^9.39.2"` devDep with
  full transitive tree (69 top-level packages). NO eslint config file
  anywhere at root (no `.eslintrc*`, no `eslint.config.*`). No script,
  CI workflow, git hook, or source file referenced them.
- **Why it was open:** a previous session had run `npm install
  --save-dev eslint` at the repo root intending to set up monorepo-wide
  linting, but never followed through with config, scripts, or
  integration. Orphan install, idle for ~3.5 months.
- **Impact:** low — functionally nothing; cosmetic `git status` noise
  + 14 MB dead disk usage.
- **Resolution trigger:** Phase 2 end-of-phase audit forced the decision.
- **Close when:** the 3 items are removed OR deliberately committed
  with a documented purpose.
- **Closed:** 2026-04-24 · commit a9d20d2 (Phase 2 end-of-phase
  audit) — `package.json`, `package-lock.json`, and `node_modules/` at
  repo root were deleted. `frontend/` keeps its own lint setup;
  `backend/` will use Python linters (ruff/flake8). A future repo-wide
  lint policy, if decided, will be introduced deliberately with
  scripts + CI + docs, not as an orphan install.

---

## Template for new entries

```markdown
### 🔴/🟡/🟢 TD-NNN · Short title

- **Source:** Phase X Task Y.Z (commit SHA, YYYY-MM-DD)
- **Issue:** What's wrong or incomplete, factually.
- **Why it's open:** Why we didn't fix it immediately.
- **Impact:** Concrete consequence (correctness / ergonomics / perf / docs).
- **Resolution trigger:** Specific condition that makes this fixable.
- **Close when:** Testable criterion for closure.
```
