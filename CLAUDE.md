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
- **tdc-frontend-expert**: Vue.js 3, TypeScript, Tailwind CSS, GSAP/ScrollTrigger
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
| **Frontend** | Vue.js 3 (Composition API) + Vite |
| **Styling** | Tailwind CSS |
| **Animations** | GSAP + ScrollTrigger + Lenis |
| **State** | Pinia |
| **i18n** | Vue I18n (EN, IT, FR, ES) |
| **Auth** | Flask-Login + JWT + OAuth2 (Google, Discord, Facebook) |
| **Task Queue** | Celery + Redis |

### External Integrations
- **Google Calendar**: Staff + Public event calendars
- **Facebook**: Page + Group posting
- **Patreon**: Supporter management, webhooks, exclusive content
- **Second Life**: In-world API for event displays

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
import Lenis from '@studio-freight/lenis'

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
