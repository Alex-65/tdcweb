# CLAUDE.md

## 🔴 NEVER IGNORE - CORE RULES (ALWAYS ACTIVE)
1. **DEBUG FIRST, CODE NEVER** → Add console.log/logger debug EVERYWHERE before any fix. Read logs. Understand problem with PROOF. Only then fix. ZERO trial-and-error.
2. **MUST use subagents for complex work** (2+ files = expert, unclear = problem-isolator)
3. **Domain experts mandatory**: Database→database-expert, Vue→frontend-expert, Flask→backend-expert
4. **Problem unclear?** → problem-isolator FIRST, never guess or explore alone
5. **PREFER EXPERT DIRETTI over orchestrator** → Use specific domain experts directly for transparency. Orchestrator only for 10+ parallel agents or complex decision trees. Multi-phase sequential workflows = call experts directly, one per phase.
6. **Zero superficiality** → Complete understanding BEFORE any modification
7. **File size limits**: NEW files must respect limits (.vue ≤500, .py ≤1000, .ts ≤800), existing large files = do NOT refactor unless absolutely necessary
8. **Fix-Test-Verify**: Find bug → Apply fix → TEST IMMEDIATELY → Only continue if problem persists
9. **ABSOLUTELY FORBIDDEN: Batch file modifications** → NEVER use scripts or batch commands to modify multiple files. Each file modification MUST be done individually, manually, with explicit user visibility
10. **TEST BEFORE DECLARING DONE** → NEVER say a modification is complete without running tests that prove it works
11. **EXPLICIT CHANGE IMPACT REPORT** → For EVERY modification, state: (a) exact files/lines changed, (b) what could break, (c) what was tested
12. **ID ORDERING GOLDEN RULE** → When ordering by database ID: (1) SELECT include `id` field, (2) SQL `ORDER BY id`, (3) Pass numeric ID in JSON, (4) Frontend `.sort((a,b) => a.id - b.id)`. NEVER rely on Object.entries() order or parseInt() tricks
13. **BROWSER TESTING: Playwright MCP** → Use `mcp__plugin_playwright_playwright__*` tools for browser testing, screenshots, and UI validation
14. **BROWSER RESOLUTION: 1920x1080 ALWAYS** → Set desktop resolution 1920x1080 before any browser test
15. **SUBAGENT TASK WORKFLOW (no-commit model)** → After EACH subagent task: (a) run ALL tests (backend pytest + frontend vitest + integration where relevant); (b) CREATE missing tests for the code just produced (both backend and frontend sides); (c) dispatch **`tdc-code-reviewer`** for spec + code quality review; (d) if the task modified UI, ALSO dispatch **`tdc-design-system-enforcer`** for visual compliance; (e) report results; (f) **STOP and wait for user checkpoint** before dispatching next task. **NO COMMITS at task level** — code accumulates in the working tree until phase end (rule 16). Implementer subagents must NOT commit; controller handles commits at phase boundary. This aligns with the user's practice of committing only when documentation is simultaneously updated.
16. **PHASE-END COMMIT PROTOCOL** → At the end of EACH phase, in order: (a) **triple review** — dispatch `tdc-code-reviewer` (Phase 1 spec compliance + Phase 2 code quality) and `tdc-design-system-enforcer` (for UI changes); (b) **real tests** (E2E, integration, performance — not only smoke tests); (c) **state cleanup** — if tests dirtied DB/filesystem/external services, restore; (d) **dispatch `tdc-documentation-expert`** to analyze the phase's git diff and update ALL impacted docs (CLAUDE.md, TECH_DEBT, playbook, specs, plans, API refs, CHANGELOG, agent inventories, etc. — creating missing docs where needed); (e) **atomic commit(s)** — code + docs committed together in one or a few logically-grouped commits, never docs-only commits. **Pre-implementation counterpart:** `tdc-design-enforcer` blocks any phase/task from starting without an approved spec under `docs/superpowers/specs/`.
17. **TEST STATE CLEANUP** → Any test that mutates persistent state (DB rows, files, external API objects) MUST restore the pre-test state upon completion. No test residue allowed between runs. If a test crashes mid-run, the next step is always: clean up first, then investigate.
18. **TECH DEBT REGISTER** → `docs/TECH_DEBT.md` is the single source of truth for items that can't be fixed immediately. **Fix-now-if-possible is the default** — this file is a last resort, not a buffer. Every entry has: source (phase/task/commit), issue, why-it's-open, impact, **resolution trigger** (specific condition), and close-when criterion. Review at phase start AND during phase-end triple review (rule 16). Items sitting open for 3+ phases without their trigger firing get re-evaluated (escalate-to-fix or WONTFIX with explicit reasoning). Never let this file become a dumping ground.

---

Essential guidance for Claude Code when working with The Dreamer's Cave website project.

**Project:** tdcweb - The Dreamer's Cave Virtual Music Club Website
**Domain:** thedreamerscave.club
**Motto:** "You Can See The Music"
**Last Updated**: January 2025

## 🚨 CRITICAL DEVELOPMENT PRINCIPLES

**🔴 ZERO SUPERFICIALITY - TOTAL UNDERSTANDING MANDATORY**

**RIGOROUS METHODOLOGY:**
1. **FIRST**: Complete system understanding
   - Use `tdc-problem-isolator` for complex or unknown problems
   - Read all necessary code extensively (Read/Grep/Glob)
   - Trace complete data flow and dependencies
   - Verify with SQL queries/direct code, never assume
   - Identify precise problem and root cause

2. **ONLY THEN**: Correct implementation
   - Once only, with full understanding
   - Based on complete comprehension, never on guesswork
   - Cross-validate between multiple sources (DB, code, API)

**⛔ ABSOLUTELY FORBIDDEN:**
- Random modifications hoping they work
- Implementing "probable solutions" or trial-and-error
- Skipping analysis to go straight to implementation
- Trusting documentation over actual code reality
- Creating or running scripts that modify multiple files at once

**IRON RULE**: *"Probably works" doesn't exist. Either you understand everything or you touch nothing.*

## 🔴 DEBUG-FIRST METHODOLOGY - ABSOLUTE RULE

**NEVER write code without seeing the problem in logs FIRST**

### Mandatory Debug Process:
1. **ADD DEBUG MESSAGES**:
   - Frontend: `console.log('[ComponentName] action:', data)` in EVERY function
   - Backend: `logger.info(f"[endpoint] data: {data}")` in EVERY endpoint
   - Show: current state, parameters received, API responses, state updates

2. **REPRODUCE THE PROBLEM**:
   - Execute the failing action
   - Read the console/logs output
   - Identify EXACTLY where it fails with PROOF from logs

3. **UNDERSTAND WITH EVIDENCE**:
   - What values are actually being passed? (not what you think)
   - What does the API actually return? (not what you assume)
   - What is the actual state? (not what should be)

4. **ONLY THEN FIX**:
   - Write targeted fix based on evidence
   - Keep debug messages until confirmed working
   - Remove debug only after user confirms fix

### ⛔ ABSOLUTELY FORBIDDEN:
- "Let me try this fix" without debug output
- "This should work" based on code reading alone
- Making ANY change before seeing logs prove the problem
- Guessing what's wrong instead of measuring
- Trial-and-error hoping something sticks

**IRON RULE**: *If you haven't seen debug output proving what's wrong, you don't know what's wrong. PERIOD.*

## 📋 SUBAGENT-DRIVEN IMPLEMENTATION WORKFLOW - MANDATORY

**🔴 When implementing any plan in subagent-driven mode, this is the non-negotiable protocol.**

### Per-task loop (no commits)

```
┌──────────────────────────────────────────────────────────────────┐
│  1. DISPATCH subagent for the next task in the plan             │
│     └─ pass: task spec + relevant context files                  │
│     └─ explicit instruction: DO NOT commit                       │
│                                                                  │
│  2. Subagent EXECUTES the task                                   │
│     └─ produces code + tests per the task's step list            │
│     └─ does NOT run `git commit`                                 │
│                                                                  │
│  3. RUN ALL TESTS                                                │
│     ├─ Backend:  pytest (all markers, respecting fixtures)      │
│     ├─ Frontend: npm test (vitest, all spec files)              │
│     └─ Integration: if the task touches a boundary              │
│                                                                  │
│  4. CREATE MISSING TESTS                                         │
│     ├─ For any new code lacking tests (backend & frontend)      │
│     ├─ Unit tests for pure logic                                 │
│     ├─ Integration tests for cross-layer code                    │
│                                                                  │
│  5. DISPATCH tdc-code-reviewer (and tdc-design-system-enforcer   │
│     if UI changes). Fix issues before proceeding.                │
│                                                                  │
│  6. CHECKPOINT                                                   │
│     ├─ Report: what was done, tests run, tests created, diffs,  │
│     │         review verdicts                                    │
│     └─ STOP — wait for user approval to proceed to next task    │
│                                                                  │
│  Code remains uncommitted in the working tree. Commits happen   │
│  only at phase end (rule 16).                                    │
└──────────────────────────────────────────────────────────────────┘
```

### Per-phase commit protocol (at the end of every phase)

```
┌──────────────────────────────────────────────────────────────────┐
│  A. SPEC + CODE REVIEW (via tdc-code-reviewer, 2 phases)         │
│     ├─ Phase 1: spec compliance across the whole phase           │
│     └─ Phase 2: code quality / security / conventions /          │
│        verification evidence                                     │
│                                                                  │
│  B. DESIGN-SYSTEM REVIEW (via tdc-design-system-enforcer)        │
│     └─ Visual compliance for UI changes in this phase            │
│        (dark theme, location CSS vars, Tailwind tokens, GSAP     │
│        discipline, typography, spacing)                          │
│                                                                  │
│  C. REAL TESTS (not just smoke tests)                            │
│     ├─ Full E2E journeys (Playwright, 1920x1080)                 │
│     ├─ Integration tests (cross-service)                         │
│     ├─ Performance sanity (LCP, bundle size, query timing)       │
│     └─ Security smoke: auth boundaries, cookie flags, CSP        │
│                                                                  │
│  D. TEST STATE CLEANUP                                           │
│     ├─ Identify what tests wrote (DB rows, files, external)      │
│     ├─ Restore to pre-test state                                 │
│     └─ Verify cleanup with a query/listing                       │
│                                                                  │
│  E. DOCUMENTATION SYNC (via tdc-documentation-expert)            │
│     ├─ Analyze git diff for the phase                            │
│     ├─ Update EVERY impacted doc per the Impact Matrix           │
│     ├─ CREATE missing docs where needed                          │
│     ├─ Validate link integrity + stack-reference currency        │
│     └─ Return report (staging recommendation + commit message)   │
│                                                                  │
│  F. ATOMIC COMMIT(S)                                             │
│     ├─ Code + docs committed together                            │
│     ├─ One commit, or a small set of logically-grouped commits   │
│     ├─ NEVER docs-only or code-only commits at phase boundary    │
│     └─ Commit message references spec + plan + SHA range         │
│                                                                  │
│  G. PHASE CHECKPOINT                                             │
│     ├─ Report all reviews + real test results + cleanup +        │
│     │   docs sync + commit SHAs                                  │
│     └─ STOP — wait for user approval before next phase           │
│                                                                  │
│  Push to remote happens ONLY with explicit user authorization,   │
│  never automatically.                                            │
└──────────────────────────────────────────────────────────────────┘
```

### Hard rules

- **Never skip steps 3-5** of the per-task loop. Not even on "trivial" tasks. If a task seems too small for tests, the task was scoped wrong — split it.
- **Never skip the phase-end review + docs sync**. "The code looks fine" is not a substitute.
- **Tests come WITH the code**. They land in the same phase-end commit as the feature they cover. No "I'll write tests later".
- **DB/filesystem state after tests = DB/filesystem state before tests.** Always. This is enforced, not aspirational.
- **Docs land WITH code at phase end.** There are no docs-only commits at phase boundary. If docs drift during a phase, it's caught and corrected by `tdc-documentation-expert` before the phase commit.
- **No per-task commits.** Subagents produce code + tests in the working tree; the controller commits only at phase boundary. Aligns with the user's practice of committing only alongside documentation updates.
- **Push is always explicit.** `tdc-documentation-expert` and every other agent never push. Pushes happen only when the user explicitly authorizes each one.
- **Possible additional review post-phase**: the user may request an extra review at some point after the phase closes. Treat it as a normal ad-hoc deliverable when it comes.

---

## 🔴 FIX-TEST-VERIFY METHODOLOGY - ABSOLUTE RULE

**When debugging/fixing issues:**
1. **Find a bug** → Apply the fix
2. **TEST IMMEDIATELY** → Verify if it resolves the problem
3. **ONLY if problem persists** → Continue searching for other issues

**⛔ ABSOLUTELY FORBIDDEN:**
- Finding and fixing a bug, then continuing to search for more problems WITHOUT testing
- Making multiple changes before verifying if the first fix worked
- Risk breaking working code by searching for non-existent problems

**IRON RULE**: *One fix at a time. Test before proceeding. Never continue blindly after a fix.*

## 🔴 MANDATORY SUBAGENT USAGE - ZERO TOLERANCE

**Claude MUST PROACTIVELY use subagents - NO EXCEPTIONS**

### 🚨 MANDATORY TRIGGERS (MUST use subagent IMMEDIATELY):

**🔴 Claude MUST use `tdc-problem-isolator` for:**
- Any problem Claude doesn't immediately understand 100%
- Multi-component issues (frontend + backend + database)
- "Search/investigate/understand" requests
- Before any complex analysis or debugging

**🔴 Claude MUST use domain experts for:**
- **Database tasks** → `tdc-database-expert` (queries, schema, migrations)
- **Frontend work** → `tdc-frontend-expert` (Vue.js, TypeScript, components, GSAP)
- **Backend logic** → `tdc-backend-expert` (Flask, business logic, services)
- **API endpoints** → `tdc-api-expert` (REST, validation)
- **Authentication** → `tdc-auth-expert` (sessions, OAuth, JWT, RBAC)
- **Security analysis** → `tdc-security-expert` (vulnerabilities, OWASP)
- **Performance issues** → `tdc-performance-expert` (optimization, caching, GSAP performance)
- **Integrations** → `tdc-integration-expert` (Google Calendar, Facebook, Patreon, Second Life API)

**🔴 Claude MUST use coordinators for:**
- **Testing strategy** → `tdc-testing-expert` (plans testing approach)
- **Documentation updates** → `tdc-documentation-expert` (maintains docs)
- **Complex workflows** → `tdc-orchestrator` (3+ agents needed)

**🔴 Claude MUST use advisory system for:**
- **Difficult decisions** → Advisory agents (architecture, security, risk, performance)
- **Decision questions** → `tdc-advisory-coordinator`
- **Conflicting approaches** → Multiple advisory agents in parallel

### ⚖️ NON-NEGOTIABLE DECISION RULES:
- **2+ files to modify** → MUST use relevant expert
- **Don't know where to start** → MUST use `tdc-problem-isolator`
- **Multiple domains involved** → Call specific experts directly (NOT orchestrator)
- **Unsure about approach** → MUST use advisory system
- **"This is complex"** → STOP. MUST use subagent.

**ABSOLUTELY FORBIDDEN**: Doing complex work directly without consulting relevant experts first.

### 🎯 ORCHESTRATOR vs EXPERT DIRETTI - CRITICAL CHOICE

**🔴 LESSON LEARNED**: Expert diretti are ALWAYS better than orchestrator for transparency and control.

**WHEN TO USE EXPERT DIRETTI** (PREFERRED - 95% of cases):
- ✅ Multi-phase sequential workflows (FASE 1 → FASE 2 → FASE 3)
- ✅ Multiple domains (backend + frontend + database)
- ✅ Need to stop/test after each step
- ✅ User wants visibility on process
- ✅ Debugging is important

**Example** (CORRECT approach):
```
FASE 1: Task(tdc-backend-expert, "modify events service") → Test → Stop
FASE 2: Task(tdc-frontend-expert, "update EventCard component") → Test → Stop
FASE 3: Task(tdc-frontend-expert, "add GSAP animations") → Test → Stop
```

**WHY EXPERT DIRETTI ARE BETTER**:
- ✅ Complete transparency - see exactly what happens
- ✅ Easy debugging - know where/why failures occur
- ✅ Better control - stop/modify between phases
- ✅ Follows CLAUDE.md domain expert rules
- ✅ User sees the process, not just results

**WHEN TO USE ORCHESTRATOR** (RARE - 5% of cases):
- ⚠️ Only for 10+ agents running in PARALLEL
- ⚠️ Complex decision trees with conditional branching
- ⚠️ NOT for sequential multi-phase workflows
- ⚠️ NOT for "coordination" (you coordinate better directly)

**IRON RULE**: *When in doubt, use expert diretti. Transparency > automation.*

## 🤖 INTELLIGENT AGENT SYSTEM (24 Agents)

### 🎯 USAGE PATTERNS

**Simple/Routine Problems:**
```
"[Describe problem] using tdc-[domain]-expert"
```

**Complex/Unknown Problems:**
```
"Activate tdc-problem-isolator for [problem]"
```
- Isolates involved components
- Recommends correct agents
- Prepares focused context

**Deadlocks/Multi-Domain Issues:**
```
"Activate advisory system for [complex problem]"
```
- 4 advisory agents analyze in parallel
- Advisory coordinator synthesizes strategy
- Go/no-go decision with clear roadmap

**New Feature Planning:**
```
"Plan implementation of [feature] using tdc-problem-isolator"
```

### 🏗️ Core Development Team (7)
- **tdc-database-expert**: MySQL schema, migrations, queries (NO SQLAlchemy)
- **tdc-api-expert**: RESTful endpoints, validation, Second Life API
- **tdc-frontend-expert**: Nuxt 4, Vue 3, TypeScript, Tailwind CSS, GSAP/ScrollTrigger/Lenis, SSR/SSG/ISR, BFF server routes
- **tdc-backend-expert**: Flask architecture, business logic, services
- **tdc-auth-expert**: Authentication, OAuth2, JWT, sessions, RBAC
- **tdc-integration-expert**: Google Calendar, Facebook, Patreon, Second Life API
- **tdc-documentation-expert**: Documentation maintenance

### 🧪 Testing & Quality (5)
- **tdc-testing-expert**: Testing strategy coordinator (3+ agents needed)
- **tdc-visual-tester**: Visual regression, screenshot comparison, location themes
- **tdc-e2e-tester**: End-to-end workflows, user journey testing
- **tdc-browser-performance-tester**: Core Web Vitals, GSAP performance
- **tdc-accessibility-tester**: WCAG 2.1 AA compliance

### 🎯 Specialized Support (6)
- **tdc-security-expert**: Vulnerability assessment, OWASP
- **tdc-performance-expert**: Database optimization, caching, animation optimization
- **tdc-ux-researcher**: User research, personas, usability studies
- **tdc-network-expert**: Network diagnostics, connection pools
- **tdc-troubleshooting-expert**: Debugging, log analysis
- **tdc-problem-isolator**: Problem mapping and scope isolation

### 🛡️ Review Guardians (3)
**Mandatory review gates. Invoked via CLAUDE.md rules 15 and 16.**
- **tdc-design-enforcer**: Pre-implementation gate. Requires approved spec at `docs/superpowers/specs/*-design.md` BEFORE any code is written. Integrates with `superpowers:brainstorming` + `superpowers:writing-plans`.
- **tdc-code-reviewer**: Post-implementation two-phase review. Phase 1 spec compliance, Phase 2 code quality + security + TDC conventions + verification evidence. Blocks merge.
- **tdc-design-system-enforcer**: Visual compliance for UI changes. Enforces TDC visual identity (dark theme, per-location CSS vars, mood palettes, Inter typography, GSAP discipline, Tailwind tokens). Blocks UI merge.

### 🧠 Coordination (2)
- **tdc-orchestrator**: Master coordinator for complex workflows
- **tdc-problem-isolator**: Problem mapping and scope isolation

### ⚖️ Advisory System (5)
**For Complex Decisions & Deadlock Resolution:**
- **tdc-advisory-architecture**: Multi-approach architectural analysis
- **tdc-advisory-security**: Security risk assessment and mitigation
- **tdc-advisory-performance**: Performance impact and optimization
- **tdc-advisory-risk**: Comprehensive risk assessment and go/no-go
- **tdc-advisory-coordinator**: Advisory synthesis and final recommendations

## 🏢 PROJECT CONTEXT

**The Dreamer's Cave** is a virtual music club in Second Life featuring:
- 10+ themed locations with unique visual identities
- Custom multimedia technology that synchronizes visuals with live music
- Events calendar with Google Calendar integration
- Patreon-based revenue model with exclusive content
- Social media automation (Facebook posting)
- In-world Second Life API for venue displays

### User Roles
- **user**: Registered users with profiles, favorites, notifications
- **staff**: Event managers, content creators, moderators
- **admin**: Full system access, user management, integrations

### Technology Stack
| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+ / Flask |
| **Database** | MySQL 8.x with mysql-connector-python (NO SQLAlchemy) |
| **Frontend** | **Nuxt 4** (Vue 3 Composition API) + Vite + **TypeScript (strict)** |
| **Frontend ports** | Dev `:9503`, Prod `:9501` (node SSR server) |
| **Backend ports** | Dev `:9502`, Prod `:9500` (gunicorn) |
| **Styling** | Tailwind CSS + CSS variables (per-location theming) |
| **Animations** | GSAP + ScrollTrigger + Lenis (client-only `.client.ts` plugins) |
| **State** | Pinia via `@pinia/nuxt` |
| **i18n** | `@nuxtjs/i18n` — `prefix_except_default`, EN default, `/it/ /fr/ /es/` |
| **SEO** | `@nuxtjs/seo` + `@nuxtjs/sitemap` + `@nuxtjs/robots` (useSeoMeta, useSchemaOrg) |
| **Image** | `@nuxt/image` (`<NuxtImg>`, auto avif/webp) |
| **Forms** | vee-validate + zod (same schema client+server via `readValidatedBody`) |
| **Rich text** | `@tiptap/vue-3` (admin-only, `<ClientOnly>`-wrapped) |
| **Auth transport** | **JWT HttpOnly cookies** (`tdc_access` 15min Lax, `tdc_refresh` 7d Strict Path=/api/auth, rotated on use) |
| **Auth emit** | Flask + JWT + OAuth2 (Google, Discord, Facebook) |
| **BFF** | Nuxt `server/api/auth/**` + `server/api/revalidate` (auth cookie handling + on-demand ISR). All other `/api/**` proxy to Flask. |
| **Task Queue** | Celery + Redis |
| **Testing** | vitest + `@nuxt/test-utils` + happy-dom (unit/component); Playwright (E2E, 1920x1080) |

### External Integrations
- **Google Calendar**: Staff + Public event calendars
- **Facebook**: Page + Group posting
- **Patreon**: Supporter management, webhooks, exclusive content
- **Second Life**: In-world API for event displays

### 🎬 Rendering Strategy (per-route, via `routeRules` in `nuxt.config.ts`)

| Route pattern | Strategy | TTL / Notes |
|---|---|---|
| `/`, `/about`, `/contact` | **SSG** (`prerender: true`) | Build-time; rare changes |
| `/locations`, `/locations/**` | **SSG** + on-demand revalidate | 10 fixed venues, admin-edited |
| `/artists`, `/artists/**` | **SSG** + on-demand revalidate | Few changes |
| `/events`, `/events/**` | **ISR** (`swr: 300`) | 5 min stale-while-revalidate |
| `/blog`, `/blog/**` | **ISR** (`swr: 3600`) + on-demand | 1h + instant-publish via revalidate |
| `/auth/login`, `/auth/register`, `/auth/callback/**` | **SSR** (no cache) | Dynamic per session |
| `/dashboard/**`, `/admin/**` | **SPA** (`ssr: false`) | Auth-gated, no SEO value |
| `/api/auth/**`, `/api/revalidate` | Nitro server routes (BFF) | Handled by Nuxt node |
| `/api/**` (other) | Proxied to Flask | via nginx (prod) or Nitro devProxy (dev) |

**On-demand revalidation**: admin save → client POSTs `/api/revalidate { path }` → Nitro clears cache for that path → next visitor gets fresh content.

### 🔒 SSR Client-Only Rules (NON-NEGOTIABLE)

1. **GSAP + ScrollTrigger** → only in `*.client.ts` plugins. Use `gsap.context()` + `ctx.revert()` on `onBeforeUnmount`, else ScrollTrigger leaks across navigations and breaks scroll.
2. **Lenis** → only in `app/plugins/lenis.client.ts`. Sync with `gsap.ticker.add(lenis.raf)` — NEVER a separate `requestAnimationFrame` loop. Stop on `/admin/*` and `/dashboard/*`.
3. **Browser globals** (`window`, `document`, `localStorage`, `sessionStorage`, `matchMedia`, `IntersectionObserver`, `ResizeObserver`) → forbidden in `setup()` top-level. Use `onMounted()` or `.client.ts` files.
4. **Hydration-mismatch generators in templates** (`new Date()`, `Math.random()`, `crypto.randomUUID()`, `navigator.language`) → forbidden. Use ref + `onMounted` to set, or `<ClientOnly>` with matching-shape `#fallback`.
5. **TipTap / canvas / WebGL** → always inside `<ClientOnly>` with a matching-shape fallback, or in a page with `ssr: false`.
6. **Location theming** → `useHead({ bodyAttrs: { 'data-location': slug } })` + CSS vars in `app/assets/css/main.css`. Zero-JS at paint, SSR-safe.
7. **Auth tokens in cookies only** → `httpOnly: true, secure: prod, sameSite: 'lax'/'strict'`. NEVER in `localStorage`, NEVER readable by JS.

**References**:
- Deep spec: `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md`
- Implementation plan: `docs/superpowers/plans/2026-04-23-nuxt-integration.md`
- Frontend playbook: `docs/frontend/nuxt-playbook.md`
- Project plan v3: `docs/plans/pdp-v3.md` (created during migration)
- v2 (historical): `docs/plans/pdp-v2.md`

## 💬 Communication Style - CRITICAL
**🔴 BE DIRECT AND HONEST - NO EMPTY PRAISE**
- **Be direct and honest**, even when it means saying "this doesn't convince me"
- **NO automatic compliments** or false praise for everything
- **NO cheerleading** or applauding just to be nice
- **Highlight real achievements** when they actually deserve recognition
- **Point out issues directly** instead of sugar-coating them

## 🚨 REFACTORING GOLDEN RULES - ZERO TOLERANCE
**🔴 CRITICAL: During refactoring, NEVER change visual appearance or UI behavior**
- **ZERO visual changes** - no CSS, styling, spacing, colors, icons, text positioning
- **ZERO content changes** - no message text, wording, or visual elements
- **ZERO behavior changes** - same UX patterns, interactions, animations
- **REFACTORING = STRUCTURE ONLY** - move code, split components, organize logic

## 📏 FILE SIZE LIMITS - PRAGMATIC APPROACH
**🔴 MANDATORY for NEW files: Split when they exceed these thresholds**
- **Vue.js components** (.vue): MAX 500 lines - split into sub-components or composables
- **Python files** (.py): MAX 1000 lines - split into modules or separate classes
- **TypeScript files** (.ts): MAX 800 lines - split into modules or separate services

**🟡 EXISTING large files: Pragmatic survival rules**
- **DO NOT refactor** existing large files unless absolutely necessary
- **Small modifications** on large files are acceptable without refactoring
- **If refactoring breaks things**: Revert immediately, accept the large file

## 🛠️ TOOL PREFERENCE FOR FILE OPERATIONS
**🔴 MANDATORY: Always use Claude Code native tools for file operations**
- **✅ ALWAYS USE**: `Read`, `Edit`, `Write`, `MultiEdit` tools for file modifications
- **✅ TRANSPARENCY**: User sees exact changes with old_string → new_string diffs
- **⛔ AVOID**: MCP filesystem tools for content changes
- **✅ MCP FILESYSTEM OK for**: Directory listing, file info, search operations only

## 📚 DOCUMENTATION UPDATE MANDATORY WORKFLOW
**🔴 AUTOMATIC TRIGGER: When user requests documentation updates, commits, or pushes**

**Trigger Phrases** (auto-detect):
- "update documentation" / "aggiorna documentazione"
- "update docs" / "aggiorna docs"
- "commit and push" / "fai commit e push"
- Any phrase combining documentation + commit/push

**MANDATORY WORKFLOW**:
1. **🤖 AUTO-LAUNCH tdc-documentation-expert agent**
2. **🔴 CRITICAL: SINGLE COMMIT REQUIREMENT**
   - **ONE ATOMIC COMMIT** with comprehensive message
   - **NO separate documentation-only commits**

## 📂 PROJECT STRUCTURE

```
/data1/tdcweb/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models/          # Database table definitions
│   │   ├── routes/
│   │   │   ├── api/         # REST API endpoints
│   │   │   └── admin/       # Admin-only endpoints
│   │   ├── services/        # Business logic layer
│   │   ├── utils/           # Helpers (db.py, validators.py, decorators.py)
│   │   └── tasks/           # Celery async tasks
│   ├── migrations/          # Database migrations
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── components/      # Vue components by domain
│   │   │   ├── common/
│   │   │   ├── landing/
│   │   │   ├── locations/
│   │   │   ├── events/
│   │   │   ├── artists/
│   │   │   ├── blog/
│   │   │   ├── auth/
│   │   │   ├── user/
│   │   │   └── admin/
│   │   ├── composables/     # Vue composables (useLocationTheme, useScrollAnimation)
│   │   ├── stores/          # Pinia state management
│   │   ├── views/           # Route-specific pages
│   │   │   └── admin/
│   │   ├── router/          # Vue Router
│   │   ├── i18n/            # Translations (EN, IT, FR, ES)
│   │   ├── styles/          # Global CSS + Tailwind
│   │   ├── assets/          # Images, videos, fonts
│   │   └── utils/
│   └── public/
│
├── docs/
│   └── plans/
│       └── pdp-v2.md        # Project Development Plan
│
├── nginx/                   # Nginx configuration
│
├── .claude/
│   ├── agents/              # 24 specialized agents (tdc-*)
│   └── skills/              # 5 skills (tdc-docs, tdc-backend, etc.)
│
└── CLAUDE.md                # This file
```

## 🗄️ Database Configuration

**Database Credentials:**
- **Database**: `tdcweb`
- **User**: `tdcweb`
- **Password**: `tdcweb`
- **Root Password**: `rutt1n0`
- **Host**: `localhost`
- **Port**: `3306`

**🔴 CRITICAL: NO SQLAlchemy - Use mysql-connector-python ONLY**

```python
# utils/db.py pattern
import mysql.connector
from mysql.connector import pooling

connection_pool = pooling.MySQLConnectionPool(
    pool_name="tdc_pool",
    pool_size=20,
    host="localhost",
    database="tdcweb",
    user="tdcweb",
    password="tdcweb",
    charset="utf8mb4",
    collation="utf8mb4_unicode_ci"
)

def get_db():
    return connection_pool.get_connection()

def query_db(sql, params=None, one=False):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params or ())
    result = cursor.fetchone() if one else cursor.fetchall()
    cursor.close()
    conn.close()
    return result
```

## 📌 MCP Server Infrastructure

- **mysql-dev**: Development database (`tdcweb`)
- **filesystem**: Project codebase access
- **playwright**: Browser automation and testing
- **context7**: Library documentation and code examples

### 🎭 Playwright MCP - Browser Testing

**Use for:**
- Visual testing and screenshots
- E2E workflow testing
- UI interaction testing
- Location theme validation

**Key Tools:**
- `mcp__plugin_playwright_playwright__browser_navigate` - Navigate to URL
- `mcp__plugin_playwright_playwright__browser_snapshot` - Get accessibility tree
- `mcp__plugin_playwright_playwright__browser_click` - Click elements
- `mcp__plugin_playwright_playwright__browser_type` - Type text
- `mcp__plugin_playwright_playwright__browser_take_screenshot` - Capture screenshots
- `mcp__plugin_playwright_playwright__browser_resize` - Set viewport size

**Workflow Pattern:**
```
1. browser_resize(1920, 1080)           # Set resolution
2. browser_navigate(url="...")          # Go to page
3. browser_snapshot()                   # Get element refs
4. browser_type(ref="...", text="...")  # Fill form fields
5. browser_click(ref="...", element="...")  # Click buttons
6. browser_take_screenshot()            # Verify result
```

## 🎨 Location Theming System

Each location has a unique visual identity using CSS variables:

```css
/* Example: The Dreamer's Cave */
[data-location="dreamerscave"] {
  --color-primary: #0891b2;
  --color-secondary: #06b6d4;
  --color-accent: #22c55e;
  --color-dark: #0c1222;
  --gradient-hero: linear-gradient(135deg, #0891b2, #22c55e, #eab308);
}
```

**Mood Categories:**
- **Cosmic/Tech**: DreamersCave, DreamVision, Evanescence
- **Hybrid**: LiveMagic, The Lounge
- **Warm/Intimate**: Arquipélago, Noah's Ark, Jazz Club

## 🎬 Animation System (GSAP)

**Core Libraries:**
- **GSAP**: Main animation engine
- **ScrollTrigger**: Scroll-based animations
- **Lenis**: Smooth scrolling

**Composable Pattern:**
```javascript
// composables/useScrollAnimation.js
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import Lenis from 'lenis'

gsap.registerPlugin(ScrollTrigger)

export function useScrollAnimation() {
  const initSmoothScroll = () => {
    const lenis = new Lenis({ duration: 1.2 })
    // ...
  }

  const animateReveal = (elements, options = {}) => {
    gsap.from(elements, {
      y: 100,
      opacity: 0,
      duration: 1,
      stagger: 0.2,
      scrollTrigger: { trigger: elements[0], start: 'top 80%' }
    })
  }

  return { initSmoothScroll, animateReveal }
}
```

## 🌐 i18n System

**Supported Languages:**
- **EN** (default)
- **IT** (Italian)
- **FR** (French)
- **ES** (Spanish)

**Translation Strategy:**
- UI strings: JSON files in `/frontend/src/i18n/`
- Content: Database `*_translations` tables (location_translations, event_translations, etc.)
- Language detection: URL param > cookie > browser preference > default (EN)

## 🔐 Security Rules

1. **Input Validation**: All user inputs validated and sanitized
2. **Audit Logging**: Track all admin actions
3. **Never commit secrets**: Always use environment variables
4. **Follow security practices**: OWASP guidelines, secure coding
5. **Password hashing**: bcrypt with min 12 rounds
6. **JWT tokens**: Short expiry (15 min access, 7 day refresh)
7. **CSRF protection**: All forms protected
8. **Rate limiting**: Auth endpoints protected

## 🚀 Available Skills

| Skill | Description | Trigger |
|-------|-------------|---------|
| **tdc-docs** | Documentation maintenance | `/docs` |
| **tdc-backend** | Flask backend development | Backend work |
| **tdc-frontend** | Vue.js frontend development | Frontend work |
| **tdc-database** | MySQL database operations | Database work |
| **tdc-testing** | Testing strategy and execution | Testing work |

---

**Domain**: [thedreamerscave.club](https://thedreamerscave.club)
**Hosting**: mioh1 @ `/data1/tdcweb`
**Motto**: "You Can See The Music"
