# Nuxt 4 Integration — Design Spec

**Date:** 2026-04-23
**Project:** The Dreamer's Cave (tdcweb)
**Status:** Design approved, pending user spec review
**Author:** Alessandro Loria + Claude (brainstorming session)

---

## 1. Purpose

Migrate the TDC frontend from a Vue 3 + Vite SPA to **Nuxt 4** (Vue-based
meta-framework) to gain SSR/SSG/ISR capabilities, out-of-the-box SEO
tooling, and per-route rendering strategies. The Python/Flask backend and
MySQL database remain unchanged.

The migration is a full architectural redesign (not a lift-and-shift):
rendering strategies are reconsidered per route, authentication moves
from session-based to JWT-in-HttpOnly-cookie with a thin BFF layer in
Nuxt for auth only, and all existing Vue scaffold files are ported to
Nuxt conventions with TypeScript.

## 2. Motivation

TDC is a public-facing virtual music club website with:
- 10 themed locations (public content, SEO-sensitive)
- Event calendar integrated with Google Calendar (content that changes
  frequently but not real-time)
- Artist pages, blog, Patreon integration
- In-world Second Life API consumers
- Authenticated areas (user dashboard, staff/admin panels)

A pure SPA built with Vite cannot deliver acceptable SEO for location,
event, artist and blog pages without client-side JavaScript execution —
which hurts rankings and social preview rendering. Nuxt gives us:

- Per-route rendering strategy (SSG / ISR / SSR / SPA)
- First-class SEO tooling (meta tags, sitemap, robots, Schema.org)
- Image optimization (`<NuxtImg>`)
- i18n routing built-in (`/it/`, `/fr/`, `/es/`)
- File-based routing, auto-imports, Nitro server
- Stays inside the Vue ecosystem: Pinia, vue-i18n (wrapped), Tailwind,
  GSAP, Lenis, TipTap, Lucide all work unchanged

React/Next.js was considered and rejected: switching framework would
invalidate the existing Vue-oriented agents (`tdc-frontend-expert`),
skills (`tdc-frontend`), CLAUDE.md conventions, and the pdp-v2.md plan,
with no meaningful technical upside for the animation stack (GSAP +
ScrollTrigger + Lenis are framework-agnostic).

## 3. Scope

**In scope:**
- Complete Nuxt 4 scaffold replacing current `frontend/`
- TypeScript-first configuration
- Per-route rendering strategy via `routeRules`
- Hybrid BFF architecture: Nuxt `server/api/auth/**` handles auth, all
  other requests pass through to Flask directly
- Port the 10 existing Vue scaffold files to Nuxt conventions
- SSR-safe patterns for GSAP, ScrollTrigger, Lenis
- `@nuxtjs/i18n` replacing manual vue-i18n setup
- SEO modules: sitemap, robots, Schema.org (`@nuxtjs/seo`)
- Documentation updates: `CLAUDE.md`, new `pdp-v3.md`,
  `tdc-frontend-expert` agent, `tdc-frontend` skill
- Nginx production config and systemd unit for Nuxt node server
- Smoke test criteria (Definition of Done)

**Out of scope (deferred to feature-specific brainstorms):**
- Implementation of locations / events / artists / blog features
- Admin panel UI
- Patreon / Facebook / Google Calendar integration UI
- Second Life API endpoint shape (stays in Flask)
- Full auth flow implementation (spec defines architecture; feature
  brainstorm covers OAuth providers, password reset, email verify)

## 4. Locked decisions

| # | Decision | Value | Reason |
|---|---|---|---|
| 1 | Keep Vue ecosystem | Yes | Existing agents, skills, CLAUDE.md, pdp invest in Vue |
| 2 | Meta-framework | Nuxt 4 | Stable since June 2025, `app/` layer standard |
| 3 | Language | TypeScript (strict) | Type safety across Flask/Nuxt boundary, ecosystem is TS-first |
| 4 | Backend | Flask 3 (unchanged) | Working, documented, invested |
| 5 | Architecture | Hybrid BFF (auth only) | Best tradeoff: simple for public data, secure for auth |
| 6 | Access token | JWT, HttpOnly cookie `tdc_access`, 15 min | Matches existing CLAUDE.md policy |
| 7 | Refresh token | JWT, HttpOnly cookie `tdc_refresh`, 7 days, Path=/api/auth | Narrow scope, rotation on each use |
| 8 | CSRF | SameSite=Lax (access) / Strict (refresh) + Origin check | No separate CSRF token needed for same-site |
| 9 | i18n | `@nuxtjs/i18n`, `prefix_except_default` | `/` = EN, `/it/`, `/fr/`, `/es/` |
| 10 | State | Pinia via `@pinia/nuxt` | No change from pdp-v2 |
| 11 | Animations | GSAP + ScrollTrigger + Lenis (unchanged stack) | Plugins are `.client.ts` (excluded from SSR bundle) |
| 12 | Rich text | `@tiptap/vue-3` wrapped in `<ClientOnly>` | Heavy, DOM-dependent, admin-only |
| 13 | Forms | `vee-validate` + `zod` | Type-safe validation, same schema client+server |
| 14 | pdp-v2.md handling | Create new `pdp-v3.md` | v2 stays historical, v3 is Nuxt-native |
| 15 | Migration approach | Nuke & restart | Scaffold is 10 untracked files, low cost |

## 5. System topology

### 5.1 Port allocation

| | Dev | Prod |
|---|---|---|
| Flask | `:9502` (unchanged) | `:9500` (unchanged, gunicorn systemd) |
| Nuxt | `:9503` (replaces Vite) | `:9501` (new, node systemd) |
| MySQL | `:3306` | `:3306` |

Nuxt takes `:9503` in dev so the existing Vite slot is reused.
Production `:9501` is adjacent to Flask `:9500`. Both backends bind to
`127.0.0.1` in production (firewalled from the outside); only nginx
and Nuxt's node process can reach Flask.

### 5.2 Development flow

```
[Browser] --> :9503 Nuxt dev (nitro + Vite HMR)
                  |
                  +-- /api/**  (except /api/auth/**, /api/revalidate)
                  |           --> routeRules.proxy --> :9502 Flask
                  |
                  +-- /api/auth/**, /api/revalidate
                              --> Nuxt server/api/ (BFF)
                              --> internally $fetch to :9502 Flask
```

> Earlier drafts of this section used `nitro.devProxy` for the public
> read endpoints. Phase 4 end-of-phase integration smoke surfaced a
> routing precedence bug: Nitro's `devProxy` registers as h3 middleware
> BEFORE the worker that hosts `server/api/*` routes, so a catch-all
> `/api` rule silently swallows `/api/auth/**` and `/api/revalidate`
> (the BFF) before Nitro can route them. POST `/api/auth/login` would
> bypass the BFF entirely. As-built `nuxt.config.ts` therefore uses
> per-prefix `routeRules.proxy` entries (one per Flask read endpoint --
> `/api/locations`, `/api/events`, `/api/health`, `...`); these are
> integrated with the route registry, so static server routes win over
> the glob proxy rules. In production Apache (sec 5.3) does the same
> split at the reverse-proxy layer, so the dev-mode `routeRules.proxy`
> entries are the dev analog of the prod Apache rules, not a
> production codepath.

### 5.3 Production flow

```
[Browser] ──► :443 nginx
                 │
                 ├─► /_nuxt/, /assets  → static file serving
                 ├─► /api/auth/**      → :9501 Nuxt (BFF)
                 ├─► /api/revalidate   → :9501 Nuxt (on-demand ISR)
                 ├─► /api/**           → :9500 Flask
                 └─► /                 → :9501 Nuxt (SSR/SSG/SPA per route)
```

SSR data fetches from Nuxt server to Flask bypass nginx (direct loopback
call, lower latency).

## 6. Directory structure (Nuxt 4 `app/` layer)

```
frontend/
├── app/
│   ├── app.vue                       Root component
│   ├── app.config.ts                 Runtime config (theme, feature flags)
│   ├── error.vue                     Global error page (404/500)
│   ├── pages/                        File-based routing
│   │   ├── index.vue                 /                    (SSG)
│   │   ├── locations/
│   │   │   ├── index.vue             /locations           (SSG)
│   │   │   └── [slug].vue            /locations/:slug     (SSG)
│   │   ├── events/
│   │   │   ├── index.vue             /events              (ISR 5min)
│   │   │   └── [id].vue              /events/:id          (ISR 5min)
│   │   ├── artists/
│   │   │   ├── index.vue             /artists             (SSG)
│   │   │   └── [slug].vue            /artists/:slug       (SSG)
│   │   ├── blog/
│   │   │   ├── index.vue             /blog                (ISR 1h + on-demand)
│   │   │   └── [slug].vue            /blog/:slug          (ISR 1h + on-demand)
│   │   ├── auth/
│   │   │   ├── login.vue
│   │   │   ├── register.vue
│   │   │   └── callback/[provider].vue
│   │   ├── dashboard/                All SPA (ssr:false via routeRules)
│   │   │   ├── index.vue
│   │   │   ├── favorites.vue
│   │   │   ├── notifications.vue
│   │   │   └── profile.vue
│   │   └── admin/                    All SPA
│   │       ├── index.vue
│   │       ├── events/
│   │       ├── locations/
│   │       ├── blog/
│   │       └── users.vue
│   ├── layouts/
│   │   ├── default.vue
│   │   ├── auth.vue
│   │   ├── dashboard.vue
│   │   └── admin.vue
│   ├── components/
│   │   ├── common/                   AppHeader, AppFooter, LangSwitcher
│   │   ├── landing/                  Hero, FeatureGrid, Parallax
│   │   ├── locations/                LocationCard, MoodBadge
│   │   ├── events/                   EventCard, EventCalendar
│   │   ├── artists/
│   │   ├── blog/
│   │   ├── auth/
│   │   ├── user/
│   │   ├── admin/
│   │   └── ui/                       Button, Input, Modal (primitives)
│   ├── composables/
│   │   ├── useLocationTheme.ts       CSS vars for 10 location themes
│   │   ├── useScrollAnimation.ts     GSAP ScrollTrigger wrapper
│   │   ├── useSmoothScroll.ts        Lenis wrapper
│   │   ├── useAuth.ts                Auth state from cookie
│   │   └── useApi.ts                 $fetch wrapper with 401 auto-refresh
│   ├── stores/                       Pinia
│   │   ├── auth.ts
│   │   ├── locale.ts
│   │   └── ui.ts
│   ├── middleware/                   Navigation guards
│   │   ├── auth.ts
│   │   ├── admin.ts
│   │   └── staff.ts
│   ├── plugins/
│   │   ├── gsap.client.ts            Register GSAP + ScrollTrigger (client-only)
│   │   └── lenis.client.ts           Init Lenis, sync with gsap.ticker
│   ├── utils/                        Pure helpers (auto-imported by Nuxt)
│   │   └── auth-guard.ts             buildLoginRedirect / decide{Auth,Admin,Staff}Outcome (Phase 4)
│   ├── assets/
│   │   └── css/
│   │       ├── main.css              Tailwind layers
│   │       └── themes/               CSS vars per location
│   └── types/                        Shared TypeScript types
│       ├── api.ts
│       ├── location.ts
│       ├── event.ts
│       └── user.ts
├── server/                           Nitro server (server-only)
│   ├── api/
│   │   ├── auth/                     BFF (only auth routes)
│   │   │   ├── login.post.ts
│   │   │   ├── logout.post.ts
│   │   │   ├── refresh.post.ts
│   │   │   └── me.get.ts
│   │   └── revalidate.post.ts        On-demand ISR invalidation (admin)
│   ├── middleware/
│   │   └── auth-forward.ts           Reads cookie, adds Bearer to outbound $fetch
│   └── utils/
│       ├── flask-client.ts           $fetch wrapper with baseURL = Flask
│       └── cookies.ts                HttpOnly set/clear helpers
├── i18n/
│   └── locales/
│       ├── en.json
│       ├── it.json
│       ├── fr.json
│       └── es.json
├── public/                           Static files (favicon, robots.txt)
├── tests/
│   ├── unit/                         vitest for composables/utils/stores
│   └── e2e/                          Playwright per CLAUDE.md
├── nuxt.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── eslint.config.ts
├── package.json
└── .env.example
```

**File size limits** (CLAUDE.md compliance):
- `.vue` components: max 500 lines → split into sub-components or composables
- `.ts` files: max 800 lines → split into modules
- Existing large files (if any emerge): pragmatic, do not refactor
  unless necessary

### 6.1 Mapping: existing files → Nuxt layout

| Current (Vue+Vite) | Nuxt 4 |
|---|---|
| `src/App.vue` | `app/app.vue` |
| `src/main.js` | absorbed by Nuxt runtime (removed) |
| `src/router/index.js` | removed (file-based routing) |
| `src/stores/index.js` | split into `app/stores/auth.ts`, `locale.ts`, `ui.ts` |
| `src/composables/useApi.js` | `app/composables/useApi.ts` (with TS + 401 retry) |
| `src/views/HomePage.vue` | `app/pages/index.vue` |
| `src/views/EventsPage.vue` | `app/pages/events/index.vue` |
| `src/views/LocationsPage.vue` | `app/pages/locations/index.vue` |
| `src/components/common/AppHeader.vue` | `app/components/common/AppHeader.vue` |
| `src/components/common/AppFooter.vue` | `app/components/common/AppFooter.vue` |

The current `frontend/` directory will be renamed to
`frontend.vue-backup/` (untracked) and kept locally for reference.

## 7. Rendering strategy

### 7.1 Route map

| Route pattern | Strategy | Cache | Motivation |
|---|---|---|---|
| `/` | SSG | build-time | Apple-style landing, rarely changes |
| `/locations`, `/locations/**` | SSG | build-time + on-demand revalidate | 10 fixed locations, admin-edited |
| `/events`, `/events/**` | ISR | SWR 5 min | Changes often, not real-time |
| `/artists`, `/artists/**` | SSG | build-time + on-demand revalidate | Few changes |
| `/blog`, `/blog/**` | ISR + on-demand | SWR 1h + revalidate on publish | Fast publish, SEO critical |
| `/auth/login`, `/auth/register` | SSR (no cache) | — | Dynamic, light |
| `/auth/callback/**` | SSR (no cache) | — | OAuth flow |
| `/dashboard`, `/dashboard/**` | SPA (`ssr:false`) | — | Auth-gated, no SEO value |
| `/admin`, `/admin/**` | SPA (`ssr:false`) | — | Auth-gated, heavy client-side |
| `/api/auth/**` | Nitro server routes | — | BFF |
| `/api/revalidate` | Nitro server route | — | Admin on-demand cache invalidation |
| `/**` fallback | SSR | — | Safe default |

### 7.2 `nuxt.config.ts` routeRules (excerpt)

```typescript
export default defineNuxtConfig({
  routeRules: {
    '/':                { prerender: true },
    '/locations':       { prerender: true },
    '/locations/**':    { prerender: true },
    '/artists':         { prerender: true },
    '/artists/**':      { prerender: true },
    '/about':           { prerender: true },
    '/contact':         { prerender: true },

    '/events':          { swr: 300 },
    '/events/**':       { swr: 300 },
    '/blog':            { swr: 3600 },
    '/blog/**':         { swr: 3600 },

    '/auth/login':      { ssr: true, swr: false },
    '/auth/register':   { ssr: true, swr: false },
    '/auth/callback/**':{ ssr: true, swr: false },

    '/dashboard':       { ssr: false },
    '/dashboard/**':    { ssr: false },
    '/admin':           { ssr: false },
    '/admin/**':        { ssr: false },

    '/**':              { ssr: true },
  },
  nitro: {
    prerender: {
      crawlLinks: true,
      routes: ['/sitemap.xml'],
      failOnError: false,
    },
  },
})
```

### 7.3 On-demand revalidation

```typescript
// server/api/revalidate.post.ts
//
// Cache-key format derived from the Nitro source rather than guessed.
// Nitro stores SWR / cached route entries under unstorage keys of the
// form:
//
//   cache:nitro:routes:_:<escapedPathname>.<hash>.json
//
// where <escapedPathname> = escapeKey(decodeURI(pathname)) (strips \W,
// truncated to 16 chars; falls back to "index" when the strip empties
// the string), and <hash> is a content hash of the full request URL
// (path + query + varies). Source:
//   - nitropack/dist/runtime/internal/cache.mjs lines 29 and 124-145
//     (escapeKey, key construction)
//   - nitropack/dist/runtime/internal/app.mjs line 131
//     (default group name "nitro/routes")
// On-disk layout `.nuxt/cache/nitro/routes/_/<pathname>.<hash>.json`
// confirms the shape.
//
// Implication: an admin-supplied path does not map to a single key (a
// route may have several cached variants per query string / vary header).
// We therefore list keys under the per-path prefix and remove every
// match, rather than `removeItem(<single-key>)`. If Nitro changes its
// key format, this handler silently no-ops -- the worst case is
// staleness until the next SWR tick, never wrong content.
import { defineEventHandler } from 'h3'
import { z } from 'zod'

const ESCAPE_NON_WORD = /\W/g

// Mirror nitropack's escapeKey() exactly so our prefix matches what
// Nitro wrote.
const encodePathname = (path: string): string => {
  const pathname = decodeURI(path.split('?')[0] ?? path)
  const stripped = pathname.replace(ESCAPE_NON_WORD, '').slice(0, 16)
  return stripped || 'index'
}

const revalidateSchema = z.object({
  path: z.string().min(1).max(500).startsWith('/'),
})

export default defineEventHandler(async (event) => {
  await requireAdmin(event)
  const { path } = await readValidatedBody(event, (input) =>
    revalidateSchema.parse(input),
  )

  const encoded = encodePathname(path)
  // Within the `cache:nitro:routes` storage mount, keys lose the mount
  // prefix; the actual key is `_:<encoded>.<hash>.json`. We list under
  // the default group `_` and filter by `_:<encoded>.` prefix.
  const storage = useStorage('cache:nitro:routes')
  const allKeys = await storage.getKeys('_')
  const prefix = `_:${encoded}.`
  const matching = allKeys.filter((k) => k.startsWith(prefix))
  await Promise.all(matching.map((k) => storage.removeItem(k)))

  return { revalidated: path }
})
```

Trigger: when an admin saves a location / artist / event / blog post via
the admin panel, the client POSTs `/api/revalidate` with the affected
path(s). Nitro cache is cleared for that path. The next public request
regenerates.

> Earlier drafts of this section showed
> `storage.removeItem('nitro:routes:${path}.json')`. That key shape was
> a guess; the as-built handler above (Phase 4 Task 4.3) follows the
> Nitro source verbatim. Reconciled at Phase 4 docs-sync.

### 7.4 SEO modules

- `@nuxtjs/seo` — umbrella: `useSeoMeta()`, `useSchemaOrg()`,
  `<NuxtSeoMeta>`
- `@nuxtjs/sitemap` — dynamic sitemap with DB-backed slugs
- `@nuxtjs/robots` — `Disallow: /dashboard, /admin, /api/auth`
- Schema.org JSON-LD per page type:
  - Locations → `Place` + `Organization`
  - Events → `Event` with `location`, `performer`, `startDate`
  - Artists → `MusicGroup` or `Person` with `sameAs` social links
  - Blog posts → `BlogPosting`
- Open Graph + Twitter Cards via `useSeoMeta()` per route, with
  `ogImage` computed from location hero / event poster / artist photo

## 8. Data flow and authentication

### 8.1 Public data fetching

```typescript
// app/pages/locations/[slug].vue
<script setup lang="ts">
const route = useRoute()
const { data: location, error } = await useFetch<Location>(
  `/api/locations/${route.params.slug}`,
  { key: `location-${route.params.slug}` }
)
</script>
```

- In SSR: Nuxt server calls `http://localhost:9500/api/locations/...`
  directly (server-to-server, bypasses nginx).
- In client: `/api/...` is a relative path resolved via nginx (prod) or
  nitro devProxy (dev).
- `useFetch` deduplicates: after hydration the client does **not** re-fetch.

### 8.2 Authentication architecture (hybrid BFF)

Only auth routes pass through Nuxt's BFF. All other data fetches go
directly to Flask with the cookie attached.

**Login flow:**

```
Browser
  │  POST /api/auth/login {email, password}
  ▼
Nuxt server/api/auth/login.post.ts
  │  $fetch POST http://localhost:9500/api/auth/login (server-to-server)
  ▼
Flask validates, returns {access, refresh, user}
  │
  ▼
Nuxt sets two cookies on the response:
  Set-Cookie: tdc_access=<jwt>;  HttpOnly; Secure; SameSite=Lax;
                Path=/; Max-Age=900
  Set-Cookie: tdc_refresh=<jwt>; HttpOnly; Secure; SameSite=Strict;
                Path=/api/auth; Max-Age=604800
Returns 200 {user} to browser.
```

**Token semantics:**
- **Access token**: 15 min, `tdc_access` cookie, sent with every request
  whose Path matches `/`. Nuxt server middleware reads it and forwards
  as `Authorization: Bearer` to Flask during SSR. The browser attaches
  it automatically on direct client→Flask calls (same origin via nginx).
- **Refresh token**: 7 days, `tdc_refresh` cookie with
  `Path=/api/auth` and `SameSite=Strict`. The browser only sends it to
  refresh endpoints. Rotation on each refresh: old refresh token is
  invalidated server-side, new one issued.
- **Logout**: `POST /api/auth/logout` → Flask invalidates both tokens
  (revocation list), Nuxt clears both cookies.

**CSRF:** `SameSite=Lax` on access + `Strict` on refresh prevent CSRF
from third-party origins for same-site requests. Flask additionally
verifies the `Origin` header matches an allowlist. No explicit CSRF
token needed.

### 8.3 Server middleware forwarding auth

The auth-forward middleware populates `event.context.flaskHeaders` for
every incoming request that carries an access cookie. Server route
handlers then pass those headers explicitly when they call Flask.

```typescript
// server/middleware/auth-forward.ts
export default defineEventHandler(async (event) => {
  const access = getCookie(event, 'tdc_access')
  if (access) {
    event.context.flaskHeaders = { Authorization: `Bearer ${access}` }
  }
})
```

```typescript
// server/utils/flask-client.ts
import type { H3Event } from 'h3'

export const flaskFetch = <T = unknown>(
  url: string,
  event: H3Event,
  options: Parameters<typeof $fetch<T>>[1] = {},
) => {
  const { flaskUrl } = useRuntimeConfig()          // resolved per call, SSR-safe
  const flaskHeaders = (event.context.flaskHeaders ?? {}) as Record<string, string>
  return $fetch<T>(url, {
    baseURL: flaskUrl,                             // env: NUXT_FLASK_URL
    ...options,
    headers: { ...flaskHeaders, ...(options.headers ?? {}) },
  })
}
```

Usage inside a server route:

```typescript
// server/api/user/favorites.get.ts   (example, not part of scope)
export default defineEventHandler(async (event) => {
  return flaskFetch<Favorite[]>('/api/user/favorites', event)
})
```

This pattern keeps the event threading explicit (auditable) and avoids
relying on `$fetch.create` hooks that do not have access to the request
event's context.

### 8.4 Client-side auto-refresh on 401

```typescript
// app/composables/useApi.ts
/**
 * Extension of Nuxt $fetch options carrying a `_retry` marker that
 * `onResponseError` uses to guard against infinite 401 retry loops.
 * Derived from $fetch's own parameter type so it stays aligned with
 * Nitro's NitroFetchOptions (which narrows `method` to a literal
 * union, unlike ofetch's wider FetchOptions). Exported so tests can
 * build typed mock contexts without `as any`.
 */
export type RetryableFetchOptions = NonNullable<Parameters<typeof $fetch>[1]> & { _retry?: boolean }

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

**Phase 3 clarifications (implementation codification).**

The spec originally spelled the retry marker as `options._retry` with
no type extension. Phase 3 Task 3.8 delivered the implementation with
three binding refinements, now part of the contract:

1. `RetryableFetchOptions` exported, derived from
   `NonNullable<Parameters<typeof $fetch>[1]>`. Reviewer-Phase-2
   feedback forbade `as any` casts on the retry marker. Deriving from
   the `$fetch` parameter type rather than ofetch's `FetchOptions`
   keeps `method` narrowed to the Nitro literal union.
2. Retry path calls `useApi()(request, opts)` — the wrapper re-enters
   itself so `credentials: 'include'` and any future interceptor
   logic are preserved across the retried request. The `_retry` flag
   set to `true` before the recursive call prevents infinite loops
   (unit-tested in `tests/unit/useApi.test.ts`).
3. Explicit `: ReturnType<typeof $fetch.create>` return type
   annotation on `useApi()`. Without it TS7023 fires on the recursive
   self-reference. The explicit annotation names the Nitro wrapper
   type without importing internal aliases.

These refinements are non-optional under TypeScript strict mode.

### 8.5 Auth-gated pages (dashboard / admin)

```typescript
// app/pages/dashboard/favorites.vue
<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
const api = useApi()
const { data: favorites } = await api<Favorite[]>('/api/user/favorites')
</script>
```

```typescript
// app/middleware/auth.ts
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

## 9. SSR pitfalls and client-only patterns

### 9.1 GSAP + ScrollTrigger

```typescript
// app/plugins/gsap.client.ts       (suffix .client → excluded from SSR bundle)
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

export default defineNuxtPlugin(() => {
  gsap.registerPlugin(ScrollTrigger)
  return { provide: { gsap, ScrollTrigger } }
})
```

```typescript
// app/composables/useScrollAnimation.ts
export function useScrollAnimation() {
  const { $gsap, $ScrollTrigger } = useNuxtApp()
  const ctx = ref<gsap.Context | null>(null)

  const animateReveal = (selector: string, options = {}) => {
    if (!import.meta.client) return
    ctx.value = $gsap.context(() => {
      $gsap.from(selector, {
        y: 100, opacity: 0, duration: 1, stagger: 0.2,
        scrollTrigger: { trigger: selector, start: 'top 80%' },
        ...options,
      })
    })
  }

  onBeforeUnmount(() => {
    ctx.value?.revert()
    $ScrollTrigger.refresh()
  })

  return { animateReveal }
}
```

Rationale: `gsap.context()` is mandatory for cleanup. Otherwise
ScrollTrigger instances leak across navigations and cause phantom
triggers that break scroll behavior after a few route changes.

### 9.2 Lenis smooth scroll

```typescript
// app/plugins/lenis.client.ts
import Lenis from 'lenis'

export default defineNuxtPlugin(() => {
  const lenis = new Lenis({ duration: 1.2, smoothWheel: true })
  const { $gsap } = useNuxtApp()
  $gsap.ticker.add((time) => lenis.raf(time * 1000))
  $gsap.ticker.lagSmoothing(0)

  const router = useRouter()
  router.beforeEach((to) => {
    if (to.path.startsWith('/admin') || to.path.startsWith('/dashboard')) {
      lenis.stop()
    } else {
      lenis.start()
    }
  })

  return { provide: { lenis } }
})
```

Disabling Lenis on admin/dashboard avoids smooth-scroll interference
with data tables and form scroll-into-view.

**Phase 3 addition — `prefers-reduced-motion` short-circuit.** When
the media query `(prefers-reduced-motion: reduce)` matches, the
plugin skips construction entirely and provides `{ lenis: null }`.
This is a strictly-additive safety layer so wheel/touch smooth-scroll
is never active for users who have opted out of animation. Consumers
(`useSmoothScroll`, `useScrollAnimation`) also guard the same media
query — the three-layer discipline is documented in
`docs/frontend/nuxt-playbook.md §9`.

### 9.3 i18n + SSR

```typescript
// nuxt.config.ts (i18n excerpt)
i18n: {
  locales: [
    { code: 'en', iso: 'en-US', file: 'en.json', name: 'English' },
    { code: 'it', iso: 'it-IT', file: 'it.json', name: 'Italiano' },
    { code: 'fr', iso: 'fr-FR', file: 'fr.json', name: 'Français' },
    { code: 'es', iso: 'es-ES', file: 'es.json', name: 'Español' },
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
}
```

Detection order on first request: URL prefix → `i18n_redirected` cookie
→ `Accept-Language` header → default `en`.

DB-backed translations (`*_translations` tables): server-side
`useFetch('/api/locations/...')` includes `Accept-Language: ${locale.value}`
header; Flask returns translated payload. ISR cache keys are separated
per locale automatically by `@nuxtjs/i18n`.

### 9.4 Hydration mismatch — forbidden patterns

| Anti-pattern | Fix |
|---|---|
| `{{ new Date().toLocaleString() }}` in template | Format in `onMounted` or wrap in `<ClientOnly>` |
| `{{ Math.random() }}` | Avoid; or `<ClientOnly>` |
| `window.matchMedia(...)` in `setup()` | `if (import.meta.client)` or move to `onMounted` |
| `localStorage` in `setup()` | Only in `onMounted` |
| Canvas/video/WebGL components at top level | `<ClientOnly>` with a skeleton `#fallback` |

### 9.5 Client-only wrapper pattern

```vue
<ClientOnly>
  <InteractiveMap :location="location" />
  <template #fallback>
    <div class="map-skeleton" aria-hidden="true" />
  </template>
</ClientOnly>
```

### 9.6 Location theming (SSR-safe)

```vue
<script setup lang="ts">
const { data: location } = await useFetch<Location>(...)
useHead({
  bodyAttrs: { 'data-location': location.value?.slug },
})
</script>
```

CSS in `app/assets/css/themes/` applies colors via
`[data-location="dreamerscave"] { --color-primary: #0891b2 }`. Zero
JavaScript at paint time, zero FOUC, all server-rendered.

### 9.7 TipTap (blog editor)

Always inside a page with `ssr: false` (admin) or wrapped in
`<ClientOnly>`. TipTap references `document` and `window` extensively
and is too heavy to SSR.

## 10. Migration plan

### 10.1 Phases

**Phase 1 — Backup and scaffold** (~30 min)
- Rename `frontend/` to `frontend.vue-backup/` (stays local, untracked)
- Run `npx nuxi@latest init frontend` (Nuxt 4 is the default; the
  scaffolded project uses the `app/` layer)
- Keep `npm` as the package manager for consistency with the existing
  project (`package-lock.json` present); when prompted by `nuxi init`,
  choose `npm`
- Install modules: `@nuxtjs/i18n`, `@pinia/nuxt`, `@vueuse/nuxt`,
  `@nuxt/image`, `@nuxtjs/tailwindcss`, `@nuxtjs/seo`, `@nuxtjs/robots`,
  `@nuxtjs/sitemap`
- Install runtime: `gsap`, `lenis`, `@tiptap/vue-3`,
  `@tiptap/starter-kit`, `@tiptap/extension-image`,
  `@tiptap/extension-link`, `@tiptap/extension-placeholder`,
  `lucide-vue-next`, `zod`, `vee-validate`, `@vee-validate/zod`
- Commit baseline scaffold

**Phase 2 — Core configuration** (~45 min)
- `nuxt.config.ts` with full routeRules, i18n config, modules,
  nitro devProxy `/api/**` → Flask
- `tailwind.config.ts` (ported from backup, includes location theme
  tokens)
- `tsconfig.json` strict mode
- `eslint.config.ts` + Prettier
- `.env.example` and local `.env` (`NUXT_PUBLIC_API_BASE`, `FLASK_URL`)
- `app/plugins/gsap.client.ts` and `app/plugins/lenis.client.ts`
- `server/utils/flask-client.ts` and
  `server/middleware/auth-forward.ts`

**Phase 3 — Port existing files** (~1h)
- `app/app.vue` from `App.vue`
- `app/pages/index.vue` from `HomePage.vue` (add `useSeoMeta`)
- `app/pages/events/index.vue` from `EventsPage.vue`
- `app/pages/locations/index.vue` from `LocationsPage.vue`
- `app/components/common/AppHeader.vue`, `AppFooter.vue`
- `app/composables/useApi.ts` with TS types and 401 auto-refresh
- `app/stores/` split into `auth.ts`, `locale.ts`, `ui.ts`
- `i18n/locales/*.json` ported from `frontend.vue-backup/src/i18n/`
- Remove `router/index.js` concept (Nuxt file-based)

**Phase 4 — BFF auth and middleware** (~1h)
- `server/api/auth/login.post.ts`
- `server/api/auth/logout.post.ts`
- `server/api/auth/refresh.post.ts`
- `server/api/auth/me.get.ts`
- `server/api/revalidate.post.ts`
- `app/middleware/auth.ts`, `admin.ts`, `staff.ts`
- `app/composables/useAuth.ts`

**Phase 5 — Documentation and agents** (~30 min)
- Update `CLAUDE.md`:
  - Stack table → Nuxt 4 + Vite
  - New "Rendering Strategy" section
  - New "SSR Client-Only Rules" section
- Create `docs/plans/pdp-v3.md` (v2 stays as historical reference):
  - Full architectural doc, Nuxt-native
  - Rendering strategy, SSR architecture, deployment
- Update `.claude/agents/tdc-frontend-expert.md`:
  - Context switch Vue+Vite SPA → Nuxt 4 + TypeScript
  - Add patterns: `useFetch`, `$fetch`, client-only plugins, route
    meta, middleware
- Update `.claude/skills/tdc-frontend/` (if local):
  - Templates for SSR page, client-only component, SSR-safe composable
- Reference this spec as `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md`

**Phase 6 — Nginx and systemd** (~45 min)
- `nginx/thedreamerscave.conf` (production config, see §11)
- `systemd` unit `tdcweb-frontend.service` for Nuxt node server
- Deploy workflow documentation

**Phase 7 — Smoke tests** (~30 min)
- `nuxi dev` starts on `:9503`, HMR works
- Curl SSR verification: `curl :9503/locations/dreamerscave | grep '<h1>'`
- Auth flow round-trip via Playwright
- 404 pages and i18n redirects
- `nuxi build && node .output/server/index.mjs` on `:9501` starts clean
- `nginx -t` validates prod config

**Total estimated effort: ~4h30**

Each phase ends with an atomic commit. Fix-Test-Verify rule applies:
test between phases, only proceed if green.

### 10.2 Rollback strategy

If migration fails at any phase before phase 5 (docs not yet updated):
- Delete `frontend/` (Nuxt scaffold)
- Rename `frontend.vue-backup/` back to `frontend/`
- No git history affected (scaffold was untracked)

After phase 5 (docs updated): rollback also reverts documentation
commits. Always possible via `git revert` since each phase is atomic.

## 11. Nginx production configuration

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

    location /_nuxt/ {
        alias /data1/tdcweb/frontend/.output/public/_nuxt/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # BFF routes go to Nuxt node server
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

    # Everything else → Nuxt node
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

## 12. systemd unit for Nuxt node server (production)

```ini
# /etc/systemd/system/tdcweb-frontend.service
[Unit]
Description=TDC Nuxt Frontend
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

[Install]
WantedBy=multi-user.target
```

## 13. Testing strategy

- **Unit** (`vitest` via `@nuxt/test-utils`): composables, stores,
  utils, server routes (auth handlers, revalidate handler)
- **Component** (`@vue/test-utils` + `vitest`): key components such as
  `AppHeader`, `LocationCard`, auth forms
- **E2E** (Playwright per CLAUDE.md): full auth flow, navigation
  across rendered strategies, admin revalidate, i18n switching
- **SSR verification** (smoke): `curl :9503/<route> | grep <expected>`
  as part of phase 7 and future CI

## 14. Definition of Done

The migration is complete when **all** of the following pass:

- [ ] `npm run dev` (wraps `nuxi dev`) starts on `:9503`, HMR works
- [ ] `curl :9503/locations/dreamerscave | grep '<h1>'` returns the
      location title (SSR proof)
- [ ] `curl :9503/dashboard` returns SPA shell without hydrated auth
      data (auth leak proof)
- [ ] Login round-trip: `POST /api/auth/login` sets HttpOnly cookies;
      `GET /api/auth/me` returns the user
- [ ] `nuxi build` completes; `node .output/server/index.mjs` starts on
      `:9501` without errors
- [ ] `nginx -t` validates production config
- [ ] `/sitemap.xml` reachable and contains all 10 location slugs
- [ ] Browser console on `/`, `/locations`, `/events` has zero errors
- [ ] GSAP animations work on `/locations/dreamerscave` with no
      phantom ScrollTrigger instances after navigation
- [ ] `/it/locations` renders Italian translations from DB
- [ ] Core Web Vitals sanity: LCP < 2.5s on cold `/` (lab), CLS < 0.1

## 15. Out-of-scope follow-ups

These are explicitly deferred and should be brainstormed separately:
- OAuth provider implementation (Google, Discord, Facebook)
- Password reset / email verification flows
- Full admin panel UI (users, events, locations, blog editor)
- Second Life in-world API contract details (stays Flask-only)
- Patreon webhook handling
- Facebook automated posting
- Performance budget and CDN strategy beyond what Nuxt gives by default
- A/B testing infrastructure
- Analytics integration

## 16. References

- Nuxt 4 docs: https://nuxt.com/docs (v4 release June 2025)
- `@nuxtjs/i18n` v9
- `@nuxtjs/seo` umbrella module
- GSAP + Nuxt integration: plain `gsap` package is sufficient; premium
  plugins (SplitText, MorphSVG) are not in scope for this migration
- CLAUDE.md — project conventions and MCP tooling
- `docs/plans/pdp-v2.md` — historical project plan (v2, pre-Nuxt)
- `docs/plans/pdp-v3.md` — to be created, Nuxt-native project plan
