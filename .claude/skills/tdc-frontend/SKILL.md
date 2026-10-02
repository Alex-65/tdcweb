---
name: tdc-frontend
description: Create Nuxt 4 frontend code for The Dreamer's Cave. Use for pages, components, composables, stores, server BFF handlers, animations, and theming.
---

# TDC Frontend Developer (Nuxt 4)

Expert skill for creating Nuxt 4 frontend code for The Dreamer's Cave virtual music club website.

## Trigger

Use this skill when:
- User asks to create or modify frontend code under `frontend/app/**` or `frontend/server/**`
- User says "/frontend", "/tdc-frontend", "/nuxt", "/vue", or "/component"
- User asks for pages, layouts, components, composables, Pinia stores, middleware, plugins, or Nitro server routes
- User wants to implement animations (GSAP / ScrollTrigger / Lenis), theming, i18n, SEO, or BFF auth
- User asks about `useFetch`, `useApiFetch`, `$fetch`, `useAuth`, `useSeoMeta`, vee-validate + zod, or TipTap

## Project Context

**The Dreamer's Cave** -- website for a virtual music club in Second Life.
**Motto:** "You Can See The Music"

### Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Meta-framework | **Nuxt 4** | `app/` layer, `compatibilityVersion: 4`, `compatibilityDate: '2026-04-01'` |
| UI | Vue 3 Composition API | `<script setup lang="ts">` always |
| Language | **TypeScript strict** | `typescript.strict: true`, no `any` |
| Build | Vite under Nuxt | HMR, ESM, tree-shaking |
| Styling | **Tailwind CSS v4 CSS-first** via `@tailwindcss/vite` | NOT `@nuxtjs/tailwindcss`; tokens live in `app/assets/css/main.css` `@theme` block |
| Theming | CSS variables under `[data-location="<slug>"]` | Set on `<body>` via `useLocationTheme(slug)` -> `useHead({ bodyAttrs })` -- zero-JS at paint, SSR-safe |
| Animations | GSAP + ScrollTrigger + Lenis | `.client.ts` plugins only; package name `lenis` (NOT `@studio-freight/lenis`) |
| State | Pinia via `@pinia/nuxt` | **Setup syntax only** -- `defineStore('x', () => { ... })` |
| i18n | `@nuxtjs/i18n` | `prefix_except_default` -- EN at `/`, others at `/it/`, `/fr/`, `/es/` |
| SEO | `@nuxtjs/seo` + `@nuxtjs/sitemap` + `@nuxtjs/robots` | `useSeoMeta`, `useSchemaOrg` |
| Image | `@nuxt/image` | `<NuxtImg>` (auto avif/webp) |
| Forms | vee-validate + zod via `toTypedSchema` | Same schema reused server-side via `readValidatedBody` |
| Rich text | `@tiptap/vue-3` | Admin-only, `<ClientOnly>`-wrapped |
| Testing | vitest + `@nuxt/test-utils` + happy-dom (unit) | Playwright 1920x1080 (E2E) |

### Ports

| | Dev | Prod |
|---|---|---|
| Nuxt | `:9503` (`nuxi dev`) | `:9501` (node SSR via systemd) |
| Flask | `:9502` | `:9500` (gunicorn via systemd) |

### File Structure

```
frontend/
|-- app/                         <-- PRIMARY SCOPE (Nuxt 4 `app/` layer)
|   |-- app.vue
|   |-- app.config.ts
|   |-- error.vue
|   |-- assets/
|   |   `-- css/main.css         <-- Tailwind v4 @theme + per-location vars
|   |-- components/              <-- auto-imported, flat naming via components.pathPrefix: false
|   |   |-- AppHeader.vue
|   |   |-- AppFooter.vue
|   |   |-- common/
|   |   |-- locations/
|   |   |-- events/
|   |   `-- forms/
|   |-- composables/             <-- auto-imported
|   |   |-- useApiFetch.ts       <-- envelope-aware Flask fetcher (SSR-aware baseURL)
|   |   |-- useAuth.ts           <-- login/logout/refresh/me (uses useRequestFetch in SSR)
|   |   |-- useLocationTheme.ts  <-- body[data-location=...] via useHead
|   |   |-- useScrollAnimation.ts
|   |   `-- useSmoothScroll.ts
|   |-- middleware/              <-- file-based; opt-in via definePageMeta
|   |   |-- auth.ts              <-- redirect to /auth/login if not authed
|   |   |-- admin.ts             <-- gate by role 'admin'
|   |   `-- staff.ts             <-- gate by role 'staff' or 'admin'
|   |-- pages/                   <-- file-based routing
|   |-- layouts/
|   |-- plugins/
|   |   |-- gsap.client.ts       <-- registers ScrollTrigger
|   |   `-- lenis.client.ts      <-- syncs via gsap.ticker.add
|   |-- stores/                  <-- Pinia setup syntax
|   |   |-- auth.ts
|   |   |-- locale.ts
|   |   `-- ui.ts
|   |-- types/                   <-- shared TS interfaces (User, Location, Event, ApiEnvelope)
|   `-- utils/                   <-- pure helpers (decideAuthOutcome, buildLoginRedirect, ...)
|-- server/                      <-- Nitro BFF
|   |-- api/
|   |   |-- auth/
|   |   |   |-- login.post.ts
|   |   |   |-- logout.post.ts
|   |   |   |-- refresh.post.ts
|   |   |   `-- me.get.ts
|   |   `-- revalidate.post.ts   <-- admin-gated cache invalidation
|   |-- middleware/
|   |   `-- auth-forward.ts      <-- reads tdc_access cookie, stamps event.context.flaskHeaders
|   `-- utils/
|       |-- cookies.ts           <-- setAccessCookie/clearAccessCookie (HttpOnly, Lax/Strict)
|       `-- flask-client.ts      <-- flaskFetch(url, event, options) resilient wrapper
|-- i18n/locales/                <-- en.json, it.json, fr.json, es.json
|-- public/
|-- tests/
|   |-- unit/                    <-- vitest specs
|   `-- e2e/                     <-- Playwright specs
|-- nuxt.config.ts
|-- vitest.config.ts
`-- package.json
```

**File size limits (NEW files only):**
- `.vue` <= 500 lines -- split into sub-components or composables
- `.ts` <= 800 lines -- split into modules
- Existing oversized files: do NOT refactor unless strictly necessary

### Project Constants

| Item | Value |
|---|---|
| Access cookie | `tdc_access` -- HttpOnly, SameSite=Lax, Path=/, 15 min |
| Refresh cookie | `tdc_refresh` -- HttpOnly, SameSite=Strict, Path=/api/auth, 7 d, rotated on use |
| Nuxt -> Flask SSR URL | `NUXT_FLASK_URL` (server-only env, read via `runtimeConfig.flaskUrl`) |
| Public API base | `/api` (relative; resolved via `routeRules.proxy` in dev or Apache `mod_proxy_http` in prod) |
| Default locale | `en` (no prefix); others `/it/`, `/fr/`, `/es/` |
| Locations (8 of 10+ palettes live) | Cosmic/Tech: dreamerscave, dreamvision, evanescence -- Hybrid: livemagic, thelounge -- Warm: arquipelago, noahsark, jazzclub |

---

## Routing

File-based under `app/pages/`. Route options via `definePageMeta`:

```typescript
// app/pages/locations/[slug].vue
definePageMeta({
  layout: 'default',
  // public page -- no middleware
})
```

```typescript
// app/pages/dashboard/index.vue
definePageMeta({
  layout: 'dashboard',
  middleware: ['auth'],          // composes left-to-right
})
```

```typescript
// app/pages/admin/users.vue
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'admin'], // auth first, then role check
})
```

Middleware composition: array order matters. `auth` decides "is the user logged in?" and short-circuits to `/auth/login?redirect=...`. `admin` / `staff` then decide role; the user must already be authed when these run.

### Rendering strategy (declared in `nuxt.config.ts`)

| Route pattern | `routeRules` | TTL / notes |
|---|---|---|
| `/`, `/about`, `/contact` | `{ prerender: true }` | SSG -- build-time |
| `/locations/**`, `/artists/**` | `{ prerender: true }` + on-demand revalidate | SSG, admin-invalidated |
| `/events/**` | `{ swr: 300 }` | ISR 5 min |
| `/blog/**` | `{ swr: 3600 }` + on-demand | ISR 1 h + instant publish |
| `/auth/login`, `/auth/register`, `/auth/callback/**` | `{ ssr: true, swr: false }` | Live SSR per-request |
| `/dashboard/**`, `/admin/**` | `{ ssr: false }` | SPA -- auth-gated, no SEO value |
| `/api/auth/**`, `/api/revalidate` | (Nitro server routes) | Handled by Nuxt |
| `/api/**` (other) | `{ proxy: '<flaskUrl>/api/**' }` | Proxied to Flask |

**Important Phase 4 lesson**: in dev, use `routeRules.proxy` (NOT `nitro.devProxy` catch-all). Precedence ordering: `routeRules` correctly defers `/api/auth/**` and `/api/revalidate` to your Nitro handlers; a top-level `nitro.devProxy['/api']` catch-all would intercept and forward those to Flask, breaking the BFF.

---

## Data Fetching -- decision table

| API | When to use | SSR-aware | Notes |
|---|---|---|---|
| **`useApiFetch<T>(path, opts?)`** | Calling Flask from inside `setup()` -- the default | Yes | Unwraps `{success, data}` envelope to `T`; resolves baseURL via `resolveApiBaseURL(isServer, flaskUrl)` -- on SSR uses `NUXT_FLASK_URL`, on client uses `''` (relative) |
| **`useFetch<T>(path)`** | 3rd-party APIs that don't return the TDC envelope | Yes | Returns full body |
| **`$fetch<T>(path)`** | Imperative calls inside event handlers, `onMounted`, server utilities | No | Caller controls context |
| **`useRequestFetch()()`** | SSR-time calls that must forward the user's cookies (e.g. `useAuth.fetchMe()` during SSR) | Yes | Inherits incoming request headers; required so Nitro `auth-forward` middleware sees the cookie |

**Rules:**
- Always pass an explicit `key` to `useApiFetch` / `useFetch` -- deterministic dedup; required for ISR cache splitting per locale.
- Use `default: () => []` so `data.value` is never `null` -- tighter types, no `v-if` on existence.
- On i18n pages, include `locale.value` in the key and add `Accept-Language: ${locale.value}` header.
- On a hydration round-trip, `useApiFetch` rehydrates from the SSR payload -- no double fetch.

```typescript
const route = useRoute()
const { locale } = useI18n()

const { data: location, error } = await useApiFetch<Location>(
  `/api/locations/${route.params.slug}`,
  {
    key: `location-${route.params.slug}-${locale.value}`,
    headers: { 'Accept-Language': locale.value },
  },
)

if (error.value || !location.value) {
  throw createError({ statusCode: 404, statusMessage: 'Not found', fatal: true })
}
```

---

## SSR Client-Only Rules (NON-NEGOTIABLE -- CLAUDE.md)

The seven hard constraints. Reject code that violates these on review.

1. **GSAP + ScrollTrigger** registered only in `app/plugins/gsap.client.ts`. Animations are declared inside a `gsap.context()` and reverted on unmount:
   ```typescript
   const ctx = $gsap.context(() => {
     $gsap.from('.reveal', { y: 80, opacity: 0, scrollTrigger: { trigger: '.reveal' } })
   })
   onBeforeUnmount(() => ctx.revert())
   ```
   Without `revert()`, ScrollTrigger instances leak across navigations and phantom triggers fire on stale elements.

2. **Lenis** registered in `app/plugins/lenis.client.ts`. Sync to GSAP's RAF -- never a second `requestAnimationFrame`:
   ```typescript
   gsap.ticker.add((time) => lenis.raf(time * 1000))
   gsap.ticker.lagSmoothing(0)
   ```
   Stop Lenis on `/admin/*` and `/dashboard/*` so data tables and keyboard nav use native scroll.

3. **No browser globals at `setup()` top-level**: `window`, `document`, `localStorage`, `sessionStorage`, `matchMedia`, `IntersectionObserver`, `ResizeObserver`, `getComputedStyle`. Move to `onMounted()`, event handlers, or `.client.ts` files.

4. **No hydration-mismatch generators in templates**: `new Date().toLocaleString()`, `Math.random()`, `crypto.randomUUID()`, `navigator.language`. Pattern: `ref` + `onMounted` to assign, OR `<ClientOnly>` with matching-shape `#fallback`.

5. **TipTap / canvas / WebGL** always inside `<ClientOnly>` with a matching-shape fallback (or in a page with `ssr: false`):
   ```vue
   <ClientOnly>
     <TipTapEditor v-model="content" />
     <template #fallback>
       <div class="h-64 bg-surface/50 rounded-lg" aria-hidden="true" />
     </template>
   </ClientOnly>
   ```

6. **Location theming** via `useHead({ bodyAttrs: { 'data-location': slug } })` -- SSR-safe, zero JS at paint. CSS vars in `app/assets/css/main.css` cascade automatically.

7. **Auth tokens in cookies only**: `httpOnly: true, secure: prod, sameSite: 'lax'/'strict'`. Never `localStorage`, never readable by JS, never in response bodies.

---

## Pure-Helper Extraction Pattern (TDC convention)

When wrapping Nuxt auto-imports (`navigateTo`, `useNuxtApp`, `useState`, `useCookie`) for testability, extract pure decision logic into testable functions; the thin wrapper integrates them.

**Why**: `mockNuxtImport` from `@nuxt/test-utils` works for component tests but is brittle for composables that wrap many auto-imports. Pure helpers are trivially unit-testable without a Nuxt test environment.

**Example -- middleware**:

```typescript
// app/utils/auth-decisions.ts -- PURE, testable in isolation
export interface AuthOutcome {
  type: 'pass' | 'redirect'
  to?: string
}

export function decideAuthOutcome(input: {
  isAuthed: boolean
  toFullPath: string
}): AuthOutcome {
  if (input.isAuthed) return { type: 'pass' }
  return { type: 'redirect', to: buildLoginRedirect(input.toFullPath) }
}

export function buildLoginRedirect(toFullPath: string): string {
  return `/auth/login?redirect=${encodeURIComponent(toFullPath)}`
}
```

```typescript
// app/middleware/auth.ts -- thin wrapper, integrates Nuxt auto-imports
export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()
  const outcome = decideAuthOutcome({
    isAuthed: auth.isAuthenticated,
    toFullPath: to.fullPath,
  })
  if (outcome.type === 'redirect') {
    return navigateTo(outcome.to!, { replace: true })
  }
})
```

The unit test imports `decideAuthOutcome` directly -- no Nuxt context needed. Phase 4 used the same pattern for `decideAdminOutcome`, `decideStaffOutcome`, and `buildAuthOps` in `useAuth`.

---

## Pinia (setup syntax only)

```typescript
// app/stores/auth.ts
import { defineStore } from 'pinia'
import type { User } from '~/types/user'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = computed(() => user.value !== null)
  const isAdmin = computed(() => user.value?.role === 'admin')

  const setUser = (u: User | null) => { user.value = u }
  const clear = () => { user.value = null }

  return { user, isAuthenticated, isAdmin, setUser, clear }
})
```

**Consumer pattern**: destructure refs via `storeToRefs`, call actions directly:

```typescript
import { storeToRefs } from 'pinia'

const auth = useAuthStore()
const { user, isAuthenticated } = storeToRefs(auth)  // reactive refs
auth.clear()                                          // actions: not refs
```

---

## Forms (vee-validate + zod)

Same zod schema can be reused server-side via `readValidatedBody`.

```vue
<script setup lang="ts">
import { z } from 'zod'
import { toTypedSchema } from '@vee-validate/zod'
import { useForm } from 'vee-validate'

const schema = toTypedSchema(z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Min 8 characters'),
}))

const { handleSubmit, errors, defineField, isSubmitting } = useForm({
  validationSchema: schema,
})
const [email, emailAttrs] = defineField('email')
const [password, passwordAttrs] = defineField('password')

const { login } = useAuth()
const localePath = useLocalePath()

const onSubmit = handleSubmit(async (v) => {
  await login(v.email, v.password)
  await navigateTo(localePath('/dashboard'))
})
</script>

<template>
  <form @submit="onSubmit" class="space-y-4">
    <div>
      <label for="email" class="sr-only">Email</label>
      <input id="email" v-model="email" v-bind="emailAttrs" type="email"
             :aria-invalid="!!errors.email"
             :aria-describedby="errors.email ? 'email-err' : undefined" />
      <p v-if="errors.email" id="email-err" role="alert" class="text-error text-sm">
        {{ errors.email }}
      </p>
    </div>
    <button :disabled="isSubmitting" type="submit">Sign in</button>
  </form>
</template>
```

---

## SEO (`useSeoMeta` on every public page)

```typescript
useSeoMeta({
  title: location.value.name,
  description: location.value.description,
  ogTitle: location.value.name,
  ogDescription: location.value.description,
  ogImage: location.value.hero_image,
  ogType: 'website',
  twitterCard: 'summary_large_image',
})
```

For rich results add `useSchemaOrg([defineLocalBusiness({ ... })])` (or `defineEvent`, `defineMusicGroup`, `defineArticle`).

`@nuxtjs/sitemap` auto-emits hreflang tags for the four locales when `runtimeConfig.public.siteUrl` is set.

---

## Location Theming

Apply via composable. The composable uses `useHead` so the attribute is set during SSR and flows into the first HTML paint -- no flash.

```typescript
// app/composables/useLocationTheme.ts
import type { MaybeRefOrGetter } from 'vue'
import { toValue } from 'vue'

export function useLocationTheme(slug: MaybeRefOrGetter<string | null | undefined>) {
  useHead(() => ({
    bodyAttrs: {
      'data-location': toValue(slug) ?? '',
    },
  }))
}
```

Consumer:

```typescript
useLocationTheme(computed(() => location.value?.slug))
```

CSS vars in `app/assets/css/main.css` cascade automatically:

```css
@theme {
  --color-primary: var(--tdc-color-primary);
  --color-error:   var(--tdc-color-error); /* semantic, palette-agnostic */
}

@layer base {
  :root {
    --tdc-color-primary: #0891b2;
    --tdc-color-error: #ef4444;
  }
  [data-location="dreamerscave"] {
    --tdc-color-primary: #0891b2;
    --tdc-color-secondary: #06b6d4;
    --tdc-color-accent: #22c55e;
  }
  /* ... 7 more location blocks */
}
```

Slug convention: lowercase, no spaces, no diacritics (`thelounge`, `arquipelago`, `noahsark`, `jazzclub`).

---

## Server Routes (BFF) -- Phase 4 patterns

Only `/api/auth/**` and `/api/revalidate` live as Nitro handlers; everything else passes through to Flask.

### Login handler (canonical)

```typescript
// frontend/server/api/auth/login.post.ts
import { z } from 'zod'

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
})

export default defineEventHandler(async (event) => {
  const body = await readValidatedBody(event, (i) => schema.parse(i))
  const data = await flaskFetch<{ access: string; refresh: string; user: User }>(
    '/api/auth/login',
    event,
    { method: 'POST', body },
  )
  setAccessCookie(event, data.access)
  setRefreshCookie(event, data.refresh)
  return { user: data.user }
})
```

### `flaskFetch` resilient pattern

`flaskFetch` reads `$fetch` and `useRuntimeConfig` via the resilient stub-first / module-fallback pattern (Phase 3 TD-009 fix, extended in Phase 4 with `nitropack/runtime` fallback) so unit tests can stub via `globalThis` without Nitro having to expose those names on the global. See `frontend/server/utils/flask-client.ts`.

### `auth-forward` middleware

```typescript
// frontend/server/middleware/auth-forward.ts
export default defineEventHandler((event) => {
  const access = getCookie(event, 'tdc_access')
  if (access) {
    event.context.flaskHeaders = { Authorization: `Bearer ${access}` }
  }
})
```

`flaskFetch` then merges `event.context.flaskHeaders` into every outbound call -- the user's identity propagates server-to-server.

---

## Forbidden patterns -- reject on sight

| Don't | Do | Why |
|---|---|---|
| `localStorage.setItem('jwt', ...)` | HttpOnly cookie via `server/api/auth/**` | XSS token theft |
| `axios.get(...)` | `useApiFetch` / `useFetch` / `$fetch` | Nuxt-native, SSR-aware |
| Pinia options API | Setup syntax | Project standard |
| `defineProps({ foo: { type: String, ... } })` | `defineProps<{ foo: string }>()` | Type-form props |
| `any` | Define or import a real type | TS strict |
| `gsap.from(...)` without `gsap.context()` | `gsap.context(() => gsap.from(...))` + `revert()` | ScrollTrigger leaks |
| Standalone Lenis RAF | `gsap.ticker.add(lenis.raf)` | Double-RAF drift |
| Hardcoded UI text | `t('key')` | i18n mandate |
| `<NuxtLink to="/locations">` | `<NuxtLink :to="localePath('/locations')">` | Locale-preserving links |
| `text-red-400` on errors | `text-error` (semantic token) | Palette-agnostic |
| TipTap / canvas without `<ClientOnly>` | `<ClientOnly>` with matching-shape `#fallback` | SSR crash |
| `console.log` committed | Remove; `logger.info` only on server routes | Noise + perf |
| `nitro.devProxy` catch-all on `/api` | `routeRules.proxy` for `/api/**` | BFF precedence: catch-all hijacks `/api/auth` |
| `useState('auth', ...)` (key collision risk) | Pinia store | App-wide state belongs in stores |

---

## Common Snippets

### Canonical SFC

```vue
<script setup lang="ts">
import type { Location } from '~/types/location'
import { Heart } from 'lucide-vue-next'

const props = defineProps<{ location: Location; variant?: 'compact' | 'full' }>()
const emit = defineEmits<{ select: [id: number]; 'update:favorite': [v: boolean] }>()

const localePath = useLocalePath()
const auth = useAuthStore()

const isFavorite = ref(false)
const href = computed(() => localePath(`/locations/${props.location.slug}`))

const toggle = () => {
  isFavorite.value = !isFavorite.value
  emit('update:favorite', isFavorite.value)
}
</script>

<template>
  <NuxtLink :to="href" class="block">
    <h3>{{ location.name }}</h3>
    <button v-if="auth.isAuthenticated" @click.prevent="toggle" :aria-pressed="isFavorite">
      <Heart :class="isFavorite ? 'fill-current' : ''" />
    </button>
  </NuxtLink>
</template>
```

### `<ClientOnly>` with matching-shape fallback

```vue
<ClientOnly>
  <TipTapEditor v-model="content" />
  <template #fallback>
    <div class="h-64 bg-surface/50 rounded-lg" aria-hidden="true" />
  </template>
</ClientOnly>
```

### GSAP composable with cleanup

```typescript
// app/composables/useScrollAnimation.ts
export function useScrollAnimation() {
  const ctx = ref<ReturnType<typeof import('gsap').gsap.context> | null>(null)

  const animateReveal = (selector: string) => {
    if (!import.meta.client) return
    const { $gsap } = useNuxtApp() as unknown as { $gsap: typeof import('gsap').gsap }
    ctx.value = $gsap.context(() => {
      $gsap.from(selector, {
        y: 80, opacity: 0, duration: 0.8, stagger: 0.1,
        scrollTrigger: { trigger: selector, start: 'top 80%' },
      })
    })
  }

  onBeforeUnmount(() => ctx.value?.revert())
  return { animateReveal }
}
```

### `definePageMeta` combinations

```typescript
// Public page -- no meta needed (default layout, SSR on)

// Auth-gated user area
definePageMeta({ layout: 'dashboard', middleware: ['auth'] })

// Admin-only
definePageMeta({ layout: 'admin', middleware: ['auth', 'admin'] })

// Staff (or admin)
definePageMeta({ layout: 'admin', middleware: ['auth', 'staff'] })

// Login / register (no auth middleware -- the page IS the entry point)
definePageMeta({ layout: 'auth' })
```

### Error handling

```typescript
// Fatal -- renders error.vue
throw createError({ statusCode: 404, statusMessage: 'Not found', fatal: true })

// useApiFetch / useFetch
const { data, error } = await useApiFetch<T>('/api/...')
if (error.value) { /* render inline error */ }

// Imperative
try {
  await $fetch('/api/...', { method: 'POST', body })
} catch (e) {
  const err = e as import('ofetch').FetchError
  // err.statusCode, err.data
}
```

---

## Closing checklist

Before declaring a frontend task done:

- [ ] TypeScript clean (no errors in `nuxi dev` or `npm run typecheck`)
- [ ] Unit tests pass (`npm test`)
- [ ] SSR renders expected content for public routes (`curl :9503/<route> | grep <expected>`)
- [ ] No hydration warnings in browser console
- [ ] No browser globals outside `onMounted` / `.client.ts`
- [ ] `useSeoMeta` present on every public page
- [ ] All user-visible strings via `t(...)`
- [ ] GSAP wrapped in `gsap.context()` + `revert()` cleanup on unmount
- [ ] File size within limits (`.vue` <= 500, `.ts` <= 800)
- [ ] Auth tokens never readable from JS (cookies only, HttpOnly)
- [ ] No `any`, no `console.log` left behind
- [ ] Accessibility: keyboard nav works, focus visible, alt/labels present

---

## Integration with other agents / skills

| Hand off to | When |
|---|---|
| `tdc-backend-expert` / `tdc-backend` skill | Flask routes, services, Celery jobs, prod runtime |
| `tdc-database-expert` / `tdc-database` skill | MySQL schema, migrations, queries |
| `tdc-api-expert` | REST shape design, Second Life API contract |
| `tdc-auth-expert` | OAuth providers, JWT issuance server-side, password reset |
| `tdc-integration-expert` | Google Calendar / Facebook / Patreon / SL webhooks |
| `tdc-testing-expert` / `tdc-testing` skill | Multi-subsystem strategy, shared fixtures |

---

## Closing principles (from CLAUDE.md)

- **Debug-first**: add logs, see actual state, then fix. Never guess.
- **Fix-Test-Verify**: one fix -> test -> only proceed if still broken.
- **No batch modifications**: every file edit is individual and visible.
- **Zero superficiality**: read relevant code before writing.
- **Direct communication**: no cheerleading. If a pattern is wrong, say so with the reason.

The motto is **"You Can See The Music"** -- carry that intent through every interaction, transition, and pause.
