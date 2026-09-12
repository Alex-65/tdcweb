---
name: tdc-testing
description: Create and run tests for The Dreamer's Cave. Frontend vitest + @nuxt/test-utils + happy-dom; backend pytest with real-MySQL fixtures (NO DB mocks); E2E Playwright at 1920x1080.
fork: true
---

# TDC Testing Expert (Nuxt 4 + pytest)

Expert skill for creating and running tests on The Dreamer's Cave.

## Trigger

Use this skill when:
- User asks to create or run tests
- User says "/testing", "/tdc-testing", "/test", "/pytest", or "/vitest"
- User asks about test coverage or fixtures
- User wants to verify frontend BFF handlers, composables, middleware, or pages
- User wants to verify Flask endpoints, models, or auth decorators
- User needs E2E or visual regression coverage

## Project Context

**The Dreamer's Cave** -- virtual music club website. **Motto:** "You Can See The Music".

### Test Stack

| Layer | Tool | Notes |
|---|---|---|
| Frontend unit / handler | **vitest** + `@nuxt/test-utils` + happy-dom | Pure helpers + thin wrappers via stub injection |
| Frontend E2E | **Playwright** | 1920x1080 always (CLAUDE.md rule 14); uses `mcp__plugin_playwright_playwright__*` tools when available |
| Backend unit / integration | **pytest 9.x** | Real MySQL `tdcweb_test` schema -- NO DB mocks (CLAUDE.md rule, mysql-connector-python only) |
| Backend coverage | `pytest-cov` | `.coveragerc` |
| Frontend coverage | `@vitest/coverage-v8` | Configured in `vitest.config.ts` |

### Test Database

| Property | Value |
|---|---|
| Schema | `tdcweb_test` (separate from dev `tdcweb`) |
| User | `tdcweb` |
| Password | `tdcweb` |
| Strategy | conftest-managed session lifecycle + per-test cleanup fixtures |

**Important**: the `tdcweb` user does NOT have CREATE DATABASE privilege. `_ensure_test_db_schema` in conftest is a **VERIFIER**, not a provisioner -- it asserts the schema exists and matches expected tables, raising loudly if not. The schema is provisioned out-of-band by an operator with root credentials before tests run.

### File Structure

```
backend/
|-- tests/
|   |-- __init__.py
|   |-- conftest.py            <-- session/per-test fixtures, real-MySQL setup
|   |-- pytest.ini             <-- markers, paths, coverage config
|   |-- test_foundation.py     <-- DB connectivity, schema sanity (5 cases)
|   |-- test_auth.py           <-- /api/auth/* end-to-end (18 cases)
|   |-- test_locations.py      <-- /api/locations/* (10 cases)
|   |-- test_events.py         <-- /api/events/* (12 cases)
|   `-- ...

frontend/
|-- tests/
|   |-- unit/
|   |   |-- login-handler.test.ts        <-- BFF handler test (typed-globalThis stubs)
|   |   |-- useApiFetch.test.ts          <-- pure-helper test
|   |   |-- flask-client.test.ts         <-- hybrid resolver test
|   |   |-- auth-decisions.test.ts       <-- pure middleware decision test
|   |   `-- ...
|   `-- e2e/
|       |-- auth-chain.spec.ts           <-- login -> me -> revalidate -> logout
|       |-- location-theming.spec.ts
|       |-- i18n-routing.spec.ts
|       `-- ...
|-- vitest.config.ts
`-- playwright.config.ts
```

---

## Backend (pytest with real MySQL)

### Iron rules (from CLAUDE.md)

1. **NO DB mocks**. Tests run against real MySQL `tdcweb_test`. mysql-connector-python only -- no SQLAlchemy.
2. **Test state cleanup is MANDATORY** (rule 17). Any test that mutates persistent state restores the pre-test state on completion. Tests that crash mid-run must clean up before the next test starts.
3. **Real bcrypt, real JWT**. Auth tests hash/verify real passwords and emit/parse real tokens.

### conftest.py fixture catalogue

```python
# backend/tests/conftest.py
import os
import pytest
from app import create_app
from app.utils.db import get_db
from app.utils.jwt_helpers import emit_access_token

@pytest.fixture(scope='session', autouse=True)
def _ensure_test_db_schema():
    """VERIFIER: assert tdcweb_test schema exists and has expected tables.
    Does NOT create the schema -- tdcweb user lacks CREATE DATABASE privilege."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DATABASE()")
    db_name = cursor.fetchone()[0]
    assert db_name == 'tdcweb_test', f"Expected tdcweb_test, got {db_name}"
    cursor.execute("SHOW TABLES")
    tables = {row[0] for row in cursor.fetchall()}
    required = {'users', 'locations', 'events', 'oauth_accounts'}
    missing = required - tables
    assert not missing, f"Missing tables in tdcweb_test: {missing}"
    cursor.close()
    conn.close()


@pytest.fixture(scope='session')
def app():
    os.environ.setdefault('FLASK_ENV', 'testing')
    os.environ.setdefault('JWT_SECRET_KEY', 'test-jwt-secret-key-not-for-prod')
    os.environ.setdefault('SECRET_KEY', 'test-secret-key-not-for-prod')
    flask_app = create_app('testing')
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def fresh_user(app):
    """Per-test user. Cleans up automatically after the test."""
    import bcrypt
    password = 'test-password-12345'
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'user')",
        (f'fresh-{os.urandom(4).hex()}@test.local', pw_hash),
    )
    user_id = cur.lastrowid
    conn.commit()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    # Stash password for E2E login tests
    user['_test_password'] = password
    yield user
    # Cleanup
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()


@pytest.fixture
def staff_user(app):
    # Same pattern, role='staff'
    ...


@pytest.fixture
def admin_user(app):
    # Same pattern, role='admin'
    ...


@pytest.fixture
def make_location(app):
    """Factory fixture: yields a function that creates locations + cleans them up."""
    created = []

    def _make(slug='test-loc', name='Test Loc'):
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO locations (slug, name) VALUES (%s, %s)",
            (slug, name),
        )
        loc_id = cur.lastrowid
        created.append(loc_id)
        conn.commit()
        cur.close()
        conn.close()
        return loc_id

    yield _make

    # Cleanup ALL created locations
    if created:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM locations WHERE id IN (%s)" % ','.join(['%s'] * len(created)),
            created,
        )
        conn.commit()
        cur.close()
        conn.close()


@pytest.fixture
def make_event(app, make_location):
    """Factory: yields a function that creates events + cleans up."""
    created = []

    def _make(title='Test Event', location_id=None):
        if location_id is None:
            location_id = make_location()
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO events (title, location_id, starts_at) VALUES (%s, %s, NOW())",
            (title, location_id),
        )
        ev_id = cur.lastrowid
        created.append(ev_id)
        conn.commit()
        cur.close()
        conn.close()
        return ev_id

    yield _make

    if created:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM events WHERE id IN (%s)" % ','.join(['%s'] * len(created)),
            created,
        )
        conn.commit()
        cur.close()
        conn.close()
```

### Backend test patterns

**Auth happy path (real bcrypt + real JWT):**

```python
def test_login_returns_tokens_and_user(client, fresh_user):
    resp = client.post('/api/auth/login', json={
        'email': fresh_user['email'],
        'password': fresh_user['_test_password'],
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert 'access' in body['data']
    assert 'refresh' in body['data']
    assert body['data']['user']['email'] == fresh_user['email']
```

**Auth boundary:**

```python
def test_login_rejects_wrong_password(client, fresh_user):
    resp = client.post('/api/auth/login', json={
        'email': fresh_user['email'],
        'password': 'wrong-password',
    })
    assert resp.status_code == 401
    body = resp.get_json()
    assert body['success'] is False
```

**Role gate:**

```python
def test_admin_only_endpoint_rejects_user(client, fresh_user, app):
    from app.utils.jwt_helpers import emit_access_token
    token = emit_access_token(user_id=fresh_user['id'], role='user')
    resp = client.get('/api/admin/users', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 403
```

**SQL injection regression:**

```python
def test_login_email_is_parameterized(client):
    resp = client.post('/api/auth/login', json={
        'email': "' OR '1'='1",
        'password': 'whatever',
    })
    # Must reject cleanly, not 500
    assert resp.status_code in (400, 401)
```

### Running backend tests

```bash
cd /data1/tdcweb-dev/backend
pytest                                  # all tests
pytest tests/test_auth.py               # one file
pytest tests/test_auth.py::test_login_returns_tokens_and_user  # one case
pytest -v -s                            # verbose + see print/logger output
pytest --cov=app --cov-report=term-missing
```

---

## Frontend (vitest + @nuxt/test-utils + happy-dom)

### The bare auto-import gotcha

Nuxt auto-imports (`useFetch`, `useNuxtApp`, `useState`, `defineEventHandler`, `getCookie`, `setCookie`, `useRuntimeConfig`, `$fetch`) are NOT real bare imports. They are injected by the build at module-eval time. In a vitest run, those names exist either:
- On `globalThis` (Nitro dev sometimes does this), OR
- As regular module bindings inside `.nuxt/dev/...`, OR
- Not at all (server bundle for production)

**Two solutions, pick by code location.**

### Server code (`server/utils/`, `server/api/`, `server/middleware/`): hybrid resolve

The implementation function reads its dependencies through a resolver that tries `globalThis` first, falls back to a real module import. Tests stub the `globalThis` slot with typed-globalThis (NEVER `as any`).

**Reference**: `frontend/server/utils/flask-client.ts` -- the canonical resilient pattern. Tests at `frontend/tests/unit/flask-client.test.ts`.

```typescript
// flask-client.ts
import type { H3Event } from 'h3'
import { $fetch as ofetchFallback } from 'ofetch'

function resolveFetch() {
  const g = globalThis as any
  if (typeof g.$fetch === 'function') return g.$fetch
  return ofetchFallback
}

function resolveRuntimeConfig() {
  const g = globalThis as any
  if (typeof g.useRuntimeConfig === 'function') return g.useRuntimeConfig()
  // Fallback: nitropack/runtime exports useRuntimeConfig in built bundle
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { useRuntimeConfig } = require('nitropack/runtime')
    return useRuntimeConfig()
  } catch {
    throw new Error('flaskFetch: useRuntimeConfig is unavailable -- both globalThis and nitropack/runtime missing')
  }
}

export async function flaskFetch<T>(path: string, event: H3Event, opts?: any): Promise<T> {
  const $f = resolveFetch()
  const cfg = resolveRuntimeConfig()
  const headers = { ...(opts?.headers ?? {}), ...(event.context.flaskHeaders ?? {}) }
  return $f(`${cfg.flaskUrl}${path}`, { ...opts, headers })
}
```

```typescript
// tests/unit/flask-client.test.ts -- typed-globalThis stubs, never `as any`
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import type { H3Event } from 'h3'

interface NuxtGlobals {
  $fetch?: ReturnType<typeof vi.fn>
  useRuntimeConfig?: () => { flaskUrl: string }
}

declare global {
  // eslint-disable-next-line vars-on-top, no-var
  var $fetch: NuxtGlobals['$fetch']
  // eslint-disable-next-line vars-on-top, no-var
  var useRuntimeConfig: NuxtGlobals['useRuntimeConfig']
}

describe('flaskFetch', () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue({ ok: true })
    globalThis.$fetch = fetchMock
    globalThis.useRuntimeConfig = () => ({ flaskUrl: 'http://flask.test' })
  })

  afterEach(() => {
    delete (globalThis as Partial<NuxtGlobals>).$fetch
    delete (globalThis as Partial<NuxtGlobals>).useRuntimeConfig
  })

  it('resolves baseURL from runtime config', async () => {
    const { flaskFetch } = await import('~/server/utils/flask-client')
    const event = { context: {} } as H3Event
    await flaskFetch('/api/health', event)
    expect(fetchMock).toHaveBeenCalledWith(
      'http://flask.test/api/health',
      expect.objectContaining({ headers: expect.any(Object) }),
    )
  })

  it('falls back to ofetch when globalThis.$fetch is absent', async () => {
    delete (globalThis as Partial<NuxtGlobals>).$fetch
    // Re-import or use module factory; ofetch fallback path covered
    // ...
  })
})
```

### App code (composables, middleware, pages): pure-helper extraction

`mockNuxtImport` from `@nuxt/test-utils` works, but is brittle for composables that wrap many auto-imports. **Preferred approach**: extract pure decision logic into a helper function and unit-test the helper directly.

**Reference**: `frontend/app/utils/auth-decisions.ts` (pure) tested by `frontend/tests/unit/auth-decisions.test.ts`. The thin Nuxt-aware wrapper (`app/middleware/auth.ts`) is covered by E2E.

```typescript
// app/utils/auth-decisions.ts -- PURE
export interface AuthOutcome { type: 'pass' | 'redirect'; to?: string }

export function decideAuthOutcome(input: {
  isAuthed: boolean
  toFullPath: string
}): AuthOutcome {
  if (input.isAuthed) return { type: 'pass' }
  return { type: 'redirect', to: `/auth/login?redirect=${encodeURIComponent(input.toFullPath)}` }
}
```

```typescript
// tests/unit/auth-decisions.test.ts -- pure, no Nuxt context needed
import { describe, it, expect } from 'vitest'
import { decideAuthOutcome } from '~/utils/auth-decisions'

describe('decideAuthOutcome', () => {
  it('passes when authenticated', () => {
    expect(decideAuthOutcome({ isAuthed: true, toFullPath: '/dashboard' }))
      .toEqual({ type: 'pass' })
  })

  it('redirects to login with encoded redirect when not authenticated', () => {
    expect(decideAuthOutcome({ isAuthed: false, toFullPath: '/dashboard?tab=x' }))
      .toEqual({ type: 'redirect', to: '/auth/login?redirect=%2Fdashboard%3Ftab%3Dx' })
  })
})
```

### BFF handler test (canonical: login)

**Reference**: `frontend/tests/unit/login-handler.test.ts`. Pattern: typed-globalThis stubs for `flaskFetch` + `setAccessCookie` + `setRefreshCookie`, dynamic import of the handler, assert return shape AND side effects.

```typescript
// tests/unit/login-handler.test.ts (abridged)
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import type { H3Event } from 'h3'

interface Stubs {
  flaskFetch?: ReturnType<typeof vi.fn>
  setAccessCookie?: ReturnType<typeof vi.fn>
  setRefreshCookie?: ReturnType<typeof vi.fn>
  readValidatedBody?: ReturnType<typeof vi.fn>
}

declare global {
  // eslint-disable-next-line vars-on-top, no-var
  var __TDC_TEST_STUBS__: Stubs
}

describe('login.post handler', () => {
  beforeEach(() => {
    globalThis.__TDC_TEST_STUBS__ = {
      flaskFetch: vi.fn().mockResolvedValue({
        access: 'a', refresh: 'r', user: { id: 1, email: 'a@b.c', role: 'user' },
      }),
      setAccessCookie: vi.fn(),
      setRefreshCookie: vi.fn(),
      readValidatedBody: vi.fn().mockResolvedValue({ email: 'a@b.c', password: 'pw' }),
    }
  })

  afterEach(() => {
    delete (globalThis as Partial<{ __TDC_TEST_STUBS__: Stubs }>).__TDC_TEST_STUBS__
  })

  it('sets both cookies and returns user', async () => {
    const { default: handler } = await import('~/server/api/auth/login.post')
    const event = { context: {} } as H3Event
    const result = await handler(event)
    expect(result).toEqual({ user: { id: 1, email: 'a@b.c', role: 'user' } })
    expect(globalThis.__TDC_TEST_STUBS__.setAccessCookie).toHaveBeenCalledWith(event, 'a')
    expect(globalThis.__TDC_TEST_STUBS__.setRefreshCookie).toHaveBeenCalledWith(event, 'r')
  })
})
```

### Running frontend tests

```bash
cd /data1/tdcweb-dev/frontend
npm test                          # all
npm test -- login-handler         # filter by name pattern
npm test -- --reporter=verbose
npm run test:coverage             # if configured
```

---

## E2E (Playwright at 1920x1080 -- CLAUDE.md rule 14)

When MCP Playwright tools are available, prefer them: `mcp__plugin_playwright_playwright__browser_navigate`, `_snapshot`, `_click`, `_type`, `_take_screenshot`, `_resize`. Otherwise standard `@playwright/test`.

```typescript
// tests/e2e/auth-chain.spec.ts
import { test, expect } from '@playwright/test'

test.use({ viewport: { width: 1920, height: 1080 } })

test('login -> me -> revalidate -> logout', async ({ page, request }) => {
  // 1. Login via BFF (sets HttpOnly cookies)
  await page.goto('http://localhost:9503/auth/login')
  await page.fill('input[type=email]', 'admin@test.local')
  await page.fill('input[type=password]', 'admin-pass-12345')
  await page.click('button[type=submit]')
  await page.waitForURL('**/dashboard')

  // 2. Verify session via /api/auth/me (cookie auto-included by browser)
  const me = await page.request.get('http://localhost:9503/api/auth/me')
  expect(me.status()).toBe(200)

  // 3. Admin revalidate
  const rev = await page.request.post('http://localhost:9503/api/revalidate', {
    data: { path: '/locations' },
  })
  expect(rev.status()).toBe(200)

  // 4. Logout clears cookies
  await page.click('button[data-test=logout]')
  const meAfter = await page.request.get('http://localhost:9503/api/auth/me')
  expect(meAfter.status()).toBe(401)
})
```

### Running E2E

```bash
cd /data1/tdcweb-dev/frontend
npx playwright test                              # all
npx playwright test auth-chain.spec.ts           # one file
npx playwright test --headed                     # see the browser
npx playwright test --ui                         # interactive UI
```

**Resolution rule**: ALWAYS 1920x1080. Do not use Playwright defaults.

---

## Test Pyramid for TDC

| Layer | Volume | What we cover |
|---|---|---|
| Backend integration (real MySQL) | **Heavy** -- the trust foundation | Endpoints, auth, role gates, SQL parameterization, DB constraint behaviors. Phase 4 = 46 cases. |
| Frontend unit (pure helpers + handlers) | **Modest** | Decision functions (`decideAuthOutcome`, `unwrapEnvelope`, `resolveApiBaseURL`), BFF handlers via typed-globalThis stubs, server utils via hybrid resolver. Phase 4 = 73 cases. |
| Frontend component (vitest + happy-dom) | **Light** | Render-shape contracts only; visual / interaction = E2E. Reach for this when a component owns logic that can't be extracted. |
| E2E (Playwright) | **Targeted** | Auth chain, location theming, i18n routing, accessibility smoke, critical user journeys. NOT a substitute for unit / integration tests. |

**Why heavy backend / modest frontend unit?** TDC has Flask owning the business rules and SQL; the frontend largely orchestrates fetches and renders. Real-MySQL integration tests give us ground truth on what the API actually does -- that's where regressions hide.

---

## Iron rules (CLAUDE.md restated)

- **Rule 13**: Use `mcp__plugin_playwright_playwright__*` tools for browser testing when available.
- **Rule 14**: Browser viewport ALWAYS 1920x1080.
- **Rule 15**: After every subagent task, run all tests + create missing tests + dispatch reviewers + STOP at checkpoint.
- **Rule 17**: Test state cleanup is mandatory. Pre-test state == post-test state. Always.
- **No DB mocks** (project convention): backend tests run against real `tdcweb_test`. mysql-connector-python only.
- **No `any` in tests**: use typed-globalThis declarations or proper interfaces. `as any` is a smell.

---

## Forbidden patterns

| Don't | Do |
|---|---|
| Mock the database | Use real `tdcweb_test`, fixtures with cleanup |
| `as any` to satisfy TS in test setup | typed-globalThis interface + `Partial<>` for cleanup |
| Test that leaves rows behind | Fixture with explicit cleanup, or transaction rollback if you set one up |
| `mockNuxtImport` for complex composables | Extract pure helper, test the helper |
| Hardcoded sleep / arbitrary timeouts | `await page.waitForURL`, `await page.waitForResponse`, explicit conditions |
| Snapshot test for everything | Snapshots only where the contract is intentionally rigid (rendered SEO meta, sitemap output) |
| One mega-test that asserts ten things | One test = one assertion topic. Helpers compose. |
| Skipping cleanup because "the next test will reset" | No. Each test owns its own setup AND teardown. |
| Test that depends on a previous test running | Tests must be independently runnable in any order |

---

## Closing checklist

Before declaring a test task done:

- [ ] All new code has at least happy-path + one failure-path coverage
- [ ] Backend tests run against real `tdcweb_test`, not mocks
- [ ] Each fixture cleans up after itself; `pytest --collect-only` shows no leftovers
- [ ] Frontend tests use typed-globalThis, never `as any`
- [ ] Pure helpers extracted where Nuxt auto-imports made the wrapper untestable
- [ ] E2E specs run at 1920x1080
- [ ] No `console.log` / `print` left in test code
- [ ] Test files pass even when run in isolation (no order dependency)
- [ ] Coverage delta meaningful, not just box-checked

---

## Integration with other agents / skills

| Hand off to | When |
|---|---|
| `tdc-frontend-expert` / `tdc-frontend` skill | Implementing the code under test (Vue / Nuxt) |
| `tdc-backend-expert` / `tdc-backend` skill | Implementing Flask code under test |
| `tdc-database-expert` / `tdc-database` skill | Schema design, fixture data, migration coverage |
| `tdc-e2e-tester` agent | Multi-step user-journey planning |
| `tdc-visual-tester` agent | Visual regression / screenshot diffs (location theming) |
| `tdc-accessibility-tester` agent | WCAG 2.1 AA audits |
| `tdc-browser-performance-tester` agent | Core Web Vitals, GSAP frame budget |

---

## Closing principles (CLAUDE.md)

- **Debug-first**: see the failure with proof before "fixing" the test or the code under test.
- **Fix-Test-Verify**: one fix -> run the affected test -> only proceed if still broken.
- **Test before declaring done**: rule 10. No "I think this is fine".
- **Tests come WITH the code at phase end**: rule 15 + 16. They land in the same atomic commit as the feature.

The site's motto is **"You Can See The Music"**. Tests are how we keep the music in tune across releases.
