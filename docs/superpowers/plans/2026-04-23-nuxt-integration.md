# Nuxt 4 Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the TDC frontend from Vue 3 + Vite SPA to Nuxt 4 with
TypeScript, per-route rendering strategies (SSG/ISR/SSR/SPA), hybrid
BFF authentication, and SSR-safe GSAP/Lenis/i18n integration, without
altering the Flask + MySQL backend.

**Architecture:** Nuxt 4 runs on `:9503` in dev and `:9501` in prod
(adjacent to Flask `:9500`). The Nuxt `server/api/auth/**` BFF handles
login/logout/refresh by issuing HttpOnly JWT cookies; all other data
flows go directly from Nuxt (SSR) or the browser (CSR) to Flask. CSS
variables drive per-location theming, GSAP/Lenis are confined to
client-only plugins.

**Tech Stack:** Nuxt 4, TypeScript (strict), Vite, Pinia (`@pinia/nuxt`),
`@nuxtjs/i18n`, `@nuxtjs/tailwindcss`, `@nuxtjs/seo`, `@nuxtjs/sitemap`,
`@nuxtjs/robots`, `@nuxt/image`, `@vueuse/nuxt`, GSAP + ScrollTrigger,
`lenis`, `@tiptap/vue-3`, `vee-validate` + `zod`,
`lucide-vue-next`, `vitest`, `@nuxt/test-utils`, Playwright.

**Reference spec:** `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md`

**Working branch:** `dev` (no worktree — migration runs in-place with
atomic commits per task; scaffold backup covers rollback).

---

## File Structure

### Files to create

| Path | Responsibility |
|---|---|
| `frontend/nuxt.config.ts` | Nuxt configuration: modules, routeRules, i18n, nitro devProxy, runtime config |
| `frontend/tsconfig.json` | TypeScript strict mode (auto-extended from `.nuxt/tsconfig.json`) |
| `frontend/tailwind.config.ts` | Tailwind + TDC theme tokens (ported from backup) |
| `frontend/eslint.config.ts` | ESLint flat config with Vue/TS rules |
| `frontend/.env.example` | Template for env vars |
| `frontend/.env` | Local dev env (FLASK_URL, NUXT_FLASK_URL) |
| `frontend/app/app.vue` | Root component |
| `frontend/app/app.config.ts` | Runtime app config (theme defaults) |
| `frontend/app/error.vue` | Global error page |
| `frontend/app/pages/index.vue` | Landing page (SSG) |
| `frontend/app/pages/locations/index.vue` | Locations list (SSG) |
| `frontend/app/pages/events/index.vue` | Events list (ISR 5 min) |
| `frontend/app/components/common/AppHeader.vue` | Site header |
| `frontend/app/components/common/AppFooter.vue` | Site footer |
| `frontend/app/composables/useApi.ts` | `$fetch` wrapper with 401 auto-refresh |
| `frontend/app/composables/useAuth.ts` | Auth state from cookie |
| `frontend/app/composables/useScrollAnimation.ts` | GSAP ScrollTrigger wrapper (SSR-safe) |
| `frontend/app/composables/useSmoothScroll.ts` | Lenis wrapper |
| `frontend/app/composables/useLocationTheme.ts` | Per-location CSS var switcher |
| `frontend/app/stores/auth.ts` | Pinia auth store |
| `frontend/app/stores/locale.ts` | Pinia locale store |
| `frontend/app/stores/ui.ts` | Pinia UI state |
| `frontend/app/middleware/auth.ts` | Route guard: requires authenticated user |
| `frontend/app/middleware/admin.ts` | Route guard: requires role=admin |
| `frontend/app/middleware/staff.ts` | Route guard: requires role in (staff, admin) |
| `frontend/app/plugins/gsap.client.ts` | Register GSAP + ScrollTrigger |
| `frontend/app/plugins/lenis.client.ts` | Init Lenis, sync with GSAP ticker |
| `frontend/app/types/api.ts` | Shared API response types |
| `frontend/app/types/location.ts` | Location types |
| `frontend/app/types/event.ts` | Event types |
| `frontend/app/types/user.ts` | User + auth types |
| `frontend/app/assets/css/main.css` | Tailwind layers + base styles |
| `frontend/server/api/auth/login.post.ts` | BFF login → Flask + set cookies |
| `frontend/server/api/auth/logout.post.ts` | BFF logout → Flask + clear cookies |
| `frontend/server/api/auth/refresh.post.ts` | BFF refresh → rotate tokens |
| `frontend/server/api/auth/me.get.ts` | BFF identity check |
| `frontend/server/api/revalidate.post.ts` | Admin on-demand ISR invalidation |
| `frontend/server/middleware/auth-forward.ts` | Populates `event.context.flaskHeaders` from cookie |
| `frontend/server/utils/flask-client.ts` | `flaskFetch()` helper |
| `frontend/server/utils/cookies.ts` | HttpOnly set/clear helpers |
| `frontend/i18n/locales/en.json` | English UI strings |
| `frontend/i18n/locales/it.json` | Italian UI strings |
| `frontend/i18n/locales/fr.json` | French UI strings |
| `frontend/i18n/locales/es.json` | Spanish UI strings |
| `frontend/tests/unit/auth-forward.test.ts` | Test auth-forward middleware |
| `frontend/tests/unit/flask-client.test.ts` | Test flaskFetch() |
| `frontend/tests/unit/login-handler.test.ts` | Test login BFF handler |
| `frontend/tests/unit/useApi.test.ts` | Test 401 auto-refresh |
| `nginx/thedreamerscave.conf` | Production nginx config |
| `deploy/systemd/tdcweb-frontend.service` | systemd unit for Nuxt node |
| `docs/plans/pdp-v3.md` | New Nuxt-native project plan (v2 kept historical) |

### Files to modify

| Path | Change |
|---|---|
| `CLAUDE.md` | Update stack table, add Rendering Strategy + SSR Client-Only sections |
| `.claude/agents/tdc-frontend-expert.md` | Nuxt 4 context + TS patterns |

### Files to rename

| Current | New |
|---|---|
| `frontend/` (existing Vue scaffold) | `frontend.vue-backup/` (untracked, local reference) |

---

## Phase 1 — Backup and scaffold

### Task 1.1: Back up the existing Vue scaffold

**Files:**
- Rename: `frontend/` → `frontend.vue-backup/`

- [ ] **Step 1: Confirm working directory is clean of spurious edits**

Run: `git status`
Expected: only pre-existing untracked files (`frontend/`, `frontend/package-lock.json`, `frontend/postcss.config.js`, `frontend/src/`, `frontend/tailwind.config.js`, `package.json`, `package-lock.json`) and the committed spec. No other tracked modifications.

- [ ] **Step 2: Rename the Vue scaffold to a backup directory**

Run: `mv /data1/tdcweb-dev/frontend /data1/tdcweb-dev/frontend.vue-backup`

- [ ] **Step 3: Verify the rename**

Run: `ls /data1/tdcweb-dev/ | grep -E 'frontend'`
Expected output: `frontend.vue-backup` (and nothing matching plain `frontend`).

- [ ] **Step 4: No commit**

The backup directory is untracked and stays untracked. No git action.

---

### Task 1.2: Scaffold a fresh Nuxt 4 project

**Files:**
- Create: `frontend/` (Nuxt 4 scaffold, many files)

- [ ] **Step 1: Run nuxi init**

Run: `cd /data1/tdcweb-dev && npx nuxi@latest init frontend --package-manager npm --no-gitInit`
Expected: a new `frontend/` directory with `nuxt.config.ts`, `package.json`, `app/app.vue`, `tsconfig.json`, `public/`, `.gitignore`, etc.

If `nuxi init` prompts interactively despite flags, answer: package manager = `npm`, initialize git repo = `no`.

- [ ] **Step 2: Verify the scaffold**

Run: `ls /data1/tdcweb-dev/frontend/`
Expected (minimum): `app/`, `nuxt.config.ts`, `package.json`, `public/`, `tsconfig.json`.

Run: `cat /data1/tdcweb-dev/frontend/package.json | head -20`
Expected: `"nuxt": "^4.x.x"` in dependencies.

- [ ] **Step 3: Install base dependencies**

Run: `cd /data1/tdcweb-dev/frontend && npm install`
Expected: `node_modules/` populated, `package-lock.json` created, no errors.

- [ ] **Step 4: Smoke test the bare scaffold on port 9503**

Run: `cd /data1/tdcweb-dev/frontend && PORT=9503 npm run dev`
Expected: output contains `http://localhost:9503/` and no errors. Kill with Ctrl+C after confirming.

- [ ] **Step 5: Commit**

```bash
cd /data1/tdcweb-dev
git add frontend/
git commit -m "feat(frontend): bootstrap Nuxt 4 scaffold

Replace Vue 3 + Vite SPA scaffold with a fresh Nuxt 4 project using the
app/ layer. Previous scaffold moved to frontend.vue-backup/ (untracked,
kept locally as reference during porting). Package manager stays npm
for consistency with the existing project."
```

---

### Task 1.3: Install Nuxt modules

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`

- [ ] **Step 1: Install all Nuxt modules in one command**

Run:
```bash
cd /data1/tdcweb-dev/frontend && npm install \
  @nuxtjs/i18n \
  @pinia/nuxt pinia \
  @vueuse/nuxt @vueuse/core \
  @nuxt/image \
  @nuxtjs/tailwindcss \
  @nuxtjs/seo \
  @nuxtjs/robots \
  @nuxtjs/sitemap
```
Expected: packages added to `dependencies`, no errors.

- [ ] **Step 2: Verify installation**

Run: `cd /data1/tdcweb-dev/frontend && grep -E '"(@nuxtjs|@pinia|@vueuse|@nuxt/image)' package.json`
Expected: all nine modules listed.

- [ ] **Step 3: Commit**

```bash
cd /data1/tdcweb-dev
git add frontend/package.json frontend/package-lock.json
git commit -m "feat(frontend): install Nuxt modules (i18n, pinia, seo, image, tailwind)"
```

---

### Task 1.4: Install runtime dependencies

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`

- [ ] **Step 1: Install runtime libraries**

Run:
```bash
cd /data1/tdcweb-dev/frontend && npm install \
  gsap \
  lenis \
  @tiptap/vue-3 \
  @tiptap/starter-kit \
  @tiptap/extension-image \
  @tiptap/extension-link \
  @tiptap/extension-placeholder \
  lucide-vue-next \
  zod \
  vee-validate \
  @vee-validate/zod
```
Expected: packages added, no errors.

- [ ] **Step 2: Install dev dependencies for testing**

Run:
```bash
cd /data1/tdcweb-dev/frontend && npm install -D \
  vitest \
  @nuxt/test-utils \
  happy-dom \
  @playwright/test
```

- [ ] **Step 3: Verify**

Run: `grep -E '"(gsap|lenis|tiptap|zod|vee-validate|vitest|playwright)' /data1/tdcweb-dev/frontend/package.json`
Expected: all listed.

- [ ] **Step 4: Commit**

```bash
cd /data1/tdcweb-dev
git add frontend/package.json frontend/package-lock.json
git commit -m "feat(frontend): install runtime deps (gsap, lenis, tiptap, zod, vitest)"
```

---

## Phase 2 — Core configuration

### Task 2.1: Configure `nuxt.config.ts`

**Files:**
- Modify: `frontend/nuxt.config.ts`

- [ ] **Step 1: Replace nuxt.config.ts contents**

Write `/data1/tdcweb-dev/frontend/nuxt.config.ts`:

```typescript
export default defineNuxtConfig({
  compatibilityDate: '2026-04-01',

  future: {
    compatibilityVersion: 4,
  },

  modules: [
    '@nuxtjs/i18n',
    '@pinia/nuxt',
    '@vueuse/nuxt',
    '@nuxt/image',
    '@nuxtjs/tailwindcss',
    '@nuxtjs/seo',
    '@nuxtjs/robots',
    '@nuxtjs/sitemap',
  ],

  devtools: { enabled: true },

  css: ['~/assets/css/main.css'],

  typescript: {
    strict: true,
    typeCheck: false, // CI job only; don't slow dev HMR
  },

  runtimeConfig: {
    flaskUrl: process.env.NUXT_FLASK_URL || 'http://localhost:9502',
    cookieSecret: process.env.NUXT_COOKIE_SECRET || 'dev-insecure-change-me',
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || '/api',
      siteUrl: process.env.NUXT_PUBLIC_SITE_URL || 'http://localhost:9503',
    },
  },

  nitro: {
    devProxy: {
      '/api': {
        target: process.env.NUXT_FLASK_URL || 'http://localhost:9502',
        changeOrigin: true,
      },
    },
    prerender: {
      crawlLinks: true,
      routes: ['/sitemap.xml'],
      failOnError: false,
    },
  },

  routeRules: {
    '/':                 { prerender: true },
    '/locations':        { prerender: true },
    '/locations/**':     { prerender: true },
    '/artists':          { prerender: true },
    '/artists/**':       { prerender: true },
    '/about':            { prerender: true },
    '/contact':          { prerender: true },

    '/events':           { swr: 300 },
    '/events/**':        { swr: 300 },
    '/blog':             { swr: 3600 },
    '/blog/**':          { swr: 3600 },

    '/auth/login':       { ssr: true, swr: false },
    '/auth/register':    { ssr: true, swr: false },
    '/auth/callback/**': { ssr: true, swr: false },

    '/dashboard':        { ssr: false },
    '/dashboard/**':     { ssr: false },
    '/admin':            { ssr: false },
    '/admin/**':         { ssr: false },

    '/**':               { ssr: true },
  },

  i18n: {
    locales: [
      { code: 'en', language: 'en-US', file: 'en.json', name: 'English' },
      { code: 'it', language: 'it-IT', file: 'it.json', name: 'Italiano' },
      { code: 'fr', language: 'fr-FR', file: 'fr.json', name: 'Français' },
      { code: 'es', language: 'es-ES', file: 'es.json', name: 'Español' },
    ],
    defaultLocale: 'en',
    strategy: 'prefix_except_default',
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: 'i18n_redirected',
      redirectOn: 'root',
      alwaysRedirect: false,
    },
    lazy: true,
    langDir: 'locales',
  },

  robots: {
    disallow: ['/dashboard', '/admin', '/api/auth'],
  },

  devServer: {
    host: '0.0.0.0',
    port: 9503,
  },
})
```

- [ ] **Step 2: Start the dev server to verify config loads**

Run: `cd /data1/tdcweb-dev/frontend && npm run dev`
Expected: starts on `http://localhost:9503`, no TypeScript or config errors in stdout. Kill with Ctrl+C.

- [ ] **Step 3: Commit**

```bash
cd /data1/tdcweb-dev
git add frontend/nuxt.config.ts
git commit -m "feat(frontend): configure Nuxt 4 with routeRules, i18n, modules, dev proxy to Flask :9502"
```

---

### Task 2.2: Create `.env.example` and `.env`

**Files:**
- Create: `frontend/.env.example`
- Create: `frontend/.env`
- Modify: `frontend/.gitignore` (ensure `.env` is ignored)

- [ ] **Step 1: Write .env.example**

Write `/data1/tdcweb-dev/frontend/.env.example`:

```bash
# Flask backend URL used by Nuxt SSR (server-to-server)
NUXT_FLASK_URL=http://localhost:9502

# Cookie signing secret. Generate with: openssl rand -hex 64
NUXT_COOKIE_SECRET=change-me-in-production

# Public site URL (used for canonical links, OG, sitemap)
NUXT_PUBLIC_SITE_URL=http://localhost:9503

# API base path as seen by the browser
NUXT_PUBLIC_API_BASE=/api
```

- [ ] **Step 2: Write local .env (copy of example for now)**

Write `/data1/tdcweb-dev/frontend/.env`:

```bash
NUXT_FLASK_URL=http://localhost:9502
NUXT_COOKIE_SECRET=dev-insecure-do-not-use-in-prod
NUXT_PUBLIC_SITE_URL=http://localhost:9503
NUXT_PUBLIC_API_BASE=/api
```

- [ ] **Step 3: Verify .env is gitignored**

Run: `grep -E '^\\.env$|^\\.env\\.\\*$' /data1/tdcweb-dev/frontend/.gitignore || echo 'MISSING'`
If output is `MISSING`, append `.env` to `.gitignore`:

```bash
echo '.env' >> /data1/tdcweb-dev/frontend/.gitignore
```

Re-run: `grep -E '^\\.env' /data1/tdcweb-dev/frontend/.gitignore`
Expected: `.env` line present.

- [ ] **Step 4: Verify git does not see .env**

Run: `cd /data1/tdcweb-dev && git status frontend/.env frontend/.env.example`
Expected: `.env.example` is untracked (will be added); `.env` is ignored (no output for it from `status`).

- [ ] **Step 5: Commit**

```bash
cd /data1/tdcweb-dev
git add frontend/.env.example frontend/.gitignore
git commit -m "feat(frontend): add .env.example and gitignore .env"
```

---

### Task 2.3: Configure Tailwind with TDC theme tokens

**Files:**
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/app/assets/css/main.css`

- [ ] **Step 1: Write tailwind.config.ts**

Write `/data1/tdcweb-dev/frontend/tailwind.config.ts`:

```typescript
import type { Config } from 'tailwindcss'

export default <Config>{
  content: [
    './app/**/*.{vue,ts,tsx,js,jsx}',
    './nuxt.config.ts',
  ],
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary)',
        secondary: 'var(--color-secondary)',
        accent: 'var(--color-accent)',
        dark: 'var(--color-dark)',
      },
      backgroundImage: {
        'hero-gradient': 'var(--gradient-hero)',
      },
      fontFamily: {
        display: ['Inter', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
}
```

- [ ] **Step 2: Write app/assets/css/main.css**

Write `/data1/tdcweb-dev/frontend/app/assets/css/main.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --color-primary: #0891b2;
    --color-secondary: #06b6d4;
    --color-accent: #22c55e;
    --color-dark: #0c1222;
    --gradient-hero: linear-gradient(135deg, #0891b2, #22c55e, #eab308);
  }

  [data-location="dreamerscave"] {
    --color-primary: #0891b2;
    --color-secondary: #06b6d4;
    --color-accent: #22c55e;
    --color-dark: #0c1222;
    --gradient-hero: linear-gradient(135deg, #0891b2, #22c55e, #eab308);
  }

  html {
    @apply bg-dark text-white;
  }
  body {
    @apply font-body antialiased;
  }
}
```

- [ ] **Step 3: Restart dev server and verify Tailwind compiles**

Run: `cd /data1/tdcweb-dev/frontend && npm run dev`
Expected: no Tailwind errors in stdout. Open `http://localhost:9503` and verify the page has a dark background. Kill with Ctrl+C.

- [ ] **Step 4: Commit**

```bash
cd /data1/tdcweb-dev
git add frontend/tailwind.config.ts frontend/app/assets/css/main.css
git commit -m "feat(frontend): configure Tailwind with TDC theme tokens and location CSS vars"
```

---

### Task 2.4: Create the GSAP client-only plugin

**Files:**
- Create: `frontend/app/plugins/gsap.client.ts`

- [ ] **Step 1: Write the plugin**

Write `/data1/tdcweb-dev/frontend/app/plugins/gsap.client.ts`:

```typescript
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

export default defineNuxtPlugin(() => {
  gsap.registerPlugin(ScrollTrigger)
  return {
    provide: {
      gsap,
      ScrollTrigger,
    },
  }
})
```

- [ ] **Step 2: Verify SSR excludes the plugin**

Run: `cd /data1/tdcweb-dev/frontend && npm run dev` then `curl -s http://localhost:9503/ | grep -c 'gsap.registerPlugin'`
Expected: `0` (the client plugin body must not appear in SSR HTML). Kill dev server.

- [ ] **Step 3: Commit**

```bash
cd /data1/tdcweb-dev
git add frontend/app/plugins/gsap.client.ts
git commit -m "feat(frontend): add GSAP client-only plugin"
```

---

### Task 2.5: Create the Lenis client-only plugin

**Files:**
- Create: `frontend/app/plugins/lenis.client.ts`

- [ ] **Step 1: Write the plugin**

Write `/data1/tdcweb-dev/frontend/app/plugins/lenis.client.ts`:

```typescript
import Lenis from 'lenis'

export default defineNuxtPlugin((nuxtApp) => {
  const lenis = new Lenis({
    duration: 1.2,
    smoothWheel: true,
  })

  const { $gsap } = nuxtApp as unknown as { $gsap: typeof import('gsap').gsap }
  $gsap.ticker.add((time: number) => lenis.raf(time * 1000))
  $gsap.ticker.lagSmoothing(0)

  const router = useRouter()
  router.beforeEach((to) => {
    if (to.path.startsWith('/admin') || to.path.startsWith('/dashboard')) {
      lenis.stop()
    } else {
      lenis.start()
    }
  })

  return {
    provide: {
      lenis,
    },
  }
})
```

- [ ] **Step 2: Start dev server and confirm no runtime error**

Run: `cd /data1/tdcweb-dev/frontend && npm run dev`
Expected: no Lenis-related errors in stdout. Open `http://localhost:9503` and scroll — wheel should feel smooth. Kill dev server.

- [ ] **Step 3: Commit**

```bash
cd /data1/tdcweb-dev
git add frontend/app/plugins/lenis.client.ts
git commit -m "feat(frontend): add Lenis smooth-scroll client plugin synced with GSAP ticker"
```

---

### Task 2.6: Create the Flask client util (TDD)

**Files:**
- Create: `frontend/server/utils/flask-client.ts`
- Create: `frontend/tests/unit/flask-client.test.ts`
- Create: `frontend/vitest.config.ts`

- [ ] **Step 1: Write vitest config**

Write `/data1/tdcweb-dev/frontend/vitest.config.ts`:

```typescript
import { defineVitestConfig } from '@nuxt/test-utils/config'

export default defineVitestConfig({
  test: {
    environment: 'happy-dom',
    globals: true,
    include: ['tests/**/*.test.ts'],
  },
})
```

- [ ] **Step 2: Add test script to package.json**

Run:
```bash
cd /data1/tdcweb-dev/frontend && npm pkg set scripts.test="vitest run" && npm pkg set scripts."test:watch"="vitest"
```

- [ ] **Step 3: Write the failing test**

Write `/data1/tdcweb-dev/frontend/tests/unit/flask-client.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { H3Event } from 'h3'

// Mock $fetch and useRuntimeConfig before importing flask-client
const fetchMock = vi.fn()
;(globalThis as any).$fetch = fetchMock
;(globalThis as any).useRuntimeConfig = () => ({ flaskUrl: 'http://flask.test' })

import { flaskFetch } from '../../server/utils/flask-client'

describe('flaskFetch', () => {
  beforeEach(() => {
    fetchMock.mockReset()
    fetchMock.mockResolvedValue({ ok: true })
  })

  it('forwards the flaskHeaders from event.context', async () => {
    const event = {
      context: { flaskHeaders: { Authorization: 'Bearer token123' } },
    } as unknown as H3Event

    await flaskFetch('/api/user/favorites', event)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/user/favorites',
      expect.objectContaining({
        baseURL: 'http://flask.test',
        headers: expect.objectContaining({ Authorization: 'Bearer token123' }),
      }),
    )
  })

  it('works when event.context.flaskHeaders is missing', async () => {
    const event = { context: {} } as unknown as H3Event

    await flaskFetch('/api/locations', event)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/locations',
      expect.objectContaining({ baseURL: 'http://flask.test' }),
    )
  })

  it('caller-provided headers override flaskHeaders on key conflict', async () => {
    const event = {
      context: { flaskHeaders: { Authorization: 'Bearer old' } },
    } as unknown as H3Event

    await flaskFetch('/api/x', event, { headers: { Authorization: 'Bearer new' } })

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/x',
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer new' }),
      }),
    )
  })
})
```

- [ ] **Step 4: Run the test to verify it fails**

Run: `cd /data1/tdcweb-dev/frontend && npm test`
Expected: test fails with "Cannot find module '../../server/utils/flask-client'" or equivalent.

- [ ] **Step 5: Implement flask-client.ts**

Write `/data1/tdcweb-dev/frontend/server/utils/flask-client.ts`:

```typescript
import type { H3Event } from 'h3'

export const flaskFetch = <T = unknown>(
  url: string,
  event: H3Event,
  options: Parameters<typeof $fetch<T>>[1] = {},
): Promise<T> => {
  const { flaskUrl } = useRuntimeConfig()
  const flaskHeaders = (event.context.flaskHeaders ?? {}) as Record<string, string>
  return $fetch<T>(url, {
    baseURL: flaskUrl,
    ...options,
    headers: { ...flaskHeaders, ...(options.headers ?? {}) },
  })
}
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `cd /data1/tdcweb-dev/frontend && npm test`
Expected: 3 tests pass.

- [ ] **Step 7: Commit**

```bash
cd /data1/tdcweb-dev
git add frontend/server/utils/flask-client.ts frontend/tests/unit/flask-client.test.ts frontend/vitest.config.ts frontend/package.json frontend/package-lock.json
git commit -m "feat(frontend): add flaskFetch server util with tests (event.context.flaskHeaders forwarding)"
```

---

### Task 2.7: Create the auth-forward server middleware (TDD)

**Files:**
- Create: `frontend/server/middleware/auth-forward.ts`
- Create: `frontend/tests/unit/auth-forward.test.ts`

- [ ] **Step 1: Write the failing test**

Write `/data1/tdcweb-dev/frontend/tests/unit/auth-forward.test.ts`:

```typescript
import { describe, it, expect, vi } from 'vitest'
import type { H3Event } from 'h3'

const getCookieMock = vi.fn()
;(globalThis as any).getCookie = getCookieMock
;(globalThis as any).defineEventHandler = (handler: any) => handler

import authForward from '../../server/middleware/auth-forward'

describe('auth-forward middleware', () => {
  it('sets Authorization header when tdc_access cookie exists', async () => {
    getCookieMock.mockReturnValue('jwt-access-token')
    const event = { context: {} } as unknown as H3Event

    await authForward(event)

    expect(event.context.flaskHeaders).toEqual({
      Authorization: 'Bearer jwt-access-token',
    })
  })

  it('does not set flaskHeaders when cookie is missing', async () => {
    getCookieMock.mockReturnValue(undefined)
    const event = { context: {} } as unknown as H3Event

    await authForward(event)

    expect(event.context.flaskHeaders).toBeUndefined()
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd /data1/tdcweb-dev/frontend && npm test -- auth-forward`
Expected: test fails with "Cannot find module '../../server/middleware/auth-forward'".

- [ ] **Step 3: Implement the middleware**

Write `/data1/tdcweb-dev/frontend/server/middleware/auth-forward.ts`:

```typescript
export default defineEventHandler(async (event) => {
  const access = getCookie(event, 'tdc_access')
  if (access) {
    event.context.flaskHeaders = { Authorization: `Bearer ${access}` }
  }
})
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd /data1/tdcweb-dev/frontend && npm test -- auth-forward`
Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
cd /data1/tdcweb-dev
git add frontend/server/middleware/auth-forward.ts frontend/tests/unit/auth-forward.test.ts
git commit -m "feat(frontend): add auth-forward server middleware with tests"
```

---

### Task 2.8: Create the cookies helper

**Files:**
- Create: `frontend/server/utils/cookies.ts`

- [ ] **Step 1: Write the helper**

Write `/data1/tdcweb-dev/frontend/server/utils/cookies.ts`:

```typescript
import type { H3Event, CookieSerializeOptions } from 'h3'

const ACCESS_COOKIE = 'tdc_access'
const REFRESH_COOKIE = 'tdc_refresh'

const isProd = () => process.env.NODE_ENV === 'production'

export const setAccessCookie = (event: H3Event, token: string) => {
  setCookie(event, ACCESS_COOKIE, token, {
    httpOnly: true,
    secure: isProd(),
    sameSite: 'lax',
    path: '/',
    maxAge: 900, // 15 min
  } satisfies CookieSerializeOptions)
}

export const setRefreshCookie = (event: H3Event, token: string) => {
  setCookie(event, REFRESH_COOKIE, token, {
    httpOnly: true,
    secure: isProd(),
    sameSite: 'strict',
    path: '/api/auth',
    maxAge: 604800, // 7 days
  } satisfies CookieSerializeOptions)
}

export const clearAuthCookies = (event: H3Event) => {
  deleteCookie(event, ACCESS_COOKIE, { path: '/' })
  deleteCookie(event, REFRESH_COOKIE, { path: '/api/auth' })
}

export const getRefreshToken = (event: H3Event): string | undefined =>
  getCookie(event, REFRESH_COOKIE)
```

- [ ] **Step 2: Commit**

```bash
cd /data1/tdcweb-dev
git add frontend/server/utils/cookies.ts
git commit -m "feat(frontend): add HttpOnly auth cookie helpers (tdc_access 15min, tdc_refresh 7d)"
```

---

### Task 2.9: Create base shared TypeScript types

**Files:**
- Create: `frontend/app/types/api.ts`
- Create: `frontend/app/types/user.ts`
- Create: `frontend/app/types/location.ts`
- Create: `frontend/app/types/event.ts`

- [ ] **Step 1: Write types/api.ts**

Write `/data1/tdcweb-dev/frontend/app/types/api.ts`:

```typescript
export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

export interface ApiResponse<T> {
  data: T
  meta?: {
    page?: number
    perPage?: number
    total?: number
  }
}
```

- [ ] **Step 2: Write types/user.ts**

Write `/data1/tdcweb-dev/frontend/app/types/user.ts`:

```typescript
export type UserRole = 'user' | 'staff' | 'admin'

export interface User {
  id: number
  email: string
  username: string
  avatar_name: string | null
  role: UserRole
  language: string
  email_verified: boolean
  email_notifications: boolean
  created_at: string
  last_login: string | null
}

export interface AuthResponse {
  user: User
}
```

- [ ] **Step 3: Write types/location.ts**

Write `/data1/tdcweb-dev/frontend/app/types/location.ts`:

```typescript
export type LocationMood = 'cosmic' | 'hybrid' | 'warm'

export interface Location {
  id: number
  slug: string
  name: string
  mood: LocationMood
  capacity: number
  hero_image: string | null
  description: string | null
  created_at: string
}
```

- [ ] **Step 4: Write types/event.ts**

Write `/data1/tdcweb-dev/frontend/app/types/event.ts`:

```typescript
export type EventStatus = 'draft' | 'scheduled' | 'live' | 'ended' | 'cancelled'

export interface Event {
  id: number
  slug: string
  title: string
  location_id: number
  starts_at: string
  ends_at: string
  status: EventStatus
  description: string | null
  poster_image: string | null
}
```

- [ ] **Step 5: Commit**

```bash
cd /data1/tdcweb-dev
git add frontend/app/types/
git commit -m "feat(frontend): add shared TypeScript types (api, user, location, event)"
```

---

## Phase 3 — Port existing files

> **Phase-3 execution note.** All tasks below carry plan-authored
> `git commit` blocks; during the actual Phase 3 run those commits
> were **deferred** per CLAUDE.md rule 15 (no per-task commits). The
> working tree accumulated across all tasks and was committed atomically
> at phase end (rule 16). Treat the commit snippets as historical intent
> only — not as instructions for any future subagent. The amendments
> below capture the final shape of each deliverable; earlier drafts of
> the same tasks in this plan are superseded inline.

### Task 3.0: Preemptive rewrite of `flask-client.ts` (TD-009 close-out)

**Files:**
- Modify: `frontend/server/utils/flask-client.ts` (Phase 2 deliverable, rewritten)
- Modify: `frontend/tests/unit/flask-client.test.ts` (extend to cover fallback + error paths)

Inserted at the start of Phase 3, before Task 3.1. User-approved option
(A) for TD-009 on 2026-04-24: preemptive resilient-pattern rewrite
instead of waiting for a real Phase 4 SSR hit to surface the latent
globalThis-only flaw.

The Phase 2 implementation read `$fetch` and `useRuntimeConfig`
exclusively from `globalThis`. Task 2.7 had already proven that Nitro
does not universally expose h3 helpers on `globalThis` (`getCookie`
lives as a regular module binding), so the same risk applied to
`$fetch` and `useRuntimeConfig` in the prod bundle. Task 3.0 adopts
the resilient pattern used by `auth-forward.ts` and `cookies.ts`:
stub-first from `globalThis`, explicit fallback otherwise.

- [x] **Step 1: Rewrite the util**

The production shape:

```typescript
// frontend/server/utils/flask-client.ts
import type { H3Event } from 'h3'
import { $fetch as ofetchImpl } from 'ofetch'

type FetchFn = typeof $fetch
type RuntimeConfigFn = () => { flaskUrl: string } & Record<string, unknown>

const resolveFetch = (): FetchFn => {
  const stubbed = (globalThis as unknown as { $fetch?: FetchFn }).$fetch
  return stubbed ?? (ofetchImpl as unknown as FetchFn)
}

const resolveRuntimeConfig = (): ReturnType<RuntimeConfigFn> => {
  const stubbed = (globalThis as unknown as { useRuntimeConfig?: RuntimeConfigFn })
    .useRuntimeConfig
  if (!stubbed) {
    throw new Error(
      'flaskFetch: useRuntimeConfig is not available on globalThis; ' +
        'flaskFetch must be called from a Nitro server route where ' +
        'runtime config is bound',
    )
  }
  return stubbed()
}

export const flaskFetch = <T = unknown>(
  url: string,
  event: H3Event,
  options: Parameters<typeof $fetch<T>>[1] = {},
): Promise<T> => {
  const { flaskUrl } = resolveRuntimeConfig()
  const flaskHeaders = (event.context.flaskHeaders ?? {}) as Record<string, string>
  return resolveFetch()<T>(url, {
    baseURL: flaskUrl,
    ...options,
    headers: { ...flaskHeaders, ...(options.headers ?? {}) },
  }) as Promise<T>
}
```

Rationale: `$fetch` has a clean module fallback (`ofetch` publishes
`$fetch` as a named export identical to Nitro's auto-import).
`useRuntimeConfig` has no clean module fallback — the function only
exists inside a bound Nitro context — so a missing binding is an
explicit thrown Error, not a silent fallback.

- [x] **Step 2: Extend the test**

Unit test `tests/unit/flask-client.test.ts` grows from 3 to 8
assertions. New suites:

- `describe('fallback: ofetch is used when globalThis.$fetch is absent')`
  — deletes the globalThis stub, asserts the `ofetch` mock is invoked
  with the expected baseURL + headers.
- `describe('error: explicit failure when globalThis.useRuntimeConfig
  is absent')` — deletes the globalThis stub, asserts
  `flaskFetch(...)` throws with the typed error message.

The pre-existing 3 happy-path assertions continue to use globalThis
stubs (stub-first path).

- [x] **Step 3: Close TD-009**

Upon Phase 3 atomic commit landing, move TD-009 to "Closed items" in
`docs/TECH_DEBT.md` with the resolving SHA.

**No separate commit** — changes land in the Phase 3 atomic commit.

---

### Task 3.1: Port `App.vue` → `app/app.vue`

**Files:**
- Modify: `frontend/app/app.vue` (overwrite the scaffold default)

- [ ] **Step 1: Read the original App.vue**

Run: `cat /data1/tdcweb-dev/frontend.vue-backup/src/App.vue`
Note the template/script contents (likely a minimal `<NuxtPage />` or `<router-view />` host). Adapt for Nuxt.

- [ ] **Step 2: Write app/app.vue**

Write `/data1/tdcweb-dev/frontend/app/app.vue`:

```vue
<script setup lang="ts">
useHead({
  titleTemplate: (title) => (title ? `${title} — The Dreamer's Cave` : `The Dreamer's Cave — You Can See The Music`),
  htmlAttrs: { lang: 'en' },
  link: [{ rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }],
})

useSeoMeta({
  ogSiteName: "The Dreamer's Cave",
  twitterCard: 'summary_large_image',
})
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
```

**Phase 3 amendment.** The original draft referenced
`/favicon.svg`, which does not yet exist under `frontend/public/`. The
phase-end fix switched the href to `/favicon.ico` (shipped by the
Nuxt scaffold). Reintroducing an SVG favicon is deferred to a future
brand-assets task.

- [ ] **Step 3: Dev server smoke test**

Run: `cd /data1/tdcweb-dev/frontend && npm run dev` → open `http://localhost:9503` → expect no hydration errors. Kill.

- [ ] **Step 4: Commit deferred**

Per CLAUDE.md rule 15, no per-task commit. Changes accumulate in the
working tree until the Phase 3 atomic commit.

---

### Task 3.2: Create default layout and error page

**Files:**
- Create: `frontend/app/layouts/default.vue`
- Create: `frontend/app/error.vue`

- [ ] **Step 1: Write layouts/default.vue**

Write `/data1/tdcweb-dev/frontend/app/layouts/default.vue`:

```vue
<template>
  <div class="min-h-screen flex flex-col">
    <AppHeader />
    <main class="flex-1">
      <slot />
    </main>
    <AppFooter />
  </div>
</template>
```

- [ ] **Step 2: Write error.vue**

Write `/data1/tdcweb-dev/frontend/app/error.vue`:

```vue
<script setup lang="ts">
import type { NuxtError } from '#app'

defineProps<{ error: NuxtError }>()
const handleError = () => clearError({ redirect: '/' })
</script>

<template>
  <main class="min-h-screen flex items-center justify-center bg-dark text-white">
    <div class="text-center px-6" role="alert">
      <h1 class="text-6xl font-display font-bold mb-4">{{ error.statusCode }}</h1>
      <p class="text-xl mb-8">{{ error.statusMessage || $t('errors.message_fallback') }}</p>
      <button
        class="px-6 py-3 bg-primary hover:bg-secondary rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-dark focus-visible:outline-none"
        @click="handleError"
      >
        {{ $t('errors.back_to_home') }}
      </button>
    </div>
  </main>
</template>
```

**Phase 3 amendment (Task 3.2b polish pass).** The original draft used
a `<div>` root with English literals and no accessibility landmarks.
Post-review fixes:
- Root switched to `<main>` (page landmark, one per document — this
  is the global error page, not nested inside the default layout).
- `role="alert"` on the inner container so screen readers announce the
  error as a live region.
- Copy bound to `$t('errors.message_fallback')` / `$t('errors.back_to_home')`
  across EN/IT/FR/ES (keys seeded in Task 3.4 Steps 2-5).
- Focus-visible ring on the CTA per the pattern-library checklist
  (playbook §23.1 point 6).

- [ ] **Step 3: Commit deferred**

Per CLAUDE.md rule 15, no per-task commit — changes accumulate in the
working tree until the Phase 3 atomic commit.

---

### Task 3.3: Port AppHeader and AppFooter

**Files:**
- Create: `frontend/app/components/common/AppHeader.vue`
- Create: `frontend/app/components/common/AppFooter.vue`

- [ ] **Step 1: Read existing AppHeader.vue**

Run: `cat /data1/tdcweb-dev/frontend.vue-backup/src/components/common/AppHeader.vue`
Inspect the original markup. Port visuals/classes as-is; replace `vue-router`'s `<router-link>` with `<NuxtLink>` and any vue-i18n `$t` with auto-imported `useI18n()`'s `t` / or `$t` (Nuxt i18n auto-provides).

- [ ] **Step 2: Write app/components/common/AppHeader.vue**

Write `/data1/tdcweb-dev/frontend/app/components/common/AppHeader.vue`:

```vue
<script setup lang="ts">
const localePath = useLocalePath()
const { locales, locale, setLocale } = useI18n()

const availableLocales = computed(() =>
  (locales.value as { code: string; name: string }[]).filter(l => l.code !== locale.value),
)
</script>

<template>
  <header class="sticky top-0 z-40 bg-dark/90 backdrop-blur border-b border-white/10">
    <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
      <NuxtLink :to="localePath('/')" class="text-2xl font-display font-bold">
        The Dreamer's Cave
      </NuxtLink>

      <nav class="hidden md:flex items-center gap-8">
        <NuxtLink :to="localePath('/locations')" class="hover:text-primary transition-colors" active-class="text-primary font-bold">{{ $t('nav.locations') }}</NuxtLink>
        <NuxtLink :to="localePath('/events')" class="hover:text-primary transition-colors" active-class="text-primary font-bold">{{ $t('nav.events') }}</NuxtLink>
        <NuxtLink :to="localePath('/artists')" class="hover:text-primary transition-colors" active-class="text-primary font-bold">{{ $t('nav.artists') }}</NuxtLink>
        <NuxtLink :to="localePath('/blog')" class="hover:text-primary transition-colors" active-class="text-primary font-bold">{{ $t('nav.blog') }}</NuxtLink>
      </nav>

      <div class="flex items-center gap-4">
        <select
          :value="locale"
          class="bg-transparent border border-white/20 rounded px-2 py-1 text-sm"
          @change="(e) => setLocale((e.target as HTMLSelectElement).value as typeof locale)"
        >
          <option :value="locale">{{ locale.toUpperCase() }}</option>
          <option v-for="l in availableLocales" :key="l.code" :value="l.code">
            {{ l.code.toUpperCase() }}
          </option>
        </select>

        <NuxtLink
          :to="localePath('/auth/login')"
          class="px-4 py-2 border border-primary text-primary hover:bg-primary hover:text-white rounded transition-colors text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-dark"
        >
          {{ $t('nav.login') }}
        </NuxtLink>
      </div>
    </div>
  </header>
</template>
```

**Phase 3 amendments (Tasks 3.3, 3.3b, phase-end micro-edits).**

- **Login button: outline style.** The original draft used filled
  `bg-primary hover:bg-secondary + text-white`. Task 3.3b design-system
  review flagged WCAG AA contrast failures on 5/8 palettes. User chose
  option (iii) — outline with `border-primary text-primary` resting,
  filled on hover. Outline passes AA on 7/8 palettes; jazzclub is the
  only regression (TD-011).
- **Nav hover + active differentiation.** Each nav `NuxtLink` gained
  `hover:text-primary transition-colors` and
  `active-class="text-primary font-bold"`. The `font-bold` on active
  (not just colour) resolves the hover/active visual collision caught
  in scan row 36 — on `/events` hovering `/locations` now shows active
  bold + primary vs hover non-bold + primary.
- **Focus-visible ring on login CTA.** Pattern-library §23.1 point 6
  chain: 5 `focus-visible:*` classes.
- **Type narrowing on setLocale.** The `@change` handler casts the
  target value to `typeof locale` (not `typeof locale.value`); in Vue
  templates `locale` from `useI18n()` auto-unwraps the ref, so the
  template-level type is `string`, not `Ref<string>`. F1 HIGH fix from
  typecheck batch (scan row 40).

- [ ] **Step 3: Write app/components/common/AppFooter.vue**

Write `/data1/tdcweb-dev/frontend/app/components/common/AppFooter.vue`:

```vue
<script setup lang="ts">
// Computed at script-setup time (both SSR and client). On the server
// this runs at request time; on the client it runs at hydration time.
// For the overwhelming majority of the year the two agree. The
// 1-second window at midnight on 31 Dec -> 1 Jan where they could
// differ is an accepted edge per CLAUDE.md SSR Rule #4 discussion;
// fixing requires either app-config hardcoding (yearly maintenance)
// or a build-time constant baked in.
const year = new Date().getFullYear()
</script>

<template>
  <footer class="border-t border-white/10 bg-dark">
    <div class="max-w-7xl mx-auto px-6 py-8 text-sm text-white/70">
      <div class="flex flex-col md:flex-row justify-between gap-4">
        <div>© {{ year }} The Dreamer's Cave</div>
        <div class="italic">{{ $t('home.hero_title') }}</div>
      </div>
    </div>
  </footer>
</template>
```

**Phase 3 amendments.**

- **Year hoisted to `<script setup>`.** The original draft used
  `{{ new Date().getFullYear() }}` inline in the template with a note
  claiming "stable across SSR and hydration". **CLAUDE.md SSR Rule #4
  is NON-NEGOTIABLE** — `new Date()` in templates is forbidden. The
  year is computed once in script-setup and interpolated as a plain
  string. SSR HTML is byte-identical to the original intent.
- **Motto via i18n.** The literal "You Can See The Music" was
  replaced with `$t('home.hero_title')`. Since the hero title is
  identical to the motto in every locale, AppFooter reuses the existing
  key instead of duplicating strings under a `common.motto` namespace
  (pragmatic DRY; if divergence between hero title and footer motto
  emerges, extract to `common.motto` then).

- [ ] **Step 4: Commit deferred**

Per CLAUDE.md rule 15, no per-task commit — changes accumulate in the
working tree until the Phase 3 atomic commit.

---

### Task 3.4: Port the i18n locale JSON files

**Files:**
- Create: `frontend/i18n/locales/en.json`
- Create: `frontend/i18n/locales/it.json`
- Create: `frontend/i18n/locales/fr.json`
- Create: `frontend/i18n/locales/es.json`

- [ ] **Step 1: Inspect the backup locales**

Run: `ls /data1/tdcweb-dev/frontend.vue-backup/src/i18n/ 2>&1 || echo 'no backup locales'`
If files exist, copy their JSON contents. If not, use the minimal seeds below.

- [ ] **Step 2: Write i18n/locales/en.json**

Write `/data1/tdcweb-dev/frontend/i18n/locales/en.json`:

```json
{
  "nav": {
    "locations": "Locations",
    "events": "Events",
    "artists": "Artists",
    "blog": "Blog",
    "login": "Sign in"
  },
  "home": {
    "hero_title": "You Can See The Music",
    "hero_subtitle": "A virtual music club in Second Life",
    "seo": {
      "description": "A virtual music club in Second Life: 10 themed venues, live music, immersive events.",
      "og_description": "Virtual music club in Second Life since 2019"
    }
  },
  "locations": {
    "title": "Locations",
    "empty": "No locations available",
    "seo": {
      "description": "Discover the 10 themed venues of The Dreamer's Cave in Second Life."
    },
    "error": {
      "load_failed": "Could not load locations"
    }
  },
  "events": {
    "title": "Events",
    "empty": "No upcoming events",
    "seo": {
      "description": "Upcoming live music events at The Dreamer's Cave."
    },
    "error": {
      "load_failed": "Could not load events"
    }
  },
  "errors": {
    "message_fallback": "Something went wrong",
    "back_to_home": "Back to home"
  }
}
```

- [ ] **Step 3: Write i18n/locales/it.json**

Write `/data1/tdcweb-dev/frontend/i18n/locales/it.json`:

```json
{
  "nav": {
    "locations": "Location",
    "events": "Eventi",
    "artists": "Artisti",
    "blog": "Blog",
    "login": "Accedi"
  },
  "home": {
    "hero_title": "Puoi vedere la musica",
    "hero_subtitle": "Un music club virtuale in Second Life",
    "seo": {
      "description": "Un music club virtuale in Second Life: 10 venue a tema, musica dal vivo, eventi immersivi.",
      "og_description": "Music club virtuale in Second Life dal 2019"
    }
  },
  "locations": {
    "title": "Location",
    "empty": "Nessuna location disponibile",
    "seo": {
      "description": "Scopri le 10 venue a tema del The Dreamer's Cave in Second Life."
    },
    "error": {
      "load_failed": "Impossibile caricare le location"
    }
  },
  "events": {
    "title": "Eventi",
    "empty": "Nessun evento in programma",
    "seo": {
      "description": "Eventi musicali dal vivo in programma al The Dreamer's Cave."
    },
    "error": {
      "load_failed": "Impossibile caricare gli eventi"
    }
  },
  "errors": {
    "message_fallback": "Qualcosa è andato storto",
    "back_to_home": "Torna alla home"
  }
}
```

- [ ] **Step 4: Write i18n/locales/fr.json**

Write `/data1/tdcweb-dev/frontend/i18n/locales/fr.json`:

```json
{
  "nav": {
    "locations": "Lieux",
    "events": "Événements",
    "artists": "Artistes",
    "blog": "Blog",
    "login": "Se connecter"
  },
  "home": {
    "hero_title": "Vous pouvez voir la musique",
    "hero_subtitle": "Un club de musique virtuel dans Second Life",
    "seo": {
      "description": "Un club de musique virtuel dans Second Life : 10 lieux thématiques, musique live, événements immersifs.",
      "og_description": "Club de musique virtuel dans Second Life depuis 2019"
    }
  },
  "locations": {
    "title": "Lieux",
    "empty": "Aucun lieu disponible",
    "seo": {
      "description": "Découvrez les 10 lieux thématiques de The Dreamer's Cave dans Second Life."
    },
    "error": {
      "load_failed": "Impossible de charger les lieux"
    }
  },
  "events": {
    "title": "Événements",
    "empty": "Aucun événement à venir",
    "seo": {
      "description": "Événements musicaux live à venir au The Dreamer's Cave."
    },
    "error": {
      "load_failed": "Impossible de charger les événements"
    }
  },
  "errors": {
    "message_fallback": "Une erreur est survenue",
    "back_to_home": "Retour à l'accueil"
  }
}
```

- [ ] **Step 5: Write i18n/locales/es.json**

Write `/data1/tdcweb-dev/frontend/i18n/locales/es.json`:

```json
{
  "nav": {
    "locations": "Lugares",
    "events": "Eventos",
    "artists": "Artistas",
    "blog": "Blog",
    "login": "Iniciar sesión"
  },
  "home": {
    "hero_title": "Puedes ver la música",
    "hero_subtitle": "Un club de música virtual en Second Life",
    "seo": {
      "description": "Un club de música virtual en Second Life: 10 sedes temáticas, música en vivo, eventos inmersivos.",
      "og_description": "Club de música virtual en Second Life desde 2019"
    }
  },
  "locations": {
    "title": "Lugares",
    "empty": "No hay lugares disponibles",
    "seo": {
      "description": "Descubre los 10 lugares temáticos de The Dreamer's Cave en Second Life."
    },
    "error": {
      "load_failed": "No se pudieron cargar los lugares"
    }
  },
  "events": {
    "title": "Eventos",
    "empty": "No hay eventos próximos",
    "seo": {
      "description": "Próximos eventos de música en vivo en The Dreamer's Cave."
    },
    "error": {
      "load_failed": "No se pudieron cargar los eventos"
    }
  },
  "errors": {
    "message_fallback": "Algo salió mal",
    "back_to_home": "Volver al inicio"
  }
}
```

- [ ] **Step 6: Commit deferred**

Per CLAUDE.md rule 15, no per-task commit — changes accumulate in the
working tree until the Phase 3 atomic commit.

**Phase 3 amendments.** Steps 2-5 of this task were amended mid-phase
(controller-level pre-flight edits, 2026-04-24) to add the `home.seo.*`,
`errors.*`, `locations.*`, and `events.*` namespaces in all 4 locales.
Task 3.2b, 3.5b, 3.6b, and 3.7 consumed those keys. Final shape: 9
namespaces × 4 locales = 36 translations landed in Phase 3. See
`frontend/i18n/locales/{en,it,fr,es}.json` for the merged state.

---

### Task 3.5: Port the home page (`pages/index.vue`)

**Files:**
- Create: `frontend/app/pages/index.vue`

- [ ] **Step 1: Inspect the backup HomePage**

Run: `cat /data1/tdcweb-dev/frontend.vue-backup/src/views/HomePage.vue`
Port the visual content as-is, swap Vue Router directives (`router-link` → `NuxtLink`).

- [ ] **Step 2: Write app/pages/index.vue**

Write `/data1/tdcweb-dev/frontend/app/pages/index.vue`:

```vue
<script setup lang="ts">
const { t } = useI18n()

useSeoMeta({
  title: t('home.hero_title'),
  description: t('home.seo.description'),
  ogTitle: 'The Dreamer\'s Cave',
  ogDescription: t('home.seo.og_description'),
  ogType: 'website',
})
</script>

<template>
  <section class="relative min-h-screen flex items-center justify-center bg-hero-gradient">
    <div class="absolute inset-0 bg-dark/40 pointer-events-none" aria-hidden="true"></div>
    <div class="relative text-center px-6">
      <h1 class="text-6xl md:text-8xl font-display font-bold mb-6">
        {{ t('home.hero_title') }}
      </h1>
      <p class="text-2xl text-white/80">
        {{ t('home.hero_subtitle') }}
      </p>
    </div>
  </section>
</template>
```

**Phase 3 amendments (Task 3.5b + phase-end subtitle micro-edit).**

- **SEO meta via i18n.** The original draft hardcoded English in
  `useSeoMeta`. Per scan row 20, user approved option (X): add
  `home.seo.description` + `home.seo.og_description` to all 4 locales
  (done in Task 3.4) + bind `useSeoMeta` through `t(...)`. `ogTitle`
  stays literal `"The Dreamer's Cave"` — brand-integrity.
- **Dark scrim over hero gradient.** Task 3.5 design-system reviewer
  finding F1 [HIGH]: white hero text on `bg-hero-gradient` failed
  WCAG AA contrast on 5/8 palettes (dreamerscave, dreamvision,
  noahsark, livemagic, jazzclub). User approved option (1): dark
  scrim. Added `absolute inset-0 bg-dark/40 pointer-events-none
  aria-hidden="true"` scrim div behind content, repositioned
  content wrapper with `relative z-10`. Wrapper `<section>` now
  has `relative` so the scrim establishes the stacking context.
- **Subtitle upgraded to `text-2xl`.** Phase 3 micro-edit (scan row
  21). Original `text-xl md:text-2xl` (20px at mobile) still failed
  AA-normal on yellow-biased palettes even after the 40% scrim.
  `text-2xl` (24px) qualifies AA-large (3:1), which passes for all
  8 palettes post-scrim. One-word removal (`text-xl md:` dropped).

- [ ] **Step 3: SSR verification**

Run:
```bash
cd /data1/tdcweb-dev/frontend && npm run dev &
sleep 3
curl -s http://localhost:9503/ | grep -c 'You Can See The Music'
kill %1
```
Expected: `>= 1` (title present in SSR HTML).

- [ ] **Step 4: Commit deferred**

Per CLAUDE.md rule 15, no per-task commit — changes accumulate in the
working tree until the Phase 3 atomic commit.

---

### Task 3.6: Port locations list page

**Files:**
- Create: `frontend/app/pages/locations/index.vue`

- [ ] **Step 1: Write app/pages/locations/index.vue**

Write `/data1/tdcweb-dev/frontend/app/pages/locations/index.vue`:

```vue
<script setup lang="ts">
import type { Location } from '~/types/location'

const { t } = useI18n()
const localePath = useLocalePath()

const { data: locations, error } = await useFetch<Location[]>('/api/locations', {
  key: 'locations-list',
})

useSeoMeta({
  title: t('locations.title'),
  description: t('locations.seo.description'),
})
</script>

<template>
  <section class="max-w-7xl mx-auto px-6 py-16">
    <h1 class="text-5xl font-display font-bold mb-12">{{ t('locations.title') }}</h1>

    <div v-if="error" role="alert" class="text-error">
      {{ t('locations.error.load_failed') }}: {{ error.statusMessage }}
    </div>

    <div v-else-if="locations && locations.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <article
        v-for="location in locations"
        :key="location.id"
        class="border border-white/10 rounded-lg overflow-hidden hover:border-primary transition-colors"
      >
        <NuxtLink
          :to="localePath(`/locations/${location.slug}`)"
          class="block p-6 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-dark"
        >
          <h2 class="text-2xl font-display font-bold mb-2">{{ location.name }}</h2>
          <p v-if="location.description" class="text-white/70">{{ location.description }}</p>
        </NuxtLink>
      </article>
    </div>

    <div v-else class="text-white/70">
      {{ t('locations.empty') }}
    </div>
  </section>
</template>
```

**Phase 3 amendments (Task 3.6b polish pass + phase-end micro-edits).**

- **i18n throughout.** `useSeoMeta`, `<h1>`, the error message, and the
  empty state all bind through `t('locations.*')`. Keys seeded in Task
  3.4.
- **Semantic error token.** `text-red-400` replaced with `text-error`
  (`--color-error` token, added in the same Task 3.6b per §14.5
  playbook semantic-token pattern).
- **Three-state template.** `v-if="error"` → `v-else-if="locations && locations.length"`
  → `v-else` (empty). The original draft had no empty-state branch.
- **Null-guard description.** `<p v-if="location.description">` avoids
  rendering an empty paragraph for locations with no description.
- **`useLocalePath()` wrap on NuxtLink.** Controller micro-edit (scan
  row 25). Without it, IT/FR/ES deep links would strip their locale
  prefix (functional i18n bug caught by design-system reviewer).
- **`role="alert"` on error branch.** Phase-end micro-edit (scan row
  45). Screen-reader live-region announcement, consistent with
  `error.vue`.
- **Focus-visible ring on card link.** Pattern-library §23.1 point 6.

- [ ] **Step 2: Commit deferred**

Per CLAUDE.md rule 15, no per-task commit — changes accumulate in the
working tree until the Phase 3 atomic commit.

---

### Task 3.7: Port events list page

**Files:**
- Create: `frontend/app/pages/events/index.vue`

- [ ] **Step 1: Write app/pages/events/index.vue**

Write `/data1/tdcweb-dev/frontend/app/pages/events/index.vue`:

```vue
<script setup lang="ts">
import type { Event } from '~/types/event'

const { t } = useI18n()

const { data: events, error } = await useFetch<Event[]>('/api/events', {
  key: 'events-list',
  query: { upcoming: 'true' },
})

useSeoMeta({
  title: t('events.title'),
  description: t('events.seo.description'),
})
</script>

<template>
  <section class="max-w-7xl mx-auto px-6 py-16">
    <h1 class="text-5xl font-display font-bold mb-12">{{ t('events.title') }}</h1>

    <div v-if="error" role="alert" class="text-error">
      {{ t('events.error.load_failed') }}: {{ error.statusMessage }}
    </div>

    <ul v-else-if="events && events.length" class="space-y-4">
      <li
        v-for="event in events"
        :key="event.id"
        class="border border-white/10 rounded-lg p-6"
      >
        <h2 class="text-2xl font-display font-bold mb-1">{{ event.title }}</h2>
        <time :datetime="event.starts_at" class="text-white/60 text-sm">{{ event.starts_at }}</time>
      </li>
    </ul>

    <div v-else class="text-white/70">
      {{ t('events.empty') }}
    </div>
  </section>
</template>
```

**Phase 3 amendments (Task 3.7 preemptive polish + phase-end micro-edit).**

Task 3.7 was the first task to ship the full preemptive-polish
pattern (playbook §23.1). Design-system reviewer flagged zero blocking
findings. Delta vs the original draft:

- **i18n everywhere.** `useSeoMeta`, `<h1>`, error, empty all via
  `t('events.*')`.
- **`text-error` + `role="alert"`.** `role="alert"` added as a
  phase-end micro-edit (scan row 45) for consistency with
  locations + error.vue.
- **Empty-state branch.** `v-else` with `t('events.empty')`.
- **`<time :datetime="...">` machine-readable.** Raw ISO 8601 is both
  the visible text and the `datetime` attribute. Developer-shaped;
  user-friendly formatting deferred to `useFormattedDate` (TD-012).

- [ ] **Step 2: Commit deferred**

Per CLAUDE.md rule 15, no per-task commit — changes accumulate in the
working tree until the Phase 3 atomic commit.

---

### Task 3.8: Port the `useApi` composable (TDD)

**Files:**
- Create: `frontend/app/composables/useApi.ts`
- Create: `frontend/tests/unit/useApi.test.ts`

- [ ] **Step 1: Write the failing test**

Write `/data1/tdcweb-dev/frontend/tests/unit/useApi.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { FetchContext } from 'ofetch'

const createMock = vi.fn()
;(globalThis as unknown as { $fetch: { create: typeof createMock } }).$fetch = { create: createMock }

import { useApi, type RetryableFetchOptions } from '../../app/composables/useApi'

describe('useApi', () => {
  beforeEach(() => {
    createMock.mockReset()
    createMock.mockReturnValue(vi.fn())
  })

  it('creates a $fetch instance with credentials: include', () => {
    useApi()
    expect(createMock).toHaveBeenCalledWith(
      expect.objectContaining({
        credentials: 'include',
      }),
    )
  })

  it('registers an onResponseError handler', () => {
    useApi()
    const opts = createMock.mock.calls[0]![0]
    expect(typeof opts.onResponseError).toBe('function')
  })

  it('onResponseError triggers refresh and retries once on 401', async () => {
    const refreshFetch = vi.fn().mockResolvedValue({})
    const retriedFetch = vi.fn().mockResolvedValue({ ok: true })
    ;(globalThis as unknown as { $fetch: unknown }).$fetch = Object.assign(
      (url: string) => url === '/api/auth/refresh' ? refreshFetch(url) : retriedFetch(url),
      { create: createMock },
    )

    useApi()
    const opts = createMock.mock.calls[0]![0]
    const options: RetryableFetchOptions = {}
    const context = {
      response: { status: 401 },
      request: '/api/foo',
      options,
    } as unknown as FetchContext & { response: { status: number } }
    await opts.onResponseError(context)

    expect(refreshFetch).toHaveBeenCalledWith('/api/auth/refresh')
    expect(options._retry).toBe(true)
  })

  it('onResponseError does NOT retry when already retried', async () => {
    const refreshFetch = vi.fn()
    ;(globalThis as unknown as { $fetch: unknown }).$fetch = Object.assign(
      () => refreshFetch(),
      { create: createMock },
    )

    useApi()
    const opts = createMock.mock.calls[0]![0]
    const options: RetryableFetchOptions = { _retry: true }
    const context = {
      response: { status: 401 },
      request: '/api/foo',
      options,
    } as unknown as FetchContext & { response: { status: number } }
    await opts.onResponseError(context)
    expect(refreshFetch).not.toHaveBeenCalled()
  })
})
```

- [ ] **Step 2: Run to confirm failure**

Run: `cd /data1/tdcweb-dev/frontend && npm test -- useApi`
Expected: module not found.

- [ ] **Step 3: Implement the composable**

Write `/data1/tdcweb-dev/frontend/app/composables/useApi.ts`:

```typescript
/**
 * Extension of Nuxt $fetch options carrying a `_retry` marker that
 * `onResponseError` uses to guard against infinite 401 retry loops.
 * Exported so tests can build typed mock contexts without `as any`.
 *
 * Derived from $fetch's own parameter type so it stays aligned with
 * Nitro's NitroFetchOptions (which narrows `method` to a literal union,
 * unlike ofetch's wider FetchOptions).
 */
export type RetryableFetchOptions = NonNullable<Parameters<typeof $fetch>[1]> & { _retry?: boolean }

// Return type annotated explicitly: the `onResponseError` handler
// recursively references `useApi()` in its retry path (spec §8.4 -- retry
// must re-enter the wrapper so `credentials: 'include'` and any future
// interceptor logic are preserved). Without the annotation TS7023 fires
// because the inferred type depends on itself. `ReturnType<typeof $fetch.create>`
// names the Nitro wrapper type without importing internal aliases.
export const useApi = (): ReturnType<typeof $fetch.create> => {
  return $fetch.create({
    credentials: 'include',
    async onResponseError({ response, request, options }) {
      const opts = options as RetryableFetchOptions
      if (response.status === 401 && !opts._retry) {
        await $fetch('/api/auth/refresh', { method: 'POST' })
        opts._retry = true
        return useApi()(request as string, opts)
      }
    },
  })
}
```

**Phase 3 amendments (intent codification, rule 19; typecheck batch F2;
MED batch F5).**

1. **`RetryableFetchOptions` derived from `NonNullable<Parameters<typeof
   $fetch>[1]>`** rather than ofetch's `FetchOptions`. Reason: Nitro's
   `$fetch` parameter type narrows `method` to a literal union, while
   ofetch's `FetchOptions` widens it to `string`. Under strict mode the
   narrow type is what reviewer-Phase-2 feedback required.
2. **Retry path calls `useApi()(request, opts)`, not `$fetch(request,
   opts)`.** Alignment to spec §8.4: the wrapper must re-enter itself so
   `credentials: 'include'` and any future interceptor logic are
   preserved on the retried request. The `_retry` flag set to `true`
   before the recursive call prevents infinite loops
   (unit-tested). F5 MED fix in scan row 41.
3. **Explicit `: ReturnType<typeof $fetch.create>` return type.**
   Required to break the TS7023 recursive-inference cycle introduced
   by `useApi()(...)` in the retry path.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd /data1/tdcweb-dev/frontend && npm test -- useApi`
Expected: 4 tests pass.

- [ ] **Step 5: Commit deferred**

Per CLAUDE.md rule 15, no per-task commit — changes accumulate in the
working tree until the Phase 3 atomic commit.

---

### Task 3.9: Split the Pinia store into domain modules

**Files:**
- Create: `frontend/app/stores/auth.ts`
- Create: `frontend/app/stores/locale.ts`
- Create: `frontend/app/stores/ui.ts`

- [ ] **Step 1: Write stores/auth.ts**

Write `/data1/tdcweb-dev/frontend/app/stores/auth.ts`:

```typescript
import { defineStore } from 'pinia'
import type { User } from '~/types/user'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = computed(() => user.value !== null)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isStaff = computed(() => user.value?.role === 'staff' || user.value?.role === 'admin')

  const setUser = (u: User | null) => { user.value = u }
  const clear = () => { user.value = null }

  return { user, isAuthenticated, isAdmin, isStaff, setUser, clear }
})
```

- [ ] **Step 2: Write stores/locale.ts**

Write `/data1/tdcweb-dev/frontend/app/stores/locale.ts`:

```typescript
import { defineStore } from 'pinia'

export const useLocaleStore = defineStore('locale', () => {
  const current = ref<string>('en')
  const setLocale = (code: string) => { current.value = code }
  return { current, setLocale }
})
```

- [ ] **Step 3: Write stores/ui.ts**

Write `/data1/tdcweb-dev/frontend/app/stores/ui.ts`:

```typescript
import { defineStore } from 'pinia'

interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  message: string
}

export const useUiStore = defineStore('ui', () => {
  const isMobileMenuOpen = ref(false)
  const notifications = ref<Notification[]>([])

  const toggleMobileMenu = () => { isMobileMenuOpen.value = !isMobileMenuOpen.value }
  const closeMobileMenu = () => { isMobileMenuOpen.value = false }

  /**
   * Push a notification onto the stack.
   *
   * @warning Do NOT call during SSR setup() or template interpolation.
   * Uses `crypto.randomUUID()` which produces different IDs on server vs
   * client, causing hydration mismatch. Safe for user-triggered actions
   * (button clicks, API error handlers, form submissions post-mount).
   */
  const pushNotification = (n: Omit<Notification, 'id'>) => {
    notifications.value.push({ ...n, id: crypto.randomUUID() })
  }
  const dismissNotification = (id: string) => {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }

  return {
    isMobileMenuOpen, notifications,
    toggleMobileMenu, closeMobileMenu,
    pushNotification, dismissNotification,
  }
})
```

**Phase 3 amendment.** `pushNotification()` was flagged by the MED
batch review (scan row 32) for SSR risk: `crypto.randomUUID()` produces
different values on server vs client, so calling it during SSR setup
or template interpolation would cause hydration mismatch. The JSDoc
`@warning` codifies the constraint; the runtime behaviour is safe as
long as callers only trigger the action from event handlers. Playbook
§10.6 expands this into a general rule for SSR-unsafe actions.

- [ ] **Step 4: Commit deferred**

Per CLAUDE.md rule 15, no per-task commit — changes accumulate in the
working tree until the Phase 3 atomic commit.

---

### Task 3.10: Create the `useScrollAnimation` composable

**Files:**
- Create: `frontend/app/composables/useScrollAnimation.ts`

- [ ] **Step 1: Write the composable**

Write `/data1/tdcweb-dev/frontend/app/composables/useScrollAnimation.ts`:

```typescript
import type { gsap } from 'gsap'

export function useScrollAnimation() {
  const ctx = ref<ReturnType<typeof import('gsap').gsap.context> | null>(null)

  const animateReveal = (selector: string, options: Record<string, unknown> = {}) => {
    if (!import.meta.client) return
    // Respect user accessibility preference: skip reveal entirely when the
    // system signals reduced motion. Elements render at their natural CSS
    // state (no translate, no fade-in), consistent with the intent of the
    // prefers-reduced-motion media query.
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const { $gsap } = useNuxtApp() as unknown as { $gsap: typeof gsap }
    ctx.value = $gsap.context(() => {
      $gsap.from(selector, {
        y: 100,
        opacity: 0,
        duration: 1,
        stagger: 0.2,
        scrollTrigger: { trigger: selector, start: 'top 80%' },
        ...options,
      })
    })
  }

  onBeforeUnmount(() => {
    if (!import.meta.client) return
    ctx.value?.revert()
    const { $ScrollTrigger } = useNuxtApp() as unknown as {
      $ScrollTrigger: typeof import('gsap/ScrollTrigger').ScrollTrigger
    }
    $ScrollTrigger?.refresh()
  })

  return { animateReveal }
}
```

**Phase 3 amendment (Task 3.10b controller micro-edit).** Original
draft had no `prefers-reduced-motion` guard — any Phase 4+ consumer
calling `animateReveal` would play the reveal regardless of user
preference. 3-line early-return guard added inline
(`if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return`)
between the `import.meta.client` check and the `useNuxtApp()` call.
This is one of the three layers of the reduced-motion discipline —
see playbook §9 for the full pattern (Lenis plugin skips construction,
`useScrollAnimation` no-ops, `useSmoothScroll` no-ops).

- [ ] **Step 2: Commit deferred**

Per CLAUDE.md rule 15, no per-task commit — changes accumulate in the
working tree until the Phase 3 atomic commit.

---

### Task 3.11: Create `useSmoothScroll` and `useLocationTheme`

**Files:**
- Create: `frontend/app/composables/useSmoothScroll.ts`
- Create: `frontend/app/composables/useLocationTheme.ts`

- [ ] **Step 1: Write useSmoothScroll.ts**

Write `/data1/tdcweb-dev/frontend/app/composables/useSmoothScroll.ts`:

```typescript
import type Lenis from 'lenis'

export function useSmoothScroll() {
  const scrollTo = (target: string | HTMLElement, options?: { offset?: number }) => {
    if (!import.meta.client) return
    // Respect user accessibility preference: skip programmatic smooth scroll
    // when reduced-motion is requested. Consumer fallback is browser-native
    // scrollIntoView / location hash if needed; this composable simply no-ops.
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const { $lenis } = useNuxtApp() as unknown as { $lenis: Lenis }
    $lenis?.scrollTo(target, options)
  }

  return { scrollTo }
}
```

**Phase 3 amendment.** Task 3.11 preemptively included the
reduced-motion guard (learning from Task 3.10b retrospective
application). The guard combines with the Lenis plugin's own
reduced-motion short-circuit (see Phase 2 / Task 2.5 / playbook §9) —
when the user has opted out, Lenis is never constructed, so
`$lenis?.scrollTo(...)` additionally no-ops via optional chaining.
Belt-and-braces.

- [ ] **Step 2: Write useLocationTheme.ts**

Write `/data1/tdcweb-dev/frontend/app/composables/useLocationTheme.ts`:

```typescript
export function useLocationTheme(slug: Ref<string | null | undefined> | string | null | undefined) {
  const slugRef = isRef(slug) ? slug : ref(slug ?? null)

  useHead(() => ({
    bodyAttrs: {
      'data-location': slugRef.value ?? undefined,
    },
  }))
}
```

**Phase 3 note.** No Phase 3 page exercises per-location theming
(home, locations list, events list are all `:root` palette). The
composable is the future bridge: when Phase 4+ detail routes land
(`/locations/[slug]`, potentially `/events/[slug]`), they will call
`useLocationTheme(computed(() => data.value?.location_slug))` to stamp
`body[data-location="..."]` and trigger the `main.css` palette
override. Unknown slugs fall back to `:root` without visual breakage.

- [ ] **Step 3: Commit deferred**

Per CLAUDE.md rule 15, no per-task commit — changes accumulate in the
working tree until the Phase 3 atomic commit.

---

## Phase 4 — BFF auth and middleware

### Task 4.1: Implement the login BFF handler (TDD)

**Files:**
- Create: `frontend/server/api/auth/login.post.ts`
- Create: `frontend/tests/unit/login-handler.test.ts`

- [ ] **Step 1: Write the failing test**

Write `/data1/tdcweb-dev/frontend/tests/unit/login-handler.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { H3Event } from 'h3'

// Typed shapes for the globalThis stubs. Mirrors the Phase 3 Gap #1
// lesson (no `as any` in test mocks): each stub is cast through
// `unknown` to a specific function-shape interface. Reconciled at
// Phase 4 docs-sync.
type DefineEventHandlerStub = <T>(h: T) => T
type ReadValidatedBodyStub = ReturnType<typeof vi.fn>
type FlaskFetchStub = ReturnType<typeof vi.fn>
type SetCookieStub = ReturnType<typeof vi.fn>
type CreateErrorStub = (opts: { statusCode: number; statusMessage: string }) => Error

const readValidatedBodyMock: ReadValidatedBodyStub = vi.fn()
const flaskFetchMock: FlaskFetchStub = vi.fn()
const setAccessCookieMock: SetCookieStub = vi.fn()
const setRefreshCookieMock: SetCookieStub = vi.fn()

;(globalThis as unknown as { defineEventHandler: DefineEventHandlerStub })
  .defineEventHandler = (h) => h
;(globalThis as unknown as { readValidatedBody: ReadValidatedBodyStub })
  .readValidatedBody = readValidatedBodyMock
;(globalThis as unknown as { flaskFetch: FlaskFetchStub })
  .flaskFetch = flaskFetchMock
;(globalThis as unknown as { setAccessCookie: SetCookieStub })
  .setAccessCookie = setAccessCookieMock
;(globalThis as unknown as { setRefreshCookie: SetCookieStub })
  .setRefreshCookie = setRefreshCookieMock
;(globalThis as unknown as { createError: CreateErrorStub })
  .createError = (opts) => Object.assign(new Error(opts.statusMessage), opts)

import loginHandler from '../../server/api/auth/login.post'

describe('POST /api/auth/login', () => {
  beforeEach(() => {
    readValidatedBodyMock.mockReset()
    flaskFetchMock.mockReset()
    setAccessCookieMock.mockReset()
    setRefreshCookieMock.mockReset()
  })

  it('sets both cookies and returns the user on success', async () => {
    readValidatedBodyMock.mockResolvedValue({ email: 'a@b.c', password: 'pw' })
    // Flask responses use the canonical envelope shape per Phase 4
    // user-intent scan row 15: { success: true, data: { ... } }. The
    // BFF unwraps `.data`. Reconciled at Phase 4 docs-sync.
    flaskFetchMock.mockResolvedValue({
      success: true,
      data: {
        access: 'acc',
        refresh: 'ref',
        user: { id: 1, email: 'a@b.c', username: 'u', role: 'user' },
      },
    })
    const event = {} as H3Event

    const result = await loginHandler(event)

    expect(setAccessCookieMock).toHaveBeenCalledWith(event, 'acc')
    expect(setRefreshCookieMock).toHaveBeenCalledWith(event, 'ref')
    expect(result).toEqual({ user: { id: 1, email: 'a@b.c', username: 'u', role: 'user' } })
  })

  it('rejects invalid body with 400', async () => {
    readValidatedBodyMock.mockRejectedValue(new Error('validation failed'))
    const event = {} as H3Event

    await expect(loginHandler(event)).rejects.toThrow()
  })
})
```

- [ ] **Step 2: Run to confirm failure**

Run: `cd /data1/tdcweb-dev/frontend && npm test -- login-handler`
Expected: module not found.

- [ ] **Step 3: Write the handler**

Write `/data1/tdcweb-dev/frontend/server/api/auth/login.post.ts`:

```typescript
import { z } from 'zod'
import type { ApiResponse } from '~/types/api'

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
})

interface FlaskLoginPayload {
  access: string
  refresh: string
  user: {
    id: number
    email: string
    username: string
    role: 'user' | 'staff' | 'admin'
  }
}

export default defineEventHandler(async (event) => {
  const body = await readValidatedBody(event, (input) => loginSchema.parse(input))

  // Flask responses use the canonical envelope per `app/utils/responses.py`:
  // `{ success: true, data: { ... } }`. The BFF unwraps `.data`. Reconciled
  // at Phase 4 docs-sync (user-intent scan row 15).
  const response = await flaskFetch<ApiResponse<FlaskLoginPayload>>(
    '/api/auth/login',
    event,
    { method: 'POST', body },
  )

  setAccessCookie(event, response.data.access)
  setRefreshCookie(event, response.data.refresh)

  return { user: response.data.user }
})
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /data1/tdcweb-dev/frontend && npm test -- login-handler`
Expected: 2 tests pass.

- [ ] **Step 5: Hand off**

Per CLAUDE.md rule 15, implementer subagents do NOT commit. The
working-tree changes accumulate; the controller commits all Phase 4
code + docs together at the phase-end atomic commit (rule 16(e)).
The placeholder `git commit` line that earlier drafts of this plan
included was removed during Phase 4 docs-sync.

---

### Task 4.2: Implement logout, refresh, me BFF handlers

**Files:**
- Create: `frontend/server/api/auth/logout.post.ts`
- Create: `frontend/server/api/auth/refresh.post.ts`
- Create: `frontend/server/api/auth/me.get.ts`

- [ ] **Step 1: Write logout.post.ts**

Write `/data1/tdcweb-dev/frontend/server/api/auth/logout.post.ts`:

```typescript
export default defineEventHandler(async (event) => {
  try {
    await flaskFetch('/api/auth/logout', event, { method: 'POST' })
  } catch {
    // Even if Flask fails, clear our cookies to log the user out locally
  }
  clearAuthCookies(event)
  return { success: true }
})
```

- [ ] **Step 2: Write refresh.post.ts**

Write `/data1/tdcweb-dev/frontend/server/api/auth/refresh.post.ts`:

```typescript
import type { ApiResponse } from '~/types/api'

interface FlaskRefreshPayload {
  access: string
  refresh: string
}

export default defineEventHandler(async (event) => {
  const refresh = getRefreshToken(event)
  if (!refresh) {
    throw createError({ statusCode: 401, statusMessage: 'No refresh token' })
  }

  // Envelope unwrap as in login (user-intent scan row 15, Phase 4).
  const response = await flaskFetch<ApiResponse<FlaskRefreshPayload>>(
    '/api/auth/refresh',
    event,
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${refresh}` },
    },
  )

  setAccessCookie(event, response.data.access)
  setRefreshCookie(event, response.data.refresh)

  return { success: true }
})
```

- [ ] **Step 3: Write me.get.ts**

Write `/data1/tdcweb-dev/frontend/server/api/auth/me.get.ts`:

```typescript
import type { ApiResponse } from '~/types/api'
import type { User } from '~/types/user'

export default defineEventHandler(async (event) => {
  const hasAccess = event.context.flaskHeaders !== undefined
  if (!hasAccess) {
    throw createError({ statusCode: 401, statusMessage: 'Not authenticated' })
  }

  // Flask `/api/auth/me` returns `success(g.current_user.to_dict())` --
  // envelope-wrapped User. BFF unwraps `.data`.
  const response = await flaskFetch<ApiResponse<User>>('/api/auth/me', event)
  return { user: response.data }
})
```

- [ ] **Step 4: Hand off**

Per CLAUDE.md rule 15, no per-task commit. Phase 4 atomic commit at
rule 16(e) absorbs these handlers along with the rest of the phase.

---

### Task 4.3: Implement the on-demand revalidate endpoint

**Files:**
- Create: `frontend/server/api/revalidate.post.ts`

- [ ] **Step 1: Write the handler**

Write `/data1/tdcweb-dev/frontend/server/api/revalidate.post.ts`:

```typescript
// Cache-key format derived from Nitro source:
//   cache:nitro:routes:_:<escapedPathname>.<hash>.json
// where <escapedPathname> = escapeKey(decodeURI(pathname)) (strips \W,
// 16-char cap, "index" fallback) and <hash> is a content hash of the
// full request URL. Source: nitropack/dist/runtime/internal/cache.mjs
// lines 29 and 124-145, default group `nitro/routes` set in
// runtime/internal/app.mjs line 131. We list under the per-path prefix
// and remove every match (multiple cached variants per path are normal)
// rather than `removeItem(<single-key>)`. Reconciled at Phase 4
// docs-sync -- earlier drafts used `routes:${path}.json`, which was a
// guess and never matched a real key.
import { defineEventHandler } from 'h3'
import { z } from 'zod'
import type { ApiResponse } from '~/types/api'
import type { User } from '~/types/user'

const ESCAPE_NON_WORD = /\W/g

const encodePathname = (path: string): string => {
  const pathname = decodeURI(path.split('?')[0] ?? path)
  const stripped = pathname.replace(ESCAPE_NON_WORD, '').slice(0, 16)
  return stripped || 'index'
}

const revalidateSchema = z.object({
  path: z
    .string()
    .min(1)
    .max(500)
    .refine((p) => p.startsWith('/'))
    .refine((p) => !/\.\./.test(p))
    .refine((p) => !/\/\//.test(p)),
})

export default defineEventHandler(async (event) => {
  // Admin gate: piggy-back on auth-forward middleware. Flask's
  // /api/auth/me returns ApiResponse<User>; BFF unwraps .data.
  let me: ApiResponse<User>
  try {
    me = await flaskFetch<ApiResponse<User>>('/api/auth/me', event)
  } catch {
    throw createError({ statusCode: 401, statusMessage: 'Not authenticated' })
  }
  if (me.data.role !== 'admin') {
    throw createError({ statusCode: 403, statusMessage: 'Admin role required' })
  }

  const { path } = await readValidatedBody(event, (input) =>
    revalidateSchema.parse(input),
  )

  const encoded = encodePathname(path)
  const storage = useStorage('cache:nitro:routes')
  const allKeys = await storage.getKeys('_')
  const prefix = `_:${encoded}.`
  const matching = allKeys.filter((k) => k.startsWith(prefix))
  await Promise.all(matching.map((k) => storage.removeItem(k)))

  return { revalidated: path }
})
```

- [ ] **Step 2: Hand off**

No per-task commit (CLAUDE.md rule 15). Phase 4 atomic commit at
rule 16(e) absorbs this handler.

---

### Task 4.4: Create client auth composable and navigation middleware

**Files:**
- Create: `frontend/app/composables/useAuth.ts`
- Create: `frontend/app/middleware/auth.ts`
- Create: `frontend/app/middleware/admin.ts`
- Create: `frontend/app/middleware/staff.ts`

- [ ] **Step 1: Write useAuth.ts**

Write `/data1/tdcweb-dev/frontend/app/composables/useAuth.ts`:

```typescript
import type { User } from '~/types/user'

// SSR cookie-forwarding contract. When this composable is invoked from a
// route middleware during SSR (auth/admin/staff guards), a raw `$fetch`
// does NOT forward the incoming request's `Cookie` header to the
// internal `/api/auth/me` Nitro route. The internal handler then sees
// no `tdc_access` cookie, the auth-forward middleware leaves
// event.context.flaskHeaders undefined, the chain returns 401, and an
// authenticated user appears as a guest on every SSR pass.
//
// `useRequestFetch()` returns a `$fetch` instance pre-bound to the
// current H3Event so SSR calls inherit the original request's cookies.
// On the client it is a pass-through to `$fetch`. We use it for all
// three BFF calls for consistency. Reconciled at Phase 4 docs-sync;
// earlier drafts of this snippet used raw `$fetch` with
// `credentials: 'include'`, which only matters in the browser and does
// nothing on the SSR side.
export function useAuth() {
  const store = useAuthStore()
  const requestFetch = useRequestFetch()
  const { user, isAuthenticated, isAdmin, isStaff } = storeToRefs(store)

  const fetchMe = async () => {
    try {
      const { user: u } = await requestFetch<{ user: User }>('/api/auth/me')
      store.setUser(u)
    } catch {
      store.clear()
    }
  }

  const login = async (email: string, password: string) => {
    const { user: u } = await requestFetch<{ user: User }>('/api/auth/login', {
      method: 'POST',
      body: { email, password },
    })
    store.setUser(u)
    return u
  }

  const logout = async () => {
    try {
      await requestFetch('/api/auth/logout', { method: 'POST' })
    } finally {
      store.clear()
    }
  }

  return {
    user,
    isAuthenticated,
    isAdmin,
    isStaff,
    fetchMe,
    login,
    logout,
  }
}
```

> The as-built `frontend/app/composables/useAuth.ts` extracts the three
> BFF operations into a pure `buildAuthOps(store, fetcher)` helper
> exported alongside `useAuth()` for testability. See playbook
> §19.7 (pure-helper extraction pattern).

- [ ] **Step 2: Write middleware/auth.ts**

Write `/data1/tdcweb-dev/frontend/app/middleware/auth.ts`:

```typescript
export default defineNuxtRouteMiddleware(async (to) => {
  const { user, fetchMe } = useAuth()
  if (!user.value) {
    await fetchMe()
    if (!user.value) {
      return navigateTo(`/auth/login?redirect=${encodeURIComponent(to.fullPath)}`)
    }
  }
})
```

- [ ] **Step 3: Write middleware/admin.ts**

Write `/data1/tdcweb-dev/frontend/app/middleware/admin.ts`:

```typescript
export default defineNuxtRouteMiddleware(async (to) => {
  const { user, fetchMe, isAdmin } = useAuth()
  if (!user.value) await fetchMe()
  if (!user.value) {
    return navigateTo(`/auth/login?redirect=${encodeURIComponent(to.fullPath)}`)
  }
  if (!isAdmin.value) {
    throw createError({ statusCode: 403, statusMessage: 'Admin only' })
  }
})
```

- [ ] **Step 4: Write middleware/staff.ts**

Write `/data1/tdcweb-dev/frontend/app/middleware/staff.ts`:

```typescript
export default defineNuxtRouteMiddleware(async (to) => {
  const { user, fetchMe, isStaff } = useAuth()
  if (!user.value) await fetchMe()
  if (!user.value) {
    return navigateTo(`/auth/login?redirect=${encodeURIComponent(to.fullPath)}`)
  }
  if (!isStaff.value) {
    throw createError({ statusCode: 403, statusMessage: 'Staff only' })
  }
})
```

- [ ] **Step 5: Hand off**

No per-task commit (CLAUDE.md rule 15). Phase 4 atomic commit at
rule 16(e) absorbs `useAuth`, `auth-guard.ts`, and the three guard
middlewares together with the BFF handlers from Tasks 4.1-4.3 and the
Phase 4B backend.

> The as-built guard middlewares (`auth.ts` / `admin.ts` / `staff.ts`)
> delegate their decision logic to pure helpers in
> `app/utils/auth-guard.ts` (`buildLoginRedirect`, `decideAuthOutcome`,
> `decideAdminOutcome`, `decideStaffOutcome`). Each middleware is a
> thin wire-up of the auto-imports to the helper. See playbook §19.7.

---

## Phase 5 — Documentation and agents

### Task 5.1: CLAUDE.md update (DONE as prep work)

**Status:** ✅ Completed before Phase 1 started.

`CLAUDE.md` was updated with:
1. Frontend stack table → Nuxt 4 + Vue 3 + TypeScript strict; added rows for
   port allocation (dev 9503 / prod 9501), i18n module, SEO modules, image
   module, forms (vee-validate + zod), rich text (TipTap), auth cookie
   transport, BFF architecture, testing tools.
2. `tdc-frontend-expert` agent description line updated to reflect new stack.
3. New section "🎬 Rendering Strategy" (per-route SSG/ISR/SSR/SPA map +
   on-demand revalidation).
4. New section "🔒 SSR Client-Only Rules" (7 non-negotiable rules covering
   GSAP, Lenis, browser globals, hydration-mismatch generators, TipTap,
   location theming, auth cookies).
5. Reference links to spec, plan, playbook, pdp-v3 (planned), pdp-v2
   (historical).

**Step required in this task:** none — CLAUDE.md is ready. Further edits
only if early phases reveal gaps.

---

### Task 5.2: Create pdp-v3.md

**Files:**
- Create: `docs/plans/pdp-v3.md`

- [ ] **Step 1: Write the pdp-v3 header and stack section**

Write `/data1/tdcweb-dev/docs/plans/pdp-v3.md`:

```markdown
# Project Development Plan (PDP) v3.0
# The Dreamer's Cave — Virtual Music Club Website

**Version:** 3.0
**Date:** 2026-04-23
**Domain:** thedreamerscave.club
**Hosting:** mioh1 (Hetzner Frankfurt, Ubuntu)
**Predecessor:** docs/plans/pdp-v2.md (v2 kept as historical reference)

---

## 1. Scope of v3

v3 captures the Nuxt 4 architecture. All product goals from v2 carry
over unchanged (10 themed locations, Google Calendar events, Patreon
integration, Facebook automation, Second Life API, Apple-style landing).
Only the frontend technology layer and rendering strategy change.

For full product scope, refer to pdp-v2 §1 (Executive Summary) and §11
(Feature List). This document supersedes pdp-v2 §2.2 (Frontend Stack),
§2.3 (Infrastructure updates), and adds new sections for Rendering
Strategy, SSR Architecture, and Deployment Topology.

---

## 2. Technology Stack

### 2.1 Backend (unchanged from v2)

| Component | Technology | Notes |
|---|---|---|
| Framework | Python 3.11+ / Flask | RESTful API |
| Database | MySQL 8.x + mysql-connector-python | NO SQLAlchemy |
| Auth | Flask JWT (access 15 min, refresh 7d) | Issued to Nuxt BFF |
| OAuth | Authlib (Google, Discord, Facebook) | — |
| Email | SMTP (self-hosted iRedMail) | — |
| Tasks | Celery + Redis | Async jobs |
| Caching | Redis | Query cache |

### 2.2 Frontend (new)

| Component | Technology | Notes |
|---|---|---|
| Framework | Nuxt 4 (Vue 3 Composition API) | `app/` layer |
| Language | TypeScript (strict) | — |
| Build | Vite (under Nuxt) | — |
| Styling | Tailwind CSS + CSS vars | Per-location theming |
| Animations | GSAP + ScrollTrigger + Lenis | Client-only plugins |
| State | Pinia (`@pinia/nuxt`) | Split: auth / locale / ui |
| i18n | `@nuxtjs/i18n` | `prefix_except_default` EN/IT/FR/ES |
| SEO | `@nuxtjs/seo` + sitemap + robots | Schema.org JSON-LD |
| Image | `@nuxt/image` | Auto webp/avif |
| Icons | lucide-vue-next | — |
| Rich text | `@tiptap/vue-3` | Blog, admin-only |
| Forms | vee-validate + zod | Type-safe validation |
| Testing | vitest + Playwright | Unit + E2E |

### 2.3 Infrastructure

| Component | Technology | Notes |
|---|---|---|
| OS | Ubuntu 22.04 | mioh1 |
| Web server | Nginx | Reverse proxy: /api/auth + /api/revalidate → Nuxt; other /api → Flask; / → Nuxt |
| Frontend runtime | Node (systemd `tdcweb-frontend.service`) | `:9501` |
| Backend runtime | Gunicorn (systemd `tdcweb-backend.service`) | `:9500` |
| SSL | Let's Encrypt (certbot) | Auto-renewal |

### 2.4 Port allocation

| | Dev | Prod |
|---|---|---|
| Flask | 9502 | 9500 |
| Nuxt | 9503 | 9501 |
| MySQL | 3306 | 3306 |

---

## 3. Rendering Strategy

| Route | Strategy | Rationale |
|---|---|---|
| `/` | SSG | Apple-style landing, rare changes |
| `/locations`, `/locations/**` | SSG | 10 fixed venues |
| `/artists`, `/artists/**` | SSG | Rare changes |
| `/events`, `/events/**` | ISR 5 min | Frequent but not real-time |
| `/blog`, `/blog/**` | ISR 1h + on-demand | Staff publish workflow |
| `/auth/**` | SSR (no cache) | Dynamic per session |
| `/dashboard/**` | SPA | Auth-gated, no SEO |
| `/admin/**` | SPA | Auth-gated, heavy client |

On-demand revalidation is triggered by admin saves via
`POST /api/revalidate { path }` to the Nuxt server route.

---

## 4. SSR Architecture (Hybrid BFF)

Nuxt's node server renders pages and hosts a minimal BFF layer at
`server/api/auth/**` that wraps Flask auth endpoints and sets HttpOnly
cookies on responses:
- `tdc_access` — 15 min, SameSite=Lax, Path=/
- `tdc_refresh` — 7 days, SameSite=Strict, Path=/api/auth (rotated on use)

All other `/api/**` paths are proxied straight to Flask (nginx in prod,
Nitro devProxy in dev). During SSR, Nuxt's `flaskFetch()` util reads
`event.context.flaskHeaders` (populated by the `auth-forward` server
middleware from the access cookie) and forwards it as `Authorization:
Bearer` to Flask.

See `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md` for
the full architecture spec and code-level patterns.

---

## 5. Deployment Topology

```
[Browser] ──► :443 nginx
                 ├─► /_nuxt/, /assets   → static
                 ├─► /api/auth/**       → :9501 Nuxt BFF
                 ├─► /api/revalidate    → :9501 Nuxt
                 ├─► /api/**            → :9500 Flask
                 └─► /                  → :9501 Nuxt (SSR/SSG/SPA)
```

Both backend processes bind to `127.0.0.1`. Nginx and Nuxt's node
process are the only clients that can reach Flask.

---

## 6. Changes from v2

| Area | v2 | v3 |
|---|---|---|
| Frontend framework | Vue 3 + Vite SPA | Nuxt 4 SSR/SSG/ISR |
| Language | JavaScript | TypeScript (strict) |
| Routing | vue-router | File-based (`app/pages/`) |
| Auth transport | Session cookies | JWT HttpOnly cookies |
| SEO | Client-side only | Server-rendered, Schema.org, sitemap |
| Image optimization | Manual | `<NuxtImg>` auto |
| i18n routing | Query param / cookie | URL prefix + cookie + browser |
| Deploy | Static dist + nginx | Node systemd + nginx |

---

## 7. Out-of-scope vs Deferred

All product features listed in pdp-v2 §11 are carried forward
unchanged. The Nuxt migration (this document) does not add or remove
product features.

Implementation plan: `docs/superpowers/plans/2026-04-23-nuxt-integration.md`.
```

- [ ] **Step 2: Commit**

```bash
cd /data1/tdcweb-dev
git add docs/plans/pdp-v3.md
git commit -m "docs(pdp): add v3 with Nuxt architecture (v2 kept as historical reference)"
```

---

### Task 5.3: tdc-frontend-expert agent rewrite (DONE as prep work)

**Status:** ✅ Completed before Phase 1 started.

The agent at `.claude/agents/tdc-frontend-expert.md` was fully rewritten
(1449 lines, 26 sections) covering:
- Nuxt 4 fundamentals (app/ layer, auto-imports, runtimeConfig)
- Vue 3 + TypeScript strict patterns
- File-based routing, layouts, `definePageMeta`
- Data fetching (useFetch / $fetch / useAsyncData decision table)
- Rendering strategies (SSG/ISR/SSR/SPA + routeRules)
- SSR pitfalls (client-only rules, hydration traps)
- GSAP `gsap.context()` correct cleanup
- Lenis synced with `gsap.ticker`
- Pinia setup-syntax stores
- Server routes (BFF), h3 utilities, cookie helpers, flaskFetch
- @nuxtjs/i18n deep dive (DB-backed translations)
- Tailwind + location theming CSS vars (SSR-safe)
- SEO (useSeoMeta, useHead, useSchemaOrg, sitemap, robots)
- @nuxt/image
- vee-validate + zod forms
- TipTap in ClientOnly
- vitest + @nuxt/test-utils + Playwright
- Accessibility WCAG 2.1 AA
- Performance (Core Web Vitals)
- 20+ forbidden patterns with rejection rules
- Integration with other TDC agents
- Closing checklist for every frontend task

**Step required in this task:** none — agent is ready. If the file
needs further refinement after early phases reveal gaps, edit directly
and commit with `docs(agent): ...` prefix.

---

## Phase 6 — Nginx and systemd

### Task 6.1: Write the production nginx config

**Files:**
- Create: `nginx/thedreamerscave.conf`

- [ ] **Step 1: Check if the nginx directory exists**

Run: `ls /data1/tdcweb-dev/nginx/ 2>&1 || echo 'need to create'`
If missing: `mkdir -p /data1/tdcweb-dev/nginx`

- [ ] **Step 2: Write nginx/thedreamerscave.conf**

Write `/data1/tdcweb-dev/nginx/thedreamerscave.conf`:

```nginx
upstream tdc_flask {
    server 127.0.0.1:9500;
}
upstream tdc_nuxt {
    server 127.0.0.1:9501;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name thedreamerscave.club www.thedreamerscave.club;

    ssl_certificate     /etc/letsencrypt/live/thedreamerscave.club/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/thedreamerscave.club/privkey.pem;

    # Static assets built by Nuxt
    location /_nuxt/ {
        alias /data1/tdcweb/frontend/.output/public/_nuxt/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # BFF routes handled by Nuxt node
    location = /api/revalidate { proxy_pass http://tdc_nuxt; }
    location /api/auth/         { proxy_pass http://tdc_nuxt; }

    # All other /api/* → Flask
    location /api/ {
        proxy_pass http://tdc_flask;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # Everything else → Nuxt node (SSR/SSG/SPA per routeRules)
    location / {
        proxy_pass http://tdc_nuxt;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name thedreamerscave.club www.thedreamerscave.club;
    return 301 https://$host$request_uri;
}
```

- [ ] **Step 3: Validate nginx syntax (if nginx installed locally)**

Run: `nginx -t -c /data1/tdcweb-dev/nginx/thedreamerscave.conf 2>&1 || echo 'nginx binary not available locally; validate on prod host during deploy'`
Expected on prod host: `nginx: configuration file ... test is successful`.

- [ ] **Step 4: Commit**

```bash
cd /data1/tdcweb-dev
git add nginx/thedreamerscave.conf
git commit -m "feat(deploy): add nginx config routing /api/auth and / to Nuxt :9501, /api to Flask :9500"
```

---

### Task 6.2: Write the systemd unit for the Nuxt node server

**Files:**
- Create: `deploy/systemd/tdcweb-frontend.service`

- [ ] **Step 1: Create the deploy directory if missing**

Run: `mkdir -p /data1/tdcweb-dev/deploy/systemd`

- [ ] **Step 2: Write the systemd unit**

Write `/data1/tdcweb-dev/deploy/systemd/tdcweb-frontend.service`:

```ini
[Unit]
Description=TDC Nuxt Frontend (SSR/SSG/ISR)
After=network.target tdcweb-backend.service
Requires=tdcweb-backend.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/data1/tdcweb/frontend
Environment="NODE_ENV=production"
Environment="PORT=9501"
Environment="HOST=127.0.0.1"
EnvironmentFile=/data1/tdcweb/frontend/.env.production
ExecStart=/usr/bin/node .output/server/index.mjs
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 3: Commit**

```bash
cd /data1/tdcweb-dev
git add deploy/systemd/tdcweb-frontend.service
git commit -m "feat(deploy): add systemd unit for Nuxt node server on :9501"
```

---

## Phase 7 — Smoke tests (Definition of Done)

### Task 7.1: Dev server + HMR check

**Files:** none changed

- [ ] **Step 1: Start dev server**

Run: `cd /data1/tdcweb-dev/frontend && npm run dev`
Expected: server binds `http://localhost:9503/`, no build errors.

- [ ] **Step 2: Verify in browser**

Open `http://localhost:9503/` in a browser. Expected: landing page renders with "You Can See The Music" headline, dark background, Tailwind styles applied.

- [ ] **Step 3: HMR check**

Edit `frontend/app/pages/index.vue` subtly (e.g., change `hero_subtitle` text), save. Expected: browser updates within ~1s without full reload.

Revert the edit. Kill dev server.

- [ ] **Step 4: No commit (observational task)**

---

### Task 7.2: SSR content verification

**Files:** none changed

- [ ] **Step 1: Start dev server and fetch with curl**

Run:
```bash
cd /data1/tdcweb-dev/frontend && npm run dev &
sleep 3
curl -s http://localhost:9503/ | grep -c 'You Can See The Music'
kill %1
```
Expected: count `>= 1`.

- [ ] **Step 2: Verify /dashboard is SPA (no auth content in HTML)**

Run:
```bash
cd /data1/tdcweb-dev/frontend && npm run dev &
sleep 3
curl -s http://localhost:9503/dashboard | grep -c 'favorites'
kill %1
```
Expected: `0` (dashboard is `ssr: false`; no server-rendered content).

- [ ] **Step 3: No commit (observational)**

---

### Task 7.3: Login round-trip (manual or Playwright)

**Files:** none changed (uses existing Flask + Nuxt)

- [ ] **Step 1: Ensure Flask is running on :9502 (dev)**

Run: `curl -s http://localhost:9502/api/health 2>&1 | head`
If not running, start it per project conventions.

- [ ] **Step 2: Start Nuxt dev and make a login request**

Run:
```bash
cd /data1/tdcweb-dev/frontend && npm run dev &
sleep 3
# Replace email/password with a real seeded test user from Flask fixtures
curl -i -X POST http://localhost:9503/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@tdc.local","password":"test"}'
kill %1
```
Expected: `HTTP/1.1 200 OK`, response contains `Set-Cookie: tdc_access=...; HttpOnly; SameSite=Lax` and `Set-Cookie: tdc_refresh=...; HttpOnly; SameSite=Strict; Path=/api/auth`.

If Flask returns 401 because no test user exists, seed one via the existing Flask fixtures/migrations before re-running.

- [ ] **Step 3: No commit (observational)**

---

### Task 7.4: Production build and node preview

**Files:** none changed

- [ ] **Step 1: Build**

Run: `cd /data1/tdcweb-dev/frontend && npm run build`
Expected: `.output/server/index.mjs` and `.output/public/_nuxt/` created, no errors.

- [ ] **Step 2: Start the built server on :9501**

Run:
```bash
cd /data1/tdcweb-dev/frontend && PORT=9501 HOST=127.0.0.1 NODE_ENV=production node .output/server/index.mjs &
sleep 3
curl -s http://localhost:9501/ | grep -c 'You Can See The Music'
kill %1
```
Expected: `>= 1`.

- [ ] **Step 3: Verify sitemap**

Run:
```bash
cd /data1/tdcweb-dev/frontend && PORT=9501 HOST=127.0.0.1 NODE_ENV=production node .output/server/index.mjs &
sleep 3
curl -s http://localhost:9501/sitemap.xml | grep -c '<url>'
kill %1
```
Expected: `>= 1` (even if empty DB, home and prerendered public pages should appear).

- [ ] **Step 4: No commit (observational)**

---

### Task 7.5: Full unit test suite

**Files:** none changed

- [ ] **Step 1: Run vitest**

Run: `cd /data1/tdcweb-dev/frontend && npm test`
Expected: all tests from tasks 2.6, 2.7, 3.8, 4.1 pass (≥ 11 tests total).

- [ ] **Step 2: No commit (observational)**

---

### Task 7.6: i18n check

**Files:** none changed

- [ ] **Step 1: Start dev and fetch Italian locales**

Run:
```bash
cd /data1/tdcweb-dev/frontend && npm run dev &
sleep 3
curl -s http://localhost:9503/it/ | grep -c 'Puoi vedere la musica'
kill %1
```
Expected: `>= 1` (Italian translation rendered server-side).

- [ ] **Step 2: No commit (observational)**

---

### Task 7.7: Final cleanup and handoff

**Files:**
- Update: top-level README or progress note (if applicable)

- [ ] **Step 1: Re-run full unit tests**

Run: `cd /data1/tdcweb-dev/frontend && npm test`
Expected: all green.

- [ ] **Step 2: Lint check**

Run: `cd /data1/tdcweb-dev/frontend && npm run lint 2>&1 || echo 'lint script not defined yet — skip if so'`
If lint exists and fails, fix warnings before closing.

- [ ] **Step 3: Summary commit (if anything to add)**

If README or notes need updating:

```bash
cd /data1/tdcweb-dev
git add <file>
git commit -m "docs: mark Nuxt 4 migration phase 7 smoke tests complete"
```

- [ ] **Step 4: Print a migration summary to the user**

Report to the user:
- Number of commits created across phases 1-7
- Count of files created vs modified
- Test results (N passed)
- Any DoD items from the spec §14 that failed and need follow-up
- Next steps: implement feature pages (locations/:slug, events/:id, artists, blog, admin) as separate feature brainstorms
