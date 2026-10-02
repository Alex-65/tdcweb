# User Intent Scan — Phase 2 (2026-04-24)

**Reviewer:** controller (main Claude)
**Trigger:** CLAUDE.md rule 19 / rule 16 step (a0)
**Scope:** entire session conversation from project kickoff through end of Phase 2 implementation
**Purpose:** capture user decisions / requests / scope changes made in conversation that must be codified in the plan or deferred, BEFORE the phase-end review runs.

This is a retroactive scan: rule 19 did not yet exist during Phase 2 execution. The gap that motivated rule 19 (`pdp-v3.md` missing from the phase-end commit) was caught by the user during the commit-proposal step (G), and corrected in the same phase's atomic commit.

---

## Scan table — user decisions vs codification

| # | User decision / request (conversation) | Where codified | Status at commit |
|---|---|---|---|
| 1 | Keep Vue, pivot to Nuxt for SSR / ISR / SEO | `spec §1-2`, `pdp-v3.md §2.2` | ✅ codified |
| 2 | Scope B — full architectural redesign (vs minimal migration) | `spec` (entire document) | ✅ codified |
| 3 | TypeScript strict throughout | `frontend/nuxt.config.ts` (`typescript.strict: true`), `pdp-v3.md §2.2` | ✅ codified |
| 4 | Architecture option C — Hybrid BFF (auth-only server routes) | `spec §8`, `server/middleware/auth-forward.ts`, `server/utils/flask-client.ts`, `server/utils/cookies.ts` | ✅ codified |
| 5 | Rendering strategy: events ISR 5 min, blog ISR + on-demand revalidate, dashboard SPA | `frontend/nuxt.config.ts` routeRules, `pdp-v3.md §4` | ✅ codified |
| 6 | Non-standard ports (Flask 9502/9500, Nuxt 9503/9501) | `frontend/.env`, `frontend/.env.example`, `nuxt.config.ts`, `CLAUDE.md § Project Constants`, `pdp-v3.md §2.6` | ✅ codified |
| 7 | Use `superpowers:brainstorming` formal flow | Spec + plan documents produced by brainstorming skill | ✅ executed |
| 8 | Create `docs/plans/pdp-v3.md`, keep `pdp-v2.md` as historical | `docs/plans/pdp-v3.md` | ✅ codified (caught late in this phase, corrected in this commit) |
| 9 | `docs/TECH_DEBT.md` with fix-now philosophy + sunset clause | `docs/TECH_DEBT.md`, `CLAUDE.md rule 18` | ✅ codified |
| 10 | Per-task test + per-phase triple review + stop-after-every-task | `CLAUDE.md rules 15–17` | ✅ codified |
| 11 | Policy (B) phase-end commit cadence, no per-task commits by subagents | `CLAUDE.md rules 15–16` (rewritten) | ✅ codified |
| 12 | Port the three BCWEB Review Guardians and adapt to TDC | `.claude/agents/tdc-code-reviewer.md`, `.claude/agents/tdc-design-enforcer.md`, `.claude/agents/tdc-design-system-enforcer.md` (commit `50824fb`) | ✅ codified |
| 13 | Rewrite `tdc-documentation-expert` for Nuxt 4 stack | `.claude/agents/tdc-documentation-expert.md` (commit `fefe316`) | ✅ codified |
| 14 | Rewrite `tdc-frontend-expert` for Nuxt 4 stack | `.claude/agents/tdc-frontend-expert.md` (commit `3b6aa99`) | ✅ codified |
| 15 | Explicit per-phase checkpoint format (spec review + code review + design-system as separate lines, not bundled) | `~/.claude/projects/.../memory/feedback_review_checkpoint_format.md` | ✅ codified in memory |
| 16 | Use native TDC subagent types (not `general-purpose` fallback) | Applied from Task 2.6 onwards (tdc-frontend-expert, tdc-auth-expert, tdc-code-reviewer native dispatch) | ✅ applied |
| 17 | `/reload-plugins` completed — new review guardians are dispatchable | Task 2.6 onwards | ✅ applied |
| 18 | `@studio-freight/lenis` → `lenis` package rename | Updated across living docs, `package.json`, plugin import (commit `fefe316` era and Task 1.4 fix) | ✅ codified (TD-004 tracks legacy skill references) |
| 19 | Tailwind v4 CSS-first (after v3/v4 conflict discovery) | `frontend/app/assets/css/main.css`, `nuxt.config.ts` vite plugin (TD-006 closed) | ✅ codified |

---

## Items deferred (with explicit rationale)

None new from this scan. All open TECH_DEBT items (TD-003, TD-004, TD-005, TD-007, TD-008, TD-009) are either upstream-gated or scheduled for a specific future phase with a concrete resolution trigger.

---

## Gaps caught

**One**: `docs/plans/pdp-v3.md` was scheduled in the original plan for Phase 5 (`plan §Phase 5 Task 5.2`). The user had expressed in conversation that it should exist as "the current plan" (with pdp-v2 historical). This decision was followed in strategy (the doc's eventual shape was locked) but not pulled forward in scheduling — the plan still said Phase 5.

The phase-end `tdc-code-reviewer` dispatch correctly evaluated Phase 2 against the plan's Phase 2 deliverables and found nothing missing. The `tdc-documentation-expert` dispatch received an explicit "don't create pdp-v3 — scheduled for Phase 5" instruction and obeyed, only flagging the forward-reference (`pdp-v3.md (future)` in README / CLAUDE.md) without acting on it.

**User caught the gap during the commit proposal (step G).** Resolution: pdp-v3.md authored in the same phase boundary, forward-references in CLAUDE.md / README / 2 agent files updated to current state, plan's Phase 5 Task 5.2 effectively satisfied early.

**Rule 19 exists because of this gap** — to prevent reviewer scope from being the sole safety net for user-intent drift.

---

## Recommendation for future phases

- Every phase opens with a mini user-intent-scan of the since-last-phase conversation window, producing this same table.
- Every phase closes (step a0) with a re-scan to catch anything that changed during implementation.
- Reviewer prompts include the scan artifact path so reviewers can cross-check.
