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

### 🟢 TD-004 · Legacy `@studio-freight/lenis` references in 3 files

- **Source:** Task 1.4 (commit 2091253, 2026-04-23)
- **Issue:** The Lenis package was renamed from `@studio-freight/lenis`
  to `lenis`. We updated `CLAUDE.md`, the spec, the plan, and the
  playbook. Three non-authoritative files still reference the old name:
  - `docs/plans/pdp-v2.md` (historical document — intentionally not
    updated per "v2 stays as historical reference")
  - `.claude/skills/tdc-frontend/SKILL.md` (old Vue+Vite skill,
    scheduled for full rewrite in Phase 5)
  - `.claude/skills/tdc-testing/SKILL.md` (testing skill, scheduled for
    review in Phase 5)
- **Why it's open:** `pdp-v2.md` is historical by design (do not edit);
  the two skill files are scheduled for a broader rewrite that will
  naturally incorporate the fix.
- **Impact:** low. These files are not consumed by subagents during
  Phase 1-4 implementation. Cosmetic/doc-accuracy only.
- **Resolution trigger:** Phase 5 skill rewrite. `pdp-v2.md` stays as
  historical (intentional — close as WONTFIX once Phase 5 completes).
- **Close when:** `grep -rn '@studio-freight/lenis'
  .claude/skills/` returns nothing.

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

---

### 🟡 TD-007 · Consolidated `docs/DESIGN.md` missing

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
