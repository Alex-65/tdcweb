# Phase 3 — Documentation Sync Review

**Reviewer:** `tdc-documentation-expert`
**Timestamp:** 2026-04-24
**Last doc-sync commit:** `218f9d8` (Phase 2 docs-sync with `<phase-2-commit>` placeholder cleanup)
**Phase:** 3 — Nuxt 4 frontend port (pages, components, composables, Pinia stores, i18n content)

## Scope analyzed

- Commits analyzed: none new since `218f9d8`; entire Phase 3 lives in the working tree per CLAUDE.md rule 15 (no per-task commits).
- Files changed vs `HEAD`: 20 total. 12 modified tracked files + 8 untracked trees (`docs/reviews/2026-04-24-user-intent-scan-phase-3.md`, `frontend/app/components/`, `frontend/app/composables/`, `frontend/app/error.vue`, `frontend/app/layouts/`, `frontend/app/pages/`, `frontend/app/stores/`, `frontend/tests/unit/useApi.test.ts`).
- Phase-3 execution artifact: `docs/reviews/2026-04-24-user-intent-scan-phase-3.md` (rows 1-46, sections A/B/C). Used as the authoritative spine for this sync.

## Impact-matrix coverage

| Code change | Docs updated |
|---|---|
| `frontend/server/utils/flask-client.ts` rewritten (Task 3.0, resilient pattern) | TECH_DEBT (TD-009 closed) · CHANGELOG (Phase 3 entry Changed/Fixed) · plan (new Task 3.0 section) |
| `frontend/tests/unit/flask-client.test.ts` +5 assertions | CHANGELOG (Tests section) · TD-009 close-when note |
| `frontend/app/app.vue` favicon fix | CHANGELOG · plan Task 3.1 amendment (favicon.svg → favicon.ico) |
| `frontend/app/layouts/default.vue` (new) | CHANGELOG · README project structure · plan Task 3.2 verification |
| `frontend/app/error.vue` (new, role="alert" + <main> + i18n) | CHANGELOG · plan Task 3.2 snippet amendment |
| `frontend/app/components/common/AppHeader.vue` (new, outline login + active-class font-bold + focus-visible) | CHANGELOG · plan Task 3.3 AppHeader snippet amendment · README |
| `frontend/app/components/common/AppFooter.vue` (new, year hoisted + motto via $t) | CHANGELOG · plan Task 3.3 AppFooter snippet amendment · playbook §7 SSR mentioned implicitly |
| `frontend/app/pages/index.vue` (new, scrim + i18n SEO + text-2xl) | CHANGELOG · plan Task 3.5 snippet amendment |
| `frontend/app/pages/locations/index.vue` (new, 3-state + localePath + role="alert") | CHANGELOG · plan Task 3.6 snippet amendment · playbook §23.1 pattern library |
| `frontend/app/pages/events/index.vue` (new, preemptive-polish) | CHANGELOG · plan Task 3.7 snippet amendment · playbook §23.1 |
| `frontend/app/composables/useApi.ts` (new, Parameters<typeof $fetch>[1] derivation + useApi() recursion) | CHANGELOG · spec §8.4 amendment · plan Task 3.8 snippet amendment · playbook §5.7 rewritten |
| `frontend/app/composables/useScrollAnimation.ts` (new, reduced-motion guard) | CHANGELOG · plan Task 3.10 amendment · playbook §§8.2, 9 |
| `frontend/app/composables/useSmoothScroll.ts` (new, reduced-motion guard) | CHANGELOG · plan Task 3.11 amendment · playbook §9.2 |
| `frontend/app/composables/useLocationTheme.ts` (new) | CHANGELOG · plan Task 3.11 amendment · playbook §14.3 already correct |
| `frontend/app/stores/{auth,locale,ui}.ts` (new) | CHANGELOG · plan Task 3.9 amendment (JSDoc @warning on pushNotification) · playbook §10.6 (new) · tdc-frontend-expert forbidden-patterns table |
| `frontend/app/assets/css/main.css` `--color-error` token added | CHANGELOG · playbook §14.2 + §14.5 (new) · TECH_DEBT TD-013 (new) · tdc-frontend-expert LOCATION THEMING block |
| `frontend/app/plugins/lenis.client.ts` reduced-motion short-circuit | CHANGELOG · spec §9.2 amendment · playbook §9.1 amendment |
| `frontend/nuxt.config.ts` `components.pathPrefix: false` + i18n `lazy: true` removal | CHANGELOG · plan (amendment embedded in Task 3.3 rationale) |
| `frontend/i18n/locales/{en,it,fr,es}.json` 36 new translations | CHANGELOG · plan Task 3.4 amendment |
| `frontend/tests/unit/useApi.test.ts` (new, 4 TDD tests) | CHANGELOG · plan Task 3.8 Step 1 already correct |

## Files updated

- `CLAUDE.md` — header "Last Updated" bumped to 2026-04-24 (Phase 3). Rules 10/31 elevations (triple review after every task, controller micro-edit threshold) left out of CLAUDE.md per scan row 10 + brief instruction — flagged in the report for user decision, not unilaterally codified.
- `README.md` — frontend project-structure updated to reflect Phase 3 working tree (pages, layouts, components, composables, stores). Features list updated with Phase 3 deliverables + Phase 4+ moved-to-future items.
- `CHANGELOG.md` — new Phase 3 entry at top, covers Added (pages, components, composables, stores, i18n), Changed (main.css, app.vue, lenis plugin, nuxt.config.ts), Fixed (flat component naming, AppFooter SSR year, nav collision, error role="alert"), Security, Infrastructure (prod build + SSR bundle audit), Verification (21 tests + 11 E2E), Deferred/Open (TD-011/12/13). Phase 2 entry's `<phase-2-commit>` placeholder replaced with `a9d20d2`/`218f9d8`. Unreleased.Planned block pruned/re-phased.
- `docs/TECH_DEBT.md` — TD-009 closed (moved to "Closed items" with Phase 3 commit placeholder). TD-007 header repaired (line was missing entirely — "Design-system consolidation" was orphaned as a bare bullet). TD-011 annotated with Phase 3 close state. TD-012 opened (`useFormattedDate` SSR-safe composable). TD-013 opened (`livemagic` vs `--color-error` collision). Unicode arrows normalized to ASCII where the surrounding section used ASCII.
- `docs/frontend/nuxt-playbook.md` — TOC extended with §23. §5.7 `useApi` snippet rewritten to match the final implementation (derived type, recursive `useApi()`, return annotation) with 4-point design-notes appendix. §8.2 `useScrollAnimation` reference code gained the reduced-motion guard. §9.1 Lenis plugin gained the reduced-motion short-circuit + 3-layer discipline callout. §9.2 `useSmoothScroll` gained the reduced-motion guard. §10.6 new subsection on store SSR caveats (`pushNotification` example). §14.2 `main.css` snippet gained `--color-error` token and the `--tdc-color-error: #ef4444` `:root` entry. §14.5 new subsection "Semantic-state tokens" with the 7-utility table and the "add-then-reuse" pattern. §14 "Known palette issues" subsection noting TD-011 and TD-013. §23 new: Pattern library (preemptive-polish 7-point checklist, `role="alert"` standardization, controller micro-edit threshold, plan-authoring cross-task consistency, `useFormattedDate` deferred note).
- `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md` — §8.4 `useApi` snippet rewritten to final shape with 3-point "Phase 3 clarifications" appendix covering the typed marker, the recursive wrapper re-entry, and the explicit return annotation. §9.2 Lenis gained a Phase 3 addition paragraph on `prefers-reduced-motion`.
- `docs/superpowers/plans/2026-04-23-nuxt-integration.md` — Phase 3 preamble note on deferred commits added. Task 3.0 (new, TD-009 preemptive rewrite) inserted as the first Phase 3 task. Tasks 3.1-3.11 snippets amended to the final working-tree shape. Every `### Step: Commit` block with verbatim git command replaced by "Commit deferred — CLAUDE.md rule 15" note.
- `docs/plans/pdp-v3.md` — phase status table updated: Phase 2 SHA `a9d20d2`, Phase 3 marked Complete (this commit), Phase 4 marked Next. New subsection "Phase 3 highlights (2026-04-24)" with a compact summary of deliverables + TD deltas + phase-3-specific learnings.
- `.claude/agents/tdc-frontend-expert.md` — `text-red-400` in the vee-validate form snippet replaced with `text-error` (semantic-token alignment). FORBIDDEN PATTERNS table extended with 7 new rows covering Phase 3 patterns (raw hex, `text-red-*`, missing `role="alert"`, missing `useLocalePath` on dynamic paths, `pushNotification` SSR, missing reduced-motion guard, missing preemptive-polish checklist). LOCATION THEMING block rewritten to 10+ wording, semantic-token callout, and TD-011/TD-013 warnings.

## Files created

- `docs/reviews/2026-04-24-tdc-documentation-expert-phase-3-sync.md` — this file.

## Files NOT updated (controller review)

- `docs/api/` — no Phase 3 API surface change (all pages use public Flask `/api/locations` and `/api/events` which pre-date Phase 3; no new API docs needed).
- `docs/backend/architecture.md` — Phase 3 touched zero backend files.
- `docs/database/` — Phase 3 touched zero DB schema.
- `docs/deployment/development.md` — no new env var or dev-workflow change in Phase 3.
- `docs/deployment/production.md` — does not exist yet; Phase 6 will create it.
- `docs/DESIGN.md` — does not exist yet; TD-007 defers creation to end of Phase 4.
- `docs/i18n/translations.md` — exists but Phase 3 only added locale JSON keys (already documented conceptually; no workflow change).
- Other `.claude/agents/*.md` — none reference Phase-3-specific content requiring updates beyond what was already done. The 27-agent inventory is unchanged.
- `.claude/skills/tdc-frontend/SKILL.md` and `.claude/skills/tdc-testing/SKILL.md` — TD-004 already defers these to Phase 5 rewrite. Leaving them alone per the open TD.

## CLAUDE.md drift NOT corrected unilaterally (controller decision requested)

Scan rows 10 and 31 surfaced two process elevations that the controller applied during Phase 3 but the scan authors explicitly left as phase-scoped. Not corrected by this agent — flagged for decision:

1. **Rule 10 elevation** (triple review after EVERY task, even non-UI). Currently applied as a phase-3 convention. If this should become a durable amendment to CLAUDE.md rule 15, the user must say so — in which case rule 15(d) changes from "if the task modified UI, ALSO dispatch `tdc-design-system-enforcer`" to "dispatch `tdc-design-system-enforcer` for every task (typically returns [N/A] when no UI surface was touched)".
2. **Rule 31 codification** (controller micro-edit threshold: ≤3 lines AND zero new behavior OR wraps existing). Codified in playbook §23.3 as frontend-domain guidance. Whether this should also appear as a rule or guidance in CLAUDE.md (governance-layer) is a controller/user call, not a docs-sync-agent call.

Both items are explicitly documented in the scan and in the playbook; they do NOT drift in the sense of "docs say one thing, reality does another" — they are unwritten convention that the user may want to cement.

## TD entries delta

- **TD-009** — closed. Resolving SHA `<phase-3-commit>` placeholder ready for controller to replace post-commit.
- **TD-011** — still open, no change beyond an inline "Current state (Phase 3 close)" note confirming no jazzclub route yet.
- **TD-012** — new. `useFormattedDate` SSR-safe composable for locale-aware date rendering. Trigger: first Phase 4+ page needing user-friendly date strings.
- **TD-013** — new. `livemagic` primary (`#ef4444`) identical to global `--color-error` (`#ef4444`). Trigger: first Phase 4+ livemagic-themed page with both a primary CTA and an error state.
- **TD-007** — header was missing from the file (rendered as a bare bullet without a heading). Repaired as part of the sync.

## Suggested phase-end commit message

```
feat(frontend): Phase 3 — Nuxt 4 frontend port (pages, components, composables, stores, i18n)

Port the surviving public-facing Vue surface from frontend.vue-backup/ onto
the Nuxt 4 runtime laid down in Phase 2. End state: dev-booting + prod-building
public site, SSR-rendered across EN/IT/FR/ES, 21/21 vitest + 11/11 Playwright
E2E at 1920x1080, SSR bundle audit clean (gsap/lenis absent from server chunks).

12 main tasks (3.0 through 3.11) + 4 polish sub-tasks (3.2b, 3.3b, 3.5b, 3.6b)
+ 2 typecheck-batch fix passes (HIGH F1-F4, MED F5-F7) + 5 controller-level
phase-end micro-edits. All via CLAUDE.md rule 15 per-task loop with phase-end
rule 16 triple review + real tests + state cleanup + docs sync in this single
atomic commit.

Deliverables
- Public pages: home (SSG), locations (SSG), events (ISR swr=300) — three-state
  templates, i18n-bound SEO, semantic error tokens, focus-visible rings,
  role="alert" on error branches, useLocalePath on internal links
- Components: layouts/default, error.vue, common/AppHeader (outline login +
  active-class font-bold differentiation), common/AppFooter (year hoisted to
  script-setup per SSR Rule #4, motto via $t('home.hero_title'))
- Composables: useApi (typed retry marker via NonNullable<Parameters<typeof
  $fetch>[1]>, recursive useApi() retry per spec §8.4), useScrollAnimation
  + useSmoothScroll (reduced-motion guards), useLocationTheme (SSR-safe body
  attr via useHead)
- Pinia stores: auth / locale / ui (ui.pushNotification flagged SSR-unsafe
  via JSDoc @warning — uses crypto.randomUUID)
- i18n: 9 namespaces × 4 locales = 36 translations (nav / home / home.seo /
  locations / events / errors)
- Semantic token: --color-error added to @theme + :root (palette-agnostic)
- Config: components.pathPrefix=false (flat <AppHeader /> naming), i18n
  lazy: true removed (@nuxtjs/i18n v9+ auto-lazies)

Tech debt
- TD-009 closed: flask-client.ts rewritten with resilient stub-first + ofetch
  fallback pattern (Task 3.0, preemptive — scan row 5/11)
- TD-011 still open: jazzclub chrome contrast regression on outline login
  (no jazzclub page in Phase 3, deferred to first jazzclub route)
- TD-012 opened: useFormattedDate SSR-safe composable needed for Phase 4+
- TD-013 opened: livemagic primary (#ef4444) collides with --color-error
  (#ef4444) — resolution deferred to first livemagic route

Verification
- nuxi typecheck: 0 errors
- npm test: 21/21 (flask-client ×8, auth-forward ×3, cookies ×9, useApi ×4
  + 1 test-utils harness assertion)
- npm run build + node .output/server/index.mjs: prod boot clean
- Playwright E2E: 11/11 PASS at 1920x1080 (home/locations/events × 4 locales
  + error page)
- SSR bundle audit: `grep -r "gsap\|lenis" frontend/.output/server/` returns
  zero runtime imports

Spec:  docs/superpowers/specs/2026-04-23-nuxt-integration-design.md
Plan:  docs/superpowers/plans/2026-04-23-nuxt-integration.md
Scan:  docs/reviews/2026-04-24-user-intent-scan-phase-3.md
Sync:  docs/reviews/2026-04-24-tdc-documentation-expert-phase-3-sync.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

## Suggested staging

```
git add \
  frontend/app/app.vue \
  frontend/app/error.vue \
  frontend/app/layouts/ \
  frontend/app/pages/ \
  frontend/app/components/ \
  frontend/app/composables/ \
  frontend/app/stores/ \
  frontend/app/assets/css/main.css \
  frontend/app/plugins/lenis.client.ts \
  frontend/nuxt.config.ts \
  frontend/server/utils/flask-client.ts \
  frontend/i18n/locales/ \
  frontend/tests/unit/useApi.test.ts \
  frontend/tests/unit/flask-client.test.ts \
  CLAUDE.md \
  README.md \
  CHANGELOG.md \
  docs/TECH_DEBT.md \
  docs/plans/pdp-v3.md \
  docs/superpowers/plans/2026-04-23-nuxt-integration.md \
  docs/superpowers/specs/2026-04-23-nuxt-integration-design.md \
  docs/frontend/nuxt-playbook.md \
  docs/reviews/2026-04-24-user-intent-scan-phase-3.md \
  docs/reviews/2026-04-24-tdc-documentation-expert-phase-3-sync.md \
  .claude/agents/tdc-frontend-expert.md
```

Code + docs staged together per CLAUDE.md rule 16 — atomic single commit.

## Validation checklist for controller before commit

- [ ] `cd frontend && npx nuxi typecheck` returns 0 errors
- [ ] `cd frontend && npm test` returns 21/21 passing
- [ ] `git status --short` shows exactly the files listed above (no surprise residue)
- [ ] Commit message matches the proposal (multi-line, references spec/plan/scan/sync)
- [ ] TD-009 close-when SHA placeholder `<phase-3-commit>` flagged for post-commit patch (same pattern as Phase 2's `<phase-2-commit>` cleanup in commit `218f9d8`)
- [ ] Phase 2 CHANGELOG placeholder replaced — verify `grep -n "<phase-2-commit>" CHANGELOG.md` returns nothing
- [ ] Controller decision captured (in reply to user, not in docs) on CLAUDE.md rule 15 elevation question (scan row 10) and rule 31 codification question (scan row 31)
- [ ] Push deferred until user authorization (no auto-push per CLAUDE.md § Hard rules)
