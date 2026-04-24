# TDC Nuxt 4 Frontend Playbook

Deep reference for the `tdc-frontend-expert` agent and human engineers.
Complements `.claude/agents/tdc-frontend-expert.md` (always-loaded rules)
and `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md`
(architectural decisions). Consult this file on-demand when implementing
a specific pattern.

---

## Table of Contents

| § | Section | Lines |
|---|---|---|
| 1 | Nuxt 4 deep-dive | ~40-110 |
| 2 | Vue 3 + TypeScript patterns | ~115-205 |
| 3 | File-based routing | ~210-280 |
| 4 | Layouts | ~285-320 |
| 5 | Data fetching deep-dive | ~325-460 |
| 6 | Rendering strategies (routeRules) | ~465-555 |
| 7 | SSR pitfalls & fixes | ~560-660 |
| 8 | GSAP + ScrollTrigger | ~665-745 |
| 9 | Lenis smooth scroll | ~750-800 |
| 10 | Pinia stores | ~805-880 |
| 11 | Server routes (BFF) | ~885-1020 |
| 12 | h3 utilities reference | ~1025-1075 |
| 13 | i18n deep-dive | ~1080-1170 |
| 14 | Tailwind + location theming | ~1175-1270 |
| 15 | SEO patterns | ~1275-1355 |
| 16 | Images (`@nuxt/image`) | ~1360-1400 |
| 17 | Forms (vee-validate + zod) | ~1405-1470 |
| 18 | TipTap editor | ~1475-1530 |
| 19 | Testing (vitest + Playwright) | ~1535-1650 |
| 20 | Accessibility (WCAG 2.1 AA) | ~1655-1695 |
| 21 | Performance (Core Web Vitals) | ~1700-1750 |
| 22 | Common task recipes | ~1755-end |
| 23 | Pattern library (Phase 3+) | end-of-file |

Lines are approximate (they drift as sections are added or rewritten).
Use `Read` with `offset`/`limit` and confirm against
`grep -nE '^## [0-9]+' docs/frontend/nuxt-playbook.md` if you need to
jump straight to a section.

---

## 1. Nuxt 4 deep-dive

### 1.1 The `app/` layer

Nuxt 4 introduces the `app/` directory to separate application code from
project tooling. Compared to Nuxt 3 (flat root), this gives a cleaner
separation. Your code lives under `app/`; build config and tooling
(`nuxt.config.ts`, `tsconfig.json`, `vitest.config.ts`, `package.json`)
stay at project root. **No `tailwind.config.ts`** — TDC uses Tailwind v4
CSS-first config, with tokens declared in `app/assets/css/main.css`
via `@theme` (see §14).

### 1.2 Auto-imports

Nuxt auto-imports:
- Vue reactivity: `ref`, `computed`, `watch`, `watchEffect`, `reactive`, `readonly`, `shallowRef`, `toRefs`, `toRef`
- Nuxt composables: `useFetch`, `useLazyFetch`, `useAsyncData`, `useLazyAsyncData`, `$fetch`, `useRoute`, `useRouter`, `useHead`, `useSeoMeta`, `useSchemaOrg`, `navigateTo`, `useRuntimeConfig`, `useState`, `useCookie`, `useRequestEvent`, `useRequestHeaders`
- Nuxt lifecycle: `definePageMeta`, `defineNuxtPlugin`, `defineNuxtComponent`, `defineEventHandler`, `defineLazyEventHandler`
- Components under `app/components/` (nested paths become prefixes: `app/components/common/AppHeader.vue` → `<CommonAppHeader />` or auto-resolved as `<AppHeader />` depending on config)
- Composables under `app/composables/` (file name = function name)
- Utils under `app/utils/`

Explicit imports needed for:
- Third-party packages (`gsap`, `zod`, `vee-validate`, `lenis`, `lucide-vue-next` with named destructuring)
- Types: `import type { User } from '~/types/user'`, `import type { H3Event } from 'h3'`

### 1.3 `nuxt.config.ts` canonical structure

```typescript
export default defineNuxtConfig({
  compatibilityDate: '2026-04-01',           // Locks runtime behavior to a specific date
  future: { compatibilityVersion: 4 },       // Opt into Nuxt 4 defaults (app/ layer)

  modules: [
    '@nuxtjs/i18n',
    '@pinia/nuxt',
    '@vueuse/nuxt',
    '@nuxt/image',
    '@nuxtjs/seo',
    '@nuxtjs/robots',
    '@nuxtjs/sitemap',
    // Tailwind v4 is wired via the Vite plugin, NOT a Nuxt module.
    // See `vite.plugins` below. `@nuxtjs/tailwindcss` targets Tailwind v3
    // and conflicts with v4 hoisted by @nuxt/ui / nuxt-og-image.
  ],

  devtools: { enabled: true },

  // Tailwind CSS v4 (CSS-first config). Tokens live in main.css.
  vite: {
    plugins: [tailwindcss()],         // import tailwindcss from '@tailwindcss/vite'
  },

  css: ['~/assets/css/main.css'],

  typescript: {
    strict: true,
    typeCheck: false,                         // Off in dev for speed; enable in CI
  },

  runtimeConfig: {
    flaskUrl: '',                             // NUXT_FLASK_URL (server only)
    cookieSecret: '',                         // NUXT_COOKIE_SECRET
    public: {
      apiBase: '/api',                        // NUXT_PUBLIC_API_BASE (client-exposed)
      siteUrl: '',                            // NUXT_PUBLIC_SITE_URL
    },
  },

  nitro: {
    devProxy: {
      '/api': { target: process.env.NUXT_FLASK_URL, changeOrigin: true },
    },
    prerender: {
      crawlLinks: true,
      routes: ['/sitemap.xml'],
      failOnError: false,
    },
  },

  routeRules: { /* see §6 */ },

  i18n: { /* see §13 */ },

  devServer: { host: '0.0.0.0', port: 9503 },
})
```

### 1.4 `runtimeConfig` rules

- **Top-level keys** = server only. Safe for secrets. Accessed via `useRuntimeConfig()` **inside event handlers or `setup()`**, never at module scope.
- **`public.*`** = exposed to client bundle. **Never put secrets here.**
- Env vars override config: `NUXT_FLASK_URL=http://localhost:9502` overrides `runtimeConfig.flaskUrl`.

---

## 2. Vue 3 + TypeScript patterns

### 2.1 Canonical component structure

```vue
<script setup lang="ts">
// 1. External imports
import type { Location } from '~/types/location'
import { Heart } from 'lucide-vue-next'

// 2. Props (typed)
const props = defineProps<{
  location: Location
  variant?: 'compact' | 'full'
}>()

// 3. Emits (typed)
const emit = defineEmits<{
  select: [id: number]
  'update:favorite': [value: boolean]
}>()

// 4. Stores / composables
const localePath = useLocalePath()
const { animateReveal } = useScrollAnimation()

// 5. Local state
const isFavorite = ref(false)

// 6. Computed
const href = computed(() => localePath(`/locations/${props.location.slug}`))

// 7. Lifecycle
onMounted(() => {
  animateReveal(`#location-${props.location.id}`)
})

// 8. Methods
const toggleFavorite = () => {
  isFavorite.value = !isFavorite.value
  emit('update:favorite', isFavorite.value)
}
</script>

<template>
  <NuxtLink :id="`location-${location.id}`" :to="href" class="block group">
    <h3 class="text-2xl font-display">{{ location.name }}</h3>
    <button
      type="button"
      :aria-pressed="isFavorite"
      class="focus-visible:outline-2"
      @click.prevent="toggleFavorite"
    >
      <Heart :class="isFavorite ? 'fill-accent' : ''" />
    </button>
  </NuxtLink>
</template>
```

### 2.2 Props with defaults

```typescript
const props = withDefaults(defineProps<{
  variant?: 'compact' | 'full'
  loading?: boolean
}>(), {
  variant: 'full',
  loading: false,
})
```

### 2.3 Typed template refs

```typescript
const headerRef = ref<HTMLElement | null>(null)
const modalRef = ref<InstanceType<typeof MyModal> | null>(null)
```

Template: `<div ref="headerRef">` — same name, Nuxt resolves.

### 2.4 Discriminated unions for state

```typescript
type FetchState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error }

const state = ref<FetchState<Location[]>>({ status: 'idle' })

// Template narrows safely:
// <div v-if="state.status === 'success'">{{ state.data.length }} locations</div>
```

### 2.5 `satisfies` for config objects

```typescript
const config = {
  locations: ['dreamerscave', 'dreamvision'] as const,
  // ...
} satisfies { locations: readonly string[] }
```

Gives both inference (exact types) and type checking (conformance).

---

## 3. File-based routing

### 3.1 File-to-route mapping

| File | Route |
|---|---|
| `app/pages/index.vue` | `/` |
| `app/pages/locations/index.vue` | `/locations` |
| `app/pages/locations/[slug].vue` | `/locations/:slug` |
| `app/pages/events/[...id].vue` | `/events/*` (catch-all) |
| `app/pages/auth/callback/[provider].vue` | `/auth/callback/:provider` |
| `app/pages/(marketing)/about.vue` | `/about` (route group — no URL segment from `(marketing)`) |

### 3.2 Dynamic params typed

```vue
<script setup lang="ts">
const route = useRoute()
const slug = computed(() => route.params.slug as string)

const { data: location, error } = await useFetch<Location>(
  `/api/locations/${slug.value}`,
  { key: `location-${slug.value}` },
)

if (!location.value) {
  throw createError({
    statusCode: 404,
    statusMessage: 'Location not found',
    fatal: true,
  })
}
</script>
```

### 3.3 `definePageMeta`

```typescript
definePageMeta({
  layout: 'dashboard',
  middleware: ['auth'],                    // or array for multiple
  alias: ['/profilo'],                     // extra paths that resolve here
  key: (route) => route.path,              // custom <NuxtPage :key> strategy
  pageTransition: { name: 'fade' },
})
```

Middlewares run in order. `middleware: ['auth', 'staff']` requires both.

### 3.4 `<NuxtLink>` with i18n

```vue
<NuxtLink :to="localePath('/locations')">{{ $t('nav.locations') }}</NuxtLink>
```

`localePath()` rewrites to `/it/locations` when locale is `it`, etc. Never hardcode prefixes.

### 3.5 Programmatic navigation

```typescript
await navigateTo('/dashboard')                            // simple
await navigateTo(localePath('/dashboard'))                // locale-aware
await navigateTo({ path: '/locations', query: { mood: 'cosmic' } })
await navigateTo('/auth/login', { replace: true })        // replace history
throw createError({ statusCode: 403 })                    // abort + error page
```

---

## 4. Layouts

```
app/layouts/
├── default.vue       Public layout (header + footer)
├── auth.vue          Minimal centered (login/register)
├── dashboard.vue     User-area sidebar
└── admin.vue         Admin sidebar with nav
```

Apply via `definePageMeta({ layout: 'dashboard' })`. Default is `default.vue` automatically.

Layout skeleton:

```vue
<!-- app/layouts/dashboard.vue -->
<template>
  <div class="min-h-screen flex bg-dark text-white">
    <aside class="w-64 border-r border-white/10">
      <DashboardSidebar />
    </aside>
    <main class="flex-1 p-8">
      <slot />
    </main>
  </div>
</template>
```

Switch layout dynamically:

```typescript
const layout = ref<'default' | 'minimal'>('default')
setPageLayout(layout.value)
```

---

## 5. Data fetching deep-dive

### 5.1 Decision tree

- **Need data for the page body, SSR-rendered?** → `useFetch`
- **Heavy async that isn't a fetch (e.g., parse markdown)?** → `useAsyncData`
- **Imperative call from an event handler?** → `$fetch`
- **Auth'd imperative call with 401 auto-refresh?** → `useApi()` (TDC composable)
- **Fetch but don't block navigation?** → `useLazyFetch` or `useLazyAsyncData`

### 5.2 `useFetch` — the default

```typescript
const { data: locations, error, pending, refresh, execute } = await useFetch<Location[]>(
  '/api/locations',
  {
    key: 'locations-list',                  // Explicit dedup key
    default: () => [],                       // Never null → tighter types
    transform: (raw) => raw.filter(l => l.is_published),
    watch: [currentFilter],                  // Re-fetch when a ref changes
    server: true,                            // Default true — runs during SSR
    lazy: false,                             // Blocks navigation until done
    immediate: true,                         // Fetch on setup (default)
    query: computed(() => ({                 // Reactive query params
      page: page.value,
      perPage: 20,
    })),
    headers: {
      'Accept-Language': locale.value,       // For DB-backed translations
    },
  },
)
```

### 5.3 Keys & cache

Two components calling `useFetch('/api/locations')` with the same `key` share the SSR payload. Without an explicit `key`, Nuxt generates one from the URL + options — reliable but easier to reason about with explicit keys.

For locale-sensitive fetches include locale in the key:
```typescript
key: `location-${slug}-${locale.value}`
```

### 5.4 `transform` — reshape at fetch time

```typescript
const { data: events } = await useFetch<{ events: Event[] }>('/api/events', {
  transform: ({ events }) => events.sort((a, b) => a.starts_at.localeCompare(b.starts_at)),
})
// data.value is Event[], already sorted
```

### 5.5 `default` — never null data

```typescript
const { data } = await useFetch<Location[]>('/api/locations', {
  default: () => [],
})
// data.value: Location[] (not Location[] | null)
// Template: <div v-for="l in data" :key="l.id"> — no v-if needed
```

### 5.6 `$fetch` — imperative

```typescript
const submit = async () => {
  try {
    const result = await $fetch<{ user: User }>('/api/auth/login', {
      method: 'POST',
      body: { email, password },
      credentials: 'include',
    })
    authStore.setUser(result.user)
  } catch (e) {
    // e is FetchError with .status, .data, .response
  }
}
```

### 5.7 The `useApi()` composable (TDC)

```typescript
// app/composables/useApi.ts
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
// recursively references `useApi()` in its retry path (spec §8.4 --
// retry must re-enter the wrapper so `credentials: 'include'` and any
// future interceptor logic are preserved). Without the annotation
// TS7023 fires because the inferred type depends on itself.
// `ReturnType<typeof $fetch.create>` names the Nitro wrapper type
// without importing internal aliases.
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

// Usage:
const api = useApi()
const favorites = await api<Favorite[]>('/api/user/favorites')
```

**Design notes (Phase 3).**

1. **Typed retry marker, zero `as any`.** Earlier drafts spelled the flag
   as `(options as any)._retry`. Reviewer-Phase-2 feedback required
   eliminating the `any` cast. The export of `RetryableFetchOptions`
   lets both the implementation and the test harness
   (`tests/unit/useApi.test.ts`) build typed contexts.
2. **Derive from `Parameters<typeof $fetch>[1]`, not ofetch's
   `FetchOptions`.** Nitro narrows `method` to a literal union
   (`'GET' | 'POST' | ...`) while ofetch's `FetchOptions` widens it to
   `string`. Deriving from `$fetch`'s own parameter keeps strict mode
   happy.
3. **Recursive retry re-enters `useApi()`, not raw `$fetch`.** The
   spec §8.4 contract requires `useApi()(request, opts)` so the
   retry inherits the wrapper's `credentials: 'include'` and any
   future interceptor logic. The `_retry` flag set to `true` before
   the recursive call prevents infinite loops.
4. **Explicit `ReturnType<typeof $fetch.create>` return type.** Without
   it, TS7023 fires on the recursive reference. The explicit
   annotation names the Nitro wrapper type without leaking internal
   aliases.

### 5.8 SSR pass-through pattern

During SSR, Nuxt's server calls Flask at `http://localhost:9500/api/...` via `useRuntimeConfig().flaskUrl` (server-to-server loopback — bypasses nginx).

In the browser, the same path goes to `/api/...` relative, resolved by nginx (prod) or Nitro devProxy (dev).

On hydration, `useFetch` does NOT re-fetch — it reuses the payload from SSR. Force client-side re-fetch with `{ server: false, lazy: true }`.

### 5.9 Server-only data

For sensitive calls that should never run on client:

```typescript
const { data } = await useFetch('/api/admin/secrets', { server: true, client: false })
```

(Or better: put the call in a `server/api/**` route and fetch that route.)

### 5.10 Error handling

```typescript
const { data, error } = await useFetch<Location>('/api/locations/xyz')

if (error.value) {
  throw createError({
    statusCode: error.value.statusCode || 500,
    statusMessage: error.value.statusMessage || 'Something broke',
    fatal: true,         // Full error page; omit for inline error UI
  })
}
```

---

## 6. Rendering strategies (`routeRules`)

### 6.1 Strategies

| Rule | Effect | Use for |
|---|---|---|
| `{ prerender: true }` | **SSG** — generated at build | Stable public content |
| `{ swr: N }` | **ISR** — serve stale, revalidate in background after N seconds | Frequently-updated public content |
| `{ isr: N }` | Alias for `swr` in most presets | Same as SWR |
| `{ ssr: true }` (default) | Server-render each request | Dynamic per user/session |
| `{ ssr: true, swr: false }` | Server-render, no cache | Auth/search pages |
| `{ ssr: false }` | Client-only (SPA) | Auth-gated apps, no SEO value |
| `{ cache: { maxAge: N } }` | Server route cache | `server/api/**` endpoints |
| `{ headers: { ... } }` | Custom response headers | Security, cache control |
| `{ redirect: '/new' }` | 302 redirect | Aliased URLs |
| `{ cors: true }` | CORS headers | Public APIs |

### 6.2 TDC route map (canonical)

```typescript
routeRules: {
  '/':                { prerender: true },
  '/locations':       { prerender: true },
  '/locations/**':    { prerender: true },
  '/artists':         { prerender: true },
  '/artists/**':      { prerender: true },
  '/about':           { prerender: true },
  '/contact':         { prerender: true },

  '/events':          { swr: 300 },              // 5 min
  '/events/**':       { swr: 300 },
  '/blog':            { swr: 3600 },             // 1 h
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
```

### 6.3 On-demand revalidation

When an admin edits a location / event / blog post, instantly refresh the cached page:

```typescript
// server/api/revalidate.post.ts
import { z } from 'zod'

export default defineEventHandler(async (event) => {
  const identity = await flaskFetch<{ role: string }>('/api/auth/me', event).catch(() => null)
  if (identity?.role !== 'admin') {
    throw createError({ statusCode: 403, statusMessage: 'Admin required' })
  }

  const { path } = await readValidatedBody(event, (i) =>
    z.object({ path: z.string().startsWith('/') }).parse(i))

  const storage = useStorage('cache:nitro')
  await storage.removeItem(`routes:${path}.json`)

  return { revalidated: path }
})
```

Client trigger after admin save:

```typescript
await $fetch('/api/revalidate', {
  method: 'POST',
  body: { path: `/locations/${slug}` },
  credentials: 'include',
})
```

### 6.4 Prerender scope

```typescript
nitro: {
  prerender: {
    crawlLinks: true,                // Follow <NuxtLink> to find more routes
    routes: ['/sitemap.xml', '/robots.txt'],
    failOnError: false,              // Don't block build on a 404
    ignore: ['/preview', '/admin'],  // Skip these paths during prerender
  },
}
```

For dynamic routes (e.g., `/locations/:slug`), the build queries Flask at build time to get the slug list. Configure via a custom Nitro hook or rely on `crawlLinks: true` if the slugs are linked from a prerendered index page.

---

## 7. SSR pitfalls & fixes

### 7.1 Hydration mismatch — diagnosis

When browser DevTools shows a Vue warning like "Hydration node mismatch", the server-rendered HTML differed from what the client generated on mount. The warning names the component.

Common causes and fixes:

| Cause | Fix |
|---|---|
| `{{ new Date().toLocaleString() }}` | Render ISO on server, format in `onMounted` |
| `{{ Math.random() }}` / `{{ crypto.randomUUID() }}` | `<ClientOnly>` with fallback |
| `{{ navigator.language }}` | Use `useRequestHeaders(['accept-language'])` on server |
| Feature detection (`'ontouchstart' in window`) | Guard with `import.meta.client` in `onMounted` |
| Third-party library that manipulates DOM on import | `<ClientOnly>` wrap, or make it a `.client.ts` plugin |

### 7.2 `<ClientOnly>` pattern

```vue
<ClientOnly>
  <InteractiveMap :location="location" />
  <template #fallback>
    <div
      class="w-full aspect-video bg-surface/50 rounded-lg"
      aria-hidden="true"
    />
  </template>
</ClientOnly>
```

Fallback should have **matching shape** (same dimensions / layout) so the page doesn't reflow on hydration.

### 7.3 `.client.ts` suffix

Files with `.client.ts` are excluded from the SSR bundle entirely:
- `app/plugins/gsap.client.ts` ✓ (GSAP only runs client-side)
- `app/plugins/lenis.client.ts` ✓
- Counterpart `.server.ts` suffix exists too (rarely needed for frontend)

### 7.4 `import.meta.client` / `import.meta.server`

```typescript
if (import.meta.client) {
  // browser-only code
}

if (import.meta.server) {
  // Nuxt server-only code (during SSR)
}
```

Both are stripped by the bundler — the server doesn't ship `import.meta.client` branches and vice versa.

### 7.5 `useCookie` — SSR-safe

```typescript
// Reactive cookie, works server + client
const theme = useCookie<'dark' | 'light'>('theme', { default: () => 'dark' })
theme.value = 'light'                              // Sets the cookie + updates value
```

Never use `document.cookie` directly in `setup()`.

### 7.6 `useState` — SSR-safe shared state

```typescript
// app/composables/useCart.ts
export const useCart = () => useState<CartItem[]>('cart', () => [])

// In any component:
const cart = useCart()
cart.value.push(item)
```

`useState` persists across SSR → hydration. Pinia is better for complex state; `useState` is perfect for simple shared pieces.

### 7.7 Debug SSR content quickly

```bash
curl -s http://localhost:9503/locations/dreamerscave | grep -E '<h1>|<h2>'
```

If the title appears, SSR works. If not, either the page is `ssr: false` (check routeRules) or the data fetch failed on the server.

---

## 8. GSAP + ScrollTrigger

### 8.1 Plugin registration (client-only)

```typescript
// app/plugins/gsap.client.ts
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

export default defineNuxtPlugin(() => {
  gsap.registerPlugin(ScrollTrigger)
  return { provide: { gsap, ScrollTrigger } }
})
```

### 8.2 Why `gsap.context()` matters

Without context:
```typescript
onMounted(() => {
  gsap.from('.card', { y: 100, scrollTrigger: { trigger: '.card' } })
})
// ❌ ScrollTrigger instance survives page navigation
// ❌ After 3 navigations, stale triggers fire on phantom elements
// ❌ Scroll behavior breaks, `.card` from a previous page still tracked
```

With context (correct):

```typescript
// app/composables/useScrollAnimation.ts
export function useScrollAnimation() {
  const ctx = ref<ReturnType<typeof import('gsap').gsap.context> | null>(null)

  const animateReveal = (selector: string, options: Record<string, unknown> = {}) => {
    if (!import.meta.client) return
    // Respect user accessibility preference: skip reveal entirely when
    // the system signals reduced motion. Elements render at their
    // natural CSS state (no translate, no fade-in). See the 3-layer
    // reduced-motion discipline below §9 Lenis.
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const { $gsap } = useNuxtApp() as unknown as { $gsap: typeof import('gsap').gsap }
    ctx.value = $gsap.context(() => {
      $gsap.from(selector, {
        y: 100, opacity: 0, duration: 1, stagger: 0.2,
        scrollTrigger: { trigger: selector, start: 'top 80%' },
        ...options,
      })
    })
  }

  onBeforeUnmount(() => {
    if (!import.meta.client) return
    ctx.value?.revert()                              // Kills every ScrollTrigger + reverts styles
    const { $ScrollTrigger } = useNuxtApp() as unknown as {
      $ScrollTrigger: typeof import('gsap/ScrollTrigger').ScrollTrigger
    }
    $ScrollTrigger?.refresh()                         // Recompute triggers for remaining elements
  })

  return { animateReveal }
}
```

### 8.3 Patterns for common animations

**Hero pin + fade**:
```typescript
$gsap.timeline({
  scrollTrigger: {
    trigger: '.hero',
    start: 'top top',
    end: 'bottom top',
    scrub: true,
  },
})
  .to('.hero-video', { scale: 1.2, opacity: 0 })
  .to('.hero-text', { y: -100, opacity: 0 }, 0)
```

**Stagger reveal**:
```typescript
$gsap.from('.grid > article', {
  y: 80, opacity: 0, duration: 0.8,
  stagger: { amount: 1.2, from: 'start' },
  scrollTrigger: { trigger: '.grid', start: 'top 75%' },
})
```

**Parallax**:
```typescript
$gsap.to('.parallax-bg', {
  y: () => window.innerHeight * 0.5,
  ease: 'none',
  scrollTrigger: { trigger: '.parallax', start: 'top bottom', end: 'bottom top', scrub: true },
})
```

### 8.4 Performance

- Prefer `transform` and `opacity` (GPU-accelerated). Avoid animating `width`, `top`, `left`.
- Use `will-change: transform` sparingly (only during active animation).
- `ScrollTrigger.config({ ignoreMobileResize: true })` to avoid iOS safe-area resize thrash.

---

## 9. Lenis smooth scroll

### 9.1 Plugin (synced with GSAP ticker)

```typescript
// app/plugins/lenis.client.ts
import Lenis from 'lenis'

export default defineNuxtPlugin((nuxtApp) => {
  // Accessibility: respect `prefers-reduced-motion`. When the user
  // has asked the system to reduce animation, do NOT instantiate
  // Lenis at all. Smooth-scroll on wheel/touch would still interpolate
  // scroll position regardless of per-call guards in useSmoothScroll.
  // Consumers rely on optional-chain `$lenis?.scrollTo(...)` to no-op
  // when the provided value is null.
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return { provide: { lenis: null as Lenis | null } }
  }

  const lenis = new Lenis({ duration: 1.2, smoothWheel: true })
  const { $gsap } = nuxtApp as unknown as { $gsap: typeof import('gsap').gsap }

  // ✓ Sync — single RAF driven by GSAP ticker
  $gsap.ticker.add((time: number) => lenis.raf(time * 1000))
  $gsap.ticker.lagSmoothing(0)

  // Stop on admin/dashboard so data tables get native scroll
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

**Three-layer reduced-motion discipline (Phase 3 pattern).**

The `prefers-reduced-motion` media query is honoured at three layers so
no single miss re-enables motion:

1. **Lenis plugin** — when the query matches, the plugin never
   constructs Lenis; `$lenis` is provided as `null`. Wheel / touch
   smooth-scroll is therefore natively disabled.
2. **`useScrollAnimation`** — `animateReveal()` checks the same query
   and early-returns. Elements render at their natural CSS state.
3. **`useSmoothScroll`** — `scrollTo()` checks the query and early-
   returns. Programmatic scroll becomes a no-op; callers fall back
   to whatever native behaviour they already had (`location.hash`,
   `scrollIntoView`).

Layer 1 is the guard; layers 2 and 3 are belt-and-braces. `$lenis` being
`null` alone would already disable layer 3, but an explicit guard makes
the intent visible at the consumer site.

### 9.2 Programmatic scrollTo

```typescript
// app/composables/useSmoothScroll.ts
export function useSmoothScroll() {
  const scrollTo = (target: string | HTMLElement, options?: { offset?: number }) => {
    if (!import.meta.client) return
    // Respect user accessibility preference: skip programmatic smooth
    // scroll when reduced-motion is requested. Consumer fallback is
    // browser-native scrollIntoView / location hash.
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const { $lenis } = useNuxtApp() as unknown as { $lenis: import('lenis').default | null }
    $lenis?.scrollTo(target, options)
  }
  return { scrollTo }
}

// Usage: scrollTo('#section-3', { offset: -80 })
```

---

## 10. Pinia stores

### 10.1 Setup syntax (project standard)

```typescript
// app/stores/auth.ts
import { defineStore } from 'pinia'
import type { User } from '~/types/user'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => user.value !== null)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isStaff = computed(() =>
    user.value?.role === 'staff' || user.value?.role === 'admin',
  )

  const setUser = (u: User | null) => { user.value = u }
  const clear = () => { user.value = null }

  return { user, isAuthenticated, isAdmin, isStaff, setUser, clear }
})
```

### 10.2 Consumption

```typescript
import { storeToRefs } from 'pinia'

const authStore = useAuthStore()
const { user, isAdmin } = storeToRefs(authStore)      // reactive refs
authStore.clear()                                     // actions: NOT refs
```

**`storeToRefs` is mandatory when destructuring reactive state.** Plain destructuring loses reactivity.

### 10.3 Cross-store access

```typescript
// app/stores/ui.ts
export const useUiStore = defineStore('ui', () => {
  const authStore = useAuthStore()                    // reference another store

  const showProFeatures = computed(() => authStore.isAdmin)

  return { showProFeatures }
})
```

### 10.4 SSR hydration

Pinia is SSR-compatible out of the box with `@pinia/nuxt`. State set during SSR is serialized into HTML and rehydrated on the client. No extra work needed.

### 10.5 TDC stores

- `auth.ts` — user, session, roles
- `locale.ts` — current language
- `ui.ts` — modal state, mobile menu, notifications
- Feature stores (future): `events.ts`, `blog.ts`, etc.

Keep each store focused. If a store exceeds ~300 lines, split by concern.

### 10.6 SSR caveats

Store **state** is SSR-safe. Store **actions** that call browser-only
APIs are not. Concrete Phase 3 example:

```typescript
// app/stores/ui.ts
export const useUiStore = defineStore('ui', () => {
  const notifications = ref<Notification[]>([])

  /**
   * Push a notification onto the stack.
   *
   * @warning Do NOT call during SSR setup() or template interpolation.
   * Uses `crypto.randomUUID()` which produces different IDs on server
   * vs client, causing hydration mismatch. Safe for user-triggered
   * actions (button clicks, API error handlers, form submissions
   * post-mount).
   */
  const pushNotification = (n: Omit<Notification, 'id'>) => {
    notifications.value.push({ ...n, id: crypto.randomUUID() })
  }
  // …
})
```

Rule of thumb: any action that calls `crypto`, `Date.now()`,
`Math.random()`, `window.*`, `localStorage`, `navigator.*`, or
`IntersectionObserver` must be invoked from an event handler
(`onMounted` or later), never from `setup()` top-level.

---

## 11. Server routes (BFF)

### 11.1 Architecture recap

TDC uses a **hybrid BFF**: only auth routes (`server/api/auth/**`) and
`server/api/revalidate` are Nuxt server routes. All other `/api/**`
proxy directly to Flask via nginx (prod) or Nitro devProxy (dev).

### 11.2 Event handler shape

```typescript
// server/api/auth/login.post.ts
import { z } from 'zod'

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
})

interface FlaskLoginResponse {
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
  const body = await readValidatedBody(event, (i) => loginSchema.parse(i))

  const response = await flaskFetch<FlaskLoginResponse>('/api/auth/login', event, {
    method: 'POST',
    body,
  })

  setAccessCookie(event, response.access)
  setRefreshCookie(event, response.refresh)

  return { user: response.user }
})
```

File naming convention:
- `server/api/users.get.ts` → `GET /api/users`
- `server/api/users.post.ts` → `POST /api/users`
- `server/api/users/[id].put.ts` → `PUT /api/users/:id`
- `server/api/users/[id].delete.ts` → `DELETE /api/users/:id`

### 11.3 Auth-forward server middleware

> **Implementation note (Phase 2 discovery).** Nitro's prod bundle does
> NOT universally expose h3 auto-imports on `globalThis` —
> `getCookie` / `defineEventHandler` live as module-level bindings in
> `.nuxt/dev/index.mjs`. A bare-identifier usage at module scope works
> in dev (Nitro patches globalThis at serve time) but throws
> `ReferenceError` inside vitest (ESM hoists `import` above any test-file
> globalThis stubs) and is fragile across Nuxt/Nitro upgrades. The
> canonical TDC pattern is **resolve-at-call-time: prefer a globalThis
> stub if present (tests), fall back to a direct `h3` import**.

The actual TDC implementation:

```typescript
// server/middleware/auth-forward.ts
import type { H3Event, EventHandler } from 'h3'
import {
  defineEventHandler as h3DefineEventHandler,
  getCookie as h3GetCookie,
} from 'h3'
import { TDC_ACCESS_COOKIE } from '../utils/cookies'

type DefineEventHandlerFn = <T extends EventHandler>(h: T) => T
type GetCookieFn = (event: H3Event, name: string) => string | undefined

const resolveDefineEventHandler = (): DefineEventHandlerFn => {
  const stubbed = (globalThis as unknown as { defineEventHandler?: DefineEventHandlerFn })
    .defineEventHandler
  return stubbed ?? (h3DefineEventHandler as DefineEventHandlerFn)
}
const resolveGetCookie = (): GetCookieFn => {
  const stubbed = (globalThis as unknown as { getCookie?: GetCookieFn }).getCookie
  return stubbed ?? (h3GetCookie as GetCookieFn)
}

const handler: EventHandler = ((event: H3Event) => {
  const access = resolveGetCookie()(event, TDC_ACCESS_COOKIE)
  if (access) {
    event.context.flaskHeaders = { Authorization: `Bearer ${access}` }
  }
}) as EventHandler

// Lazy-wrap: defer `defineEventHandler` lookup until first invocation.
let _wrapped: EventHandler | null = null
const wrapped: EventHandler = ((event: H3Event) => {
  if (!_wrapped) _wrapped = resolveDefineEventHandler()(handler)
  return _wrapped(event)
}) as EventHandler

export default wrapped
```

Runs on **every** request (page, API, static). Populates
`event.context.flaskHeaders` so downstream server-route handlers can
forward auth when calling Flask via `flaskFetch`.

**Contract (do NOT drift):** cookie name exactly `tdc_access`; header
key exactly `Authorization` (capital A); header value exactly
`Bearer <jwt>` (capital B, single space). Flask's `@jwt_required`
extractor and our unit tests depend on this casing.

### 11.4 `flaskFetch` utility

```typescript
// server/utils/flask-client.ts
import type { H3Event } from 'h3'

type FetchFn = typeof $fetch
type RuntimeConfigFn = () => { flaskUrl: string } & Record<string, unknown>

const getFetch = (): FetchFn =>
  (globalThis as unknown as { $fetch: FetchFn }).$fetch

const getRuntimeConfig = (): ReturnType<RuntimeConfigFn> =>
  (globalThis as unknown as { useRuntimeConfig: RuntimeConfigFn }).useRuntimeConfig()

export const flaskFetch = <T = unknown>(
  url: string,
  event: H3Event,
  options: Parameters<typeof $fetch<T>>[1] = {},
): Promise<T> => {
  const { flaskUrl } = getRuntimeConfig()
  const flaskHeaders = (event.context.flaskHeaders ?? {}) as Record<string, string>
  return getFetch()<T>(url, {
    baseURL: flaskUrl,
    ...options,
    headers: { ...flaskHeaders, ...(options.headers ?? {}) },
  })
}
```

> **⚠️ Known risk — TD-009.** `flaskFetch` currently reads `$fetch` and
> `useRuntimeConfig` **only** from `globalThis`, without the h3-import
> fallback used in `auth-forward.ts`. Unit tests pass because they
> install globalThis stubs. Whether Nitro's prod bundle actually keeps
> `$fetch` / `useRuntimeConfig` on globalThis across all code paths is
> **unverified** — Phase 2 Task 2.7 proved `getCookie` is NOT on
> globalThis in prod, so by analogy these may also be module bindings.
> When Phase 4 wires the first real BFF route that calls `flaskFetch`,
> verify in prod and retrofit the resilient pattern if needed. See
> `docs/TECH_DEBT.md` TD-009.

### 11.5 Cookie helpers

```typescript
// server/utils/cookies.ts
import type { H3Event } from 'h3'
import {
  setCookie as h3SetCookie,
  deleteCookie as h3DeleteCookie,
  getCookie as h3GetCookie,
} from 'h3'

export const TDC_ACCESS_COOKIE = 'tdc_access'
export const TDC_REFRESH_COOKIE = 'tdc_refresh'
export const TDC_ACCESS_TTL_SECONDS = 900       // 15 min
export const TDC_REFRESH_TTL_SECONDS = 604800   // 7 days
export const TDC_REFRESH_COOKIE_PATH = '/api/auth'

// (globalThis-first / h3-fallback resolvers elided — same pattern as §11.3)

export const setAccessCookie = (event: H3Event, token: string): void => {
  resolveSetCookie()(event, TDC_ACCESS_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: TDC_ACCESS_TTL_SECONDS,
  })
}

export const setRefreshCookie = (event: H3Event, token: string): void => {
  resolveSetCookie()(event, TDC_REFRESH_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    path: TDC_REFRESH_COOKIE_PATH,
    maxAge: TDC_REFRESH_TTL_SECONDS,
  })
}

export const clearAuthCookies = (event: H3Event): void => {
  const del = resolveDeleteCookie()
  del(event, TDC_ACCESS_COOKIE, { path: '/' })
  del(event, TDC_REFRESH_COOKIE, { path: TDC_REFRESH_COOKIE_PATH })
  // ↑ the explicit `path` per cookie is REQUIRED — browsers match the
  //   deletion path to the Set-Cookie path exactly, and a missing path
  //   silently leaves the cookie alive. Do NOT "simplify" this.
}

export const getRefreshToken = (event: H3Event): string | undefined =>
  resolveGetCookie()(event, TDC_REFRESH_COOKIE)
```

Constants live at module scope so server routes, auth composables, and
tests all agree on names, lifetimes, and path scope. Spec §8.2 is the
source of truth; any change here MUST be mirrored in the spec and in
Flask's token-issuance.

### 11.6 Logout handler

```typescript
// server/api/auth/logout.post.ts
export default defineEventHandler(async (event) => {
  try {
    await flaskFetch('/api/auth/logout', event, { method: 'POST' })
  } catch {
    // Even if Flask fails, clear our cookies locally
  }
  clearAuthCookies(event)
  return { success: true }
})
```

### 11.7 Refresh with rotation

```typescript
// server/api/auth/refresh.post.ts
export default defineEventHandler(async (event) => {
  const refresh = getRefreshToken(event)
  if (!refresh) {
    throw createError({ statusCode: 401, statusMessage: 'No refresh token' })
  }
  const response = await flaskFetch<{ access: string; refresh: string }>(
    '/api/auth/refresh',
    event,
    { method: 'POST', headers: { Authorization: `Bearer ${refresh}` } },
  )
  setAccessCookie(event, response.access)
  setRefreshCookie(event, response.refresh)
  return { success: true }
})
```

### 11.8 Identity endpoint

```typescript
// server/api/auth/me.get.ts
import type { User } from '~/types/user'

export default defineEventHandler(async (event) => {
  const hasAccess = event.context.flaskHeaders !== undefined
  if (!hasAccess) {
    throw createError({ statusCode: 401, statusMessage: 'Not authenticated' })
  }
  const user = await flaskFetch<User>('/api/auth/me', event)
  return { user }
})
```

---

## 12. h3 utilities reference

Essential Nitro/h3 helpers (auto-imported inside `server/`):

| Helper | Purpose |
|---|---|
| `defineEventHandler(handler)` | Define a server route/middleware |
| `readBody(event)` | Parse request body (JSON, form, raw) |
| `readValidatedBody(event, validator)` | Parse + validate; throws 400 on fail |
| `getQuery(event)` | URL query params as object |
| `getRouterParams(event)` / `getRouterParam(event, 'id')` | Dynamic route params |
| `getRequestHeaders(event)` / `getRequestHeader(event, 'name')` | Request headers |
| `getRequestURL(event)` | Full URL object |
| `getCookie(event, name)` | Read a cookie value |
| `setCookie(event, name, value, opts)` | Write a cookie |
| `deleteCookie(event, name, opts)` | Remove a cookie (send Set-Cookie with Max-Age=0) |
| `createError({ statusCode, statusMessage, data })` | Throw to return HTTP error |
| `sendRedirect(event, '/path', 302)` | Redirect response |
| `sendNoContent(event)` | 204 response |
| `proxyRequest(event, url)` | Forward the request to another URL |
| `useStorage('cache:nitro')` | Nitro KV storage (cache, session) |

---

## 13. i18n deep-dive

### 13.1 Configuration

```typescript
i18n: {
  locales: [
    { code: 'en', language: 'en-US', file: 'en.json', name: 'English' },
    { code: 'it', language: 'it-IT', file: 'it.json', name: 'Italiano' },
    { code: 'fr', language: 'fr-FR', file: 'fr.json', name: 'Français' },
    { code: 'es', language: 'es-ES', file: 'es.json', name: 'Español' },
  ],
  defaultLocale: 'en',
  strategy: 'prefix_except_default',              // /, /it/*, /fr/*, /es/*
  detectBrowserLanguage: {
    useCookie: true,
    cookieKey: 'i18n_redirected',
    redirectOn: 'root',                           // Detect only on /
    alwaysRedirect: false,
  },
  lazy: true,                                     // Load only current locale
  langDir: 'locales',
}
```

### 13.2 Component usage

```typescript
<script setup lang="ts">
const { t, locale, locales, setLocale } = useI18n()
const localePath = useLocalePath()
const localeRoute = useLocaleRoute()

const switchLang = (code: string) => setLocale(code as typeof locale.value)
</script>

<template>
  <h1>{{ t('home.hero_title') }}</h1>
  <NuxtLink :to="localePath('/locations')">{{ $t('nav.locations') }}</NuxtLink>

  <select :value="locale" @change="switchLang(($event.target as HTMLSelectElement).value)">
    <option v-for="l in locales" :key="l.code" :value="l.code">{{ l.name }}</option>
  </select>
</template>
```

### 13.3 DB-backed translations

TDC stores long content (location descriptions, event titles, artist bios,
blog posts) in `*_translations` MySQL tables. The UI strings in
`i18n/locales/*.json` are only for navigation and short labels.

Pattern: send `Accept-Language` with every `useFetch` that returns
translatable content, and put the locale in the cache key:

```typescript
const { locale } = useI18n()
const { data: location } = await useFetch<Location>(`/api/locations/${slug}`, {
  headers: { 'Accept-Language': locale.value },
  key: `location-${slug}-${locale.value}`,        // Cache split per locale
})
```

ISR caches are automatically segmented by locale prefix when using
`prefix_except_default` — `/it/locations/xyz` and `/locations/xyz`
have independent cache entries.

### 13.4 Plurals and interpolation

```json
{
  "event": {
    "attending": "no one attending | 1 person | {count} people attending"
  },
  "greeting": "Hello, {name}!"
}
```

```vue
{{ $t('event.attending', 3) }}                     <!-- "3 people attending" -->
{{ $t('greeting', { name: 'Alessandro' }) }}
```

### 13.5 Locale-aware routing

```typescript
// Preserve locale in programmatic nav:
await navigateTo(localePath('/dashboard'))

// Switch locale while staying on the same page:
await setLocale('it')
```

### 13.6 i18n SEO — hreflang

`@nuxtjs/seo` + `@nuxtjs/i18n` emit `<link rel="alternate" hreflang="..." />` tags automatically when configured with `baseUrl`. Set `runtimeConfig.public.siteUrl` and Nuxt handles it.

---

## 14. Tailwind + location theming

### 14.1 Tailwind v4 — CSS-first config (no config file)

TDC uses **Tailwind v4** wired via `@tailwindcss/vite`. There is **no**
`tailwind.config.ts` at project root — tokens are declared in CSS inside
`app/assets/css/main.css` via the `@theme` directive, and Tailwind v4
auto-generates utilities (`bg-primary`, `text-accent`, `font-display`, …)
from any `--color-*`, `--font-*`, `--background-image-*` tokens it finds
there.

The Vite plugin is wired in `nuxt.config.ts`:

```typescript
// nuxt.config.ts
import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  vite: { plugins: [tailwindcss()] },
  css: ['~/assets/css/main.css'],
  // DO NOT add '@nuxtjs/tailwindcss' to modules — v3 module, conflicts with v4.
})
```

### 14.2 `main.css` — tokens + per-location overrides

The single source of truth for TDC visual identity:

```css
/* frontend/app/assets/css/main.css */
@import "tailwindcss";

/* Tokens — @theme so Tailwind generates utilities, indirected through
   --tdc-* CSS vars so [data-location=".."] can override them without
   regenerating utility classes. */
@theme {
  --color-primary:   var(--tdc-color-primary);
  --color-secondary: var(--tdc-color-secondary);
  --color-accent:    var(--tdc-color-accent);
  --color-dark:      var(--tdc-color-dark);
  --color-surface:   var(--tdc-color-surface);

  /* Semantic-state token consumed via `text-error`, `bg-error`,
     `border-error` utilities. Not overridden per location (error has
     universal meaning, palette-agnostic). Added Phase 3 Task 3.6b. */
  --color-error:     var(--tdc-color-error);

  --font-display: "Inter", "system-ui", sans-serif;
  --font-body:    "Inter", "system-ui", sans-serif;

  --background-image-hero-gradient: var(--tdc-gradient-hero);
}

@layer base {
  :root {                        /* default palette (Cosmic/Tech base) */
    --tdc-color-primary:   #0891b2;
    --tdc-color-secondary: #06b6d4;
    --tdc-color-accent:    #22c55e;
    --tdc-color-dark:      #0c1222;
    --tdc-color-surface:   #141420;
    --tdc-color-error:     #ef4444;
    --tdc-gradient-hero:   linear-gradient(135deg, #0891b2, #22c55e, #eab308);
  }

  /* ---- COSMIC / TECH ---------------------------------------------- */
  [data-location="dreamerscave"] {
    --tdc-color-primary:   #0891b2;
    --tdc-color-secondary: #06b6d4;
    --tdc-color-accent:    #22c55e;
    --tdc-gradient-hero:   linear-gradient(135deg, #0891b2, #22c55e, #eab308);
  }
  [data-location="dreamvision"] {
    --tdc-color-primary:   #06b6d4;
    --tdc-color-secondary: #22c55e;
    --tdc-color-accent:    #facc15;
    --tdc-gradient-hero:   linear-gradient(135deg, #06b6d4, #22c55e, #facc15);
  }
  [data-location="evanescence"] {
    --tdc-color-primary:   #8b5cf6;
    --tdc-color-secondary: #a78bfa;
    --tdc-color-accent:    #ec4899;
    --tdc-gradient-hero:   linear-gradient(135deg, #8b5cf6, #ec4899, #facc15);
  }

  /* ---- HYBRID ----------------------------------------------------- */
  [data-location="livemagic"] {
    --tdc-color-primary:   #ef4444;
    --tdc-color-secondary: #f97316;
    --tdc-color-accent:    #06b6d4;
    --tdc-gradient-hero:   linear-gradient(135deg, #ef4444, #f97316, #06b6d4);
  }
  [data-location="thelounge"] {
    --tdc-color-primary:   #db2777;
    --tdc-color-secondary: #7c3aed;
    --tdc-color-accent:    #22d3ee;
    --tdc-gradient-hero:   linear-gradient(135deg, #db2777, #7c3aed, #22d3ee);
  }

  /* ---- WARM / INTIMATE -------------------------------------------- */
  [data-location="arquipelago"] {
    --tdc-color-primary:   #14b8a6;
    --tdc-color-secondary: #22d3ee;
    --tdc-color-accent:    #f97316;
    --tdc-gradient-hero:   linear-gradient(135deg, #14b8a6, #22d3ee, #f97316);
  }
  [data-location="noahsark"] {
    --tdc-color-primary:   #d97706;
    --tdc-color-secondary: #92400e;
    --tdc-color-accent:    #14b8a6;
    --tdc-gradient-hero:   linear-gradient(135deg, #d97706, #fbbf24, #14b8a6);
  }
  [data-location="jazzclub"] {
    --tdc-color-primary:   #92400e;
    --tdc-color-secondary: #78350f;
    --tdc-color-accent:    #14b8a6;
    --tdc-gradient-hero:   linear-gradient(135deg, #92400e, #991b1b, #14b8a6);
  }

  /* Base document styles */
  html {
    background-color: var(--tdc-color-dark);
    color: #ffffff;
  }
  body {
    font-family: var(--font-body);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
}
```

**Slug convention.** All lowercase, no diacritics, no spaces:
`thelounge`, `arquipelago`, `noahsark`, `jazzclub`. UI display names
(`"The Lounge"`, `"Arquipélago"`, `"Noah's Ark"`, `"Jazz Club"`) are
presented at the component layer and never appear as attribute values.

**Gap.** Two of the catalogued "10+ themed venues" have no palette yet
— tracked as `TD-008` in `docs/TECH_DEBT.md`. Pages for non-catalogued
slugs fall back to the `:root` Cosmic/Tech palette; no visual breakage,
just no unique identity until palettes are added.

**Known palette issues (Phase 3 close).**

- **TD-011** — `jazzclub`'s `text-primary` (#92400e) on `bg-dark` fails
  WCAG AA contrast (2.72:1). Exposed the moment a jazzclub-themed
  page ships (none in Phase 3). Candidate fixes: lighten the primary,
  introduce a separate `--tdc-color-chrome` token, or swap to the
  accent colour. Locked until first jazzclub route.
- **TD-013** — `livemagic`'s `--tdc-color-primary: #ef4444` is
  identical to the global `--tdc-color-error: #ef4444`. On any
  livemagic-themed page, error badges and primary CTAs lose semantic
  distinction. Candidate fixes: darken `--tdc-color-error` globally,
  give error states a container surface (`bg-error/10 border
  border-error`), or shift the livemagic primary.

### 14.3 SSR-safe theme switch

```typescript
// app/composables/useLocationTheme.ts
export function useLocationTheme(
  slug: Ref<string | null | undefined> | string | null | undefined,
) {
  const slugRef = isRef(slug) ? slug : ref(slug ?? null)

  useHead(() => ({
    bodyAttrs: { 'data-location': slugRef.value ?? undefined },
  }))
}

// In a page:
const { data: location } = await useFetch<Location>(`/api/locations/${slug}`)
useLocationTheme(computed(() => location.value?.slug))
```

`useHead` sets `body[data-location="..."]` in the SSR HTML. CSS vars cascade immediately — **no JavaScript at paint time, zero flash**.

### 14.4 Mood categories

| Mood | Character | Locations |
|---|---|---|
| **Cosmic/Tech** | Cyan/green/yellow gradients, electronic/futuristic | DreamersCave, DreamVision, Evanescence |
| **Hybrid** | Mixed cool+warm palettes, eclectic | LiveMagic, The Lounge |
| **Warm/Intimate** | Amber/red/teal, jazz/folk/acoustic | Arquipélago, Noah's Ark, Jazz Club |

When adding a new location, place its CSS vars under the matching mood.

### 14.5 Semantic-state tokens

Aside from the per-location palette tokens, TDC maintains a small set
of **palette-agnostic** semantic tokens. `--color-error` is the first
one, landed in Task 3.6b when the locations list needed to render
`text-error` on the failure branch.

**Pattern:** when a new semantic meaning surfaces (e.g. success,
warning, info, destructive action), add the token to `@theme` + the
global default under `:root` **in the same task that needs it**, not
in a future "tokens consolidation" pass. Consolidation into
`docs/DESIGN.md` is TD-007 — but blocking progress on consolidation
creates cascading delays. The phase-3 precedent is to add-then-reuse.

**Active semantic tokens (as of Phase 3):**

| Utility | CSS var | Default | Overridden per location? |
|---|---|---|---|
| `text-primary` / `bg-primary` | `--color-primary` → `--tdc-color-primary` | `#0891b2` | Yes |
| `text-secondary` / `bg-secondary` | `--color-secondary` → `--tdc-color-secondary` | `#06b6d4` | Yes |
| `text-accent` / `bg-accent` | `--color-accent` → `--tdc-color-accent` | `#22c55e` | Yes |
| `text-dark` / `bg-dark` | `--color-dark` → `--tdc-color-dark` | `#0c1222` | No |
| `bg-surface` | `--color-surface` → `--tdc-color-surface` | `#141420` | No |
| `text-error` / `bg-error` / `border-error` | `--color-error` → `--tdc-color-error` | `#ef4444` | **No** (universal) |
| `bg-hero-gradient` | `--background-image-hero-gradient` → `--tdc-gradient-hero` | cyan→green→yellow | Yes |

`--tdc-color-error` is intentionally outside any `[data-location=...]`
block because error semantics must not vary by location. See TD-013
for the `livemagic` primary collision with the global error colour.

---

## 15. SEO patterns

### 15.1 `useSeoMeta` on every public page

```typescript
useSeoMeta({
  title: location.value?.name,
  description: location.value?.short_description,
  ogTitle: location.value?.name,
  ogDescription: location.value?.short_description,
  ogImage: location.value?.hero_image,
  ogType: 'website',
  twitterCard: 'summary_large_image',
})
```

Reactive — updates during SSR and on client navigation.

### 15.2 `useHead` for arbitrary head tags

```typescript
const route = useRoute()
useHead({
  link: [
    { rel: 'canonical', href: `https://thedreamerscave.club${route.path}` },
  ],
})
```

### 15.3 Schema.org with `useSchemaOrg`

**Location page:**
```typescript
useSchemaOrg([
  defineOrganization({
    name: "The Dreamer's Cave",
    url: 'https://thedreamerscave.club',
    logo: '/logo.png',
    sameAs: [
      'https://facebook.com/thedreamerscave',
      'https://secondlife.com/.../thedreamerscave',
    ],
  }),
  definePlace({
    name: location.value?.name,
    description: location.value?.description,
    image: location.value?.hero_image,
  }),
])
```

**Event page:**
```typescript
useSchemaOrg([
  defineEvent({
    name: event.value?.title,
    startDate: event.value?.starts_at,
    endDate: event.value?.ends_at,
    description: event.value?.description,
    image: event.value?.poster_image,
    location: {
      '@type': 'VirtualLocation',
      url: event.value?.sl_url,
    },
    performer: event.value?.artists?.map(a => ({
      '@type': 'MusicGroup',
      name: a.name,
      sameAs: a.social_links,
    })),
  }),
])
```

**Blog post:**
```typescript
useSchemaOrg([
  defineArticle({
    headline: post.value?.title,
    datePublished: post.value?.published_at,
    dateModified: post.value?.updated_at,
    author: { '@type': 'Person', name: post.value?.author_name },
    image: post.value?.cover_image,
  }),
])
```

### 15.4 Sitemap

`@nuxtjs/sitemap` auto-generates `/sitemap.xml` from:
- Prerendered routes (from `nitro.prerender.routes` + crawled links)
- Configured dynamic routes

For DB-backed dynamic routes, provide a custom source:

```typescript
// server/api/__sitemap__/urls.get.ts
export default defineSitemapEventHandler(async () => {
  const locations = await $fetch<{ slug: string; updated_at: string }[]>('/api/locations')
  return locations.map(l => ({
    loc: `/locations/${l.slug}`,
    lastmod: l.updated_at,
  }))
})
```

### 15.5 Robots

```typescript
robots: {
  disallow: ['/dashboard', '/admin', '/api/auth'],
}
```

---

## 16. Images (`@nuxt/image`)

```vue
<NuxtImg
  :src="location.hero_image"
  :alt="location.name"
  width="1920"
  height="1080"
  sizes="sm:100vw md:50vw lg:33vw"
  format="webp"
  loading="lazy"
  placeholder
/>

<!-- Above-the-fold hero -->
<NuxtImg
  :src="location.hero_image"
  :alt="location.name"
  width="1920"
  height="1080"
  sizes="100vw"
  format="avif,webp,jpg"
  loading="eager"
  fetchpriority="high"
/>
```

- Always set `width`/`height` → avoids CLS
- `sizes` uses Tailwind breakpoint prefixes (`sm:`, `md:`, `lg:`)
- `format` list enables best-supported-first (avif → webp → fallback)
- For complex art direction: `<NuxtPicture>` with multiple `<source>`

Providers are configurable (default: built-in IPX). For external CDN, configure `image.provider` in `nuxt.config.ts`.

---

## 17. Forms (vee-validate + zod)

### 17.1 Canonical form

```vue
<script setup lang="ts">
import { z } from 'zod'
import { toTypedSchema } from '@vee-validate/zod'
import { useForm } from 'vee-validate'

const schema = toTypedSchema(
  z.object({
    email: z.string().email('Invalid email'),
    password: z.string().min(8, 'Minimum 8 characters'),
    rememberMe: z.boolean().default(false),
  }),
)

const { handleSubmit, errors, defineField, isSubmitting } = useForm({
  validationSchema: schema,
})

const [email, emailAttrs] = defineField('email')
const [password, passwordAttrs] = defineField('password')
const [rememberMe, rememberMeAttrs] = defineField('rememberMe')

const { login } = useAuth()

const onSubmit = handleSubmit(async (values) => {
  try {
    await login(values.email, values.password)
    await navigateTo('/dashboard')
  } catch (e) {
    // Map Flask errors back to field errors if needed
  }
})
</script>

<template>
  <form @submit="onSubmit" class="space-y-4 max-w-md">
    <div>
      <label for="email" class="block text-sm mb-1">Email</label>
      <input
        id="email"
        v-model="email"
        v-bind="emailAttrs"
        type="email"
        autocomplete="email"
        :aria-invalid="!!errors.email"
        :aria-describedby="errors.email ? 'email-error' : undefined"
        class="w-full px-4 py-3 bg-surface rounded-lg border border-white/10
               focus:border-primary focus:ring-2 focus:ring-primary/50"
      />
      <p v-if="errors.email" id="email-error" class="text-error text-sm mt-1">
        {{ errors.email }}
      </p>
    </div>

    <!-- Password similar -->

    <button
      type="submit"
      :disabled="isSubmitting"
      class="w-full py-3 bg-primary hover:bg-secondary rounded-lg
             disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
    >
      <span v-if="isSubmitting">…</span>
      <span v-else>Sign in</span>
    </button>
  </form>
</template>
```

### 17.2 Why zod

The same schema validates on Flask-side (if Flask uses a matching JSON schema) AND the Nuxt BFF server routes use it via `readValidatedBody`. One source of truth for client UX + server enforcement.

### 17.3 Complex forms

For multi-step or nested forms, use `useForm` at the top level and pass `defineField` results down to child components via props. Keep one form per logical submission.

---

## 18. TipTap editor

```vue
<script setup lang="ts">
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    StarterKit,
    Image,
    Link.configure({ openOnClick: false }),
    Placeholder.configure({ placeholder: 'Start writing…' }),
  ],
  onUpdate: ({ editor }) => emit('update:modelValue', editor.getHTML()),
})

// Keep editor in sync if parent changes the value externally
watch(() => props.modelValue, (newValue) => {
  if (editor.value && editor.value.getHTML() !== newValue) {
    editor.value.commands.setContent(newValue, false)
  }
})

onBeforeUnmount(() => editor.value?.destroy())
</script>

<template>
  <ClientOnly>
    <div class="border border-white/10 rounded-lg">
      <EditorContent :editor="editor" class="prose prose-invert p-4" />
    </div>
    <template #fallback>
      <div class="border border-white/10 rounded-lg h-64 bg-surface/50" aria-hidden="true" />
    </template>
  </ClientOnly>
</template>
```

**Rules:**
- Always inside `<ClientOnly>` or a page with `ssr: false`. TipTap references `document` and `window` extensively.
- Always call `editor.destroy()` in `onBeforeUnmount` — otherwise listeners leak.
- For large posts, consider lazy-loading the TipTap module: `defineAsyncComponent(() => import('./BlogEditor.vue'))`.

---

## 19. Testing (vitest + Playwright)

### 19.1 vitest config

```typescript
// vitest.config.ts
import { defineVitestConfig } from '@nuxt/test-utils/config'

export default defineVitestConfig({
  test: {
    environment: 'happy-dom',
    globals: true,
    include: ['tests/**/*.test.ts'],
  },
})
```

Scripts:
```json
"scripts": {
  "test": "vitest run",
  "test:watch": "vitest"
}
```

### 19.2 Unit test — pure logic

```typescript
// tests/unit/flask-client.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { H3Event } from 'h3'

const fetchMock = vi.fn()
;(globalThis as any).$fetch = fetchMock
;(globalThis as any).useRuntimeConfig = () => ({ flaskUrl: 'http://flask.test' })

import { flaskFetch } from '../../server/utils/flask-client'

describe('flaskFetch', () => {
  beforeEach(() => {
    fetchMock.mockReset()
    fetchMock.mockResolvedValue({ ok: true })
  })

  it('forwards flaskHeaders from event.context', async () => {
    const event = { context: { flaskHeaders: { Authorization: 'Bearer x' } } } as unknown as H3Event
    await flaskFetch('/api/x', event)
    expect(fetchMock).toHaveBeenCalledWith('/api/x', expect.objectContaining({
      baseURL: 'http://flask.test',
      headers: expect.objectContaining({ Authorization: 'Bearer x' }),
    }))
  })
})
```

### 19.3 Component test — `@nuxt/test-utils/runtime`

```typescript
import { describe, it, expect } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import LocationCard from '~/components/locations/LocationCard.vue'

describe('LocationCard', () => {
  it('renders location name', async () => {
    const wrapper = await mountSuspended(LocationCard, {
      props: {
        location: {
          id: 1,
          slug: 'dreamerscave',
          name: "Dreamer's Cave",
          mood: 'cosmic',
          capacity: 100,
          hero_image: null,
          description: null,
          created_at: '2026-01-01',
        },
      },
    })
    expect(wrapper.text()).toContain("Dreamer's Cave")
  })
})
```

### 19.4 E2E test — Playwright

Follow CLAUDE.md: **1920x1080 resolution always**, prefer the MCP Playwright tools when running inside agents.

```typescript
// tests/e2e/login.spec.ts
import { test, expect } from '@playwright/test'

test('login flow sets HttpOnly cookies and redirects', async ({ page, context }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })

  await page.goto('http://localhost:9503/auth/login')
  await page.fill('[name="email"]', 'test@tdc.local')
  await page.fill('[name="password"]', 'test')
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard')

  const cookies = await context.cookies()
  const access = cookies.find(c => c.name === 'tdc_access')
  expect(access?.httpOnly).toBe(true)
  expect(access?.sameSite).toBe('Lax')
})
```

### 19.5 Testing philosophy

- **Unit tests** for pure logic: composables, stores, utils, server handlers, schemas
- **Component tests** for reusable primitives (Button, Input, Modal) — not entire pages
- **E2E** for critical user journeys: login, favorite toggle, admin publish → ISR revalidate, language switching
- **Don't test the framework** — trust that `useFetch` does what it says. Test YOUR logic around it.

### 19.6 What NOT to test

- Nuxt / Vue / Pinia internals
- Trivial passthroughs (component that just renders a prop)
- Styling (covered by visual regression, not unit tests)

---

## 20. Accessibility (WCAG 2.1 AA)

Mandatory disciplines (violation = PR reject):

- **Images**: every `<img>` has meaningful `alt` or `alt=""` (decorative)
- **Interactive elements**: `<button>` for actions, `<a>` for navigation, OR proper `role` + keyboard handlers
- **Focus**: always-visible focus styles (`focus-visible:outline-2 focus-visible:outline-primary`)
- **Labels**: `<label for="x">` linked to `<input id="x">`; icon-only buttons have `aria-label`
- **Errors**: field errors via `aria-describedby="..._error"` + `aria-invalid="true"`
- **Landmarks**: `<header>`, `<nav>`, `<main>` (exactly one), `<footer>`
- **Headings**: hierarchical (`h1` → `h2` → `h3`), one `h1` per page
- **Color contrast**: 4.5:1 body text, 3:1 large text. Verify accent colors on location themes.
- **Keyboard**: Tab order matches visual flow; `Esc` closes modals; `Enter` submits forms
- **Announcements**: use `aria-live="polite"` for toasts; `aria-live="assertive"` only for critical errors
- **Skip link**: `<a href="#main" class="skip-link">Skip to content</a>` at top of `<body>`
- **Motion**: respect `prefers-reduced-motion` — disable Lenis and heavy GSAP for users who opt in

Testing: use `tdc-accessibility-tester` agent with Playwright for WCAG audits.

---

## 21. Performance (Core Web Vitals)

### 21.1 Targets

| Metric | Target | Measurement |
|---|---|---|
| LCP | < 2.5s | Lab: Lighthouse; field: RUM |
| CLS | < 0.1 | Same |
| INP | < 200ms | Same |
| TTFB | < 600ms | For SSR pages |

### 21.2 Levers

**LCP:**
- Prerender the home page (SSG)
- Eager-load hero images (`loading="eager"`, `fetchpriority="high"`)
- Preload hero fonts: `<link rel="preload" as="font" href="..." crossorigin>`
- Use `@nuxt/image` avif/webp for lighter payloads

**CLS:**
- Always set `width`/`height` on images
- Reserve space for dynamic content (skeletons with matching dimensions)
- Avoid injecting content above existing elements

**INP:**
- Debounce input handlers: `const debounced = useDebounceFn(handler, 200)` from `@vueuse/core`
- Avoid heavy computed chains; memoize with `computed(() => ...)` at the right granularity
- Defer non-critical work to `requestIdleCallback`

### 21.3 Bundle hygiene

- Named imports: `import { Menu } from 'lucide-vue-next'` (never `* as`)
- Dynamic imports for heavy client-only deps:
  ```typescript
  const BlogEditor = defineAsyncComponent(() => import('./BlogEditor.vue'))
  ```
- Check bundle: `npm run build` → inspect `.output/public/_nuxt/` sizes. Anything > 200KB gzipped → investigate.

### 21.4 Loading strategy

- Above-the-fold images: eager, priority
- Below-the-fold: lazy (default)
- Footer links: `<NuxtLink :prefetch="false">` to avoid prefetching rarely-used pages
- Modals, admin widgets: lazy-load via `defineAsyncComponent`

---

## 22. Common task recipes

### 22.1 Create a new public page (SSG)

1. Create `app/pages/<path>.vue`
2. `<script setup lang="ts">`, fetch with `useFetch` + explicit `key`
3. Add `useSeoMeta({ title, description, ogImage })`
4. Optional: `useSchemaOrg([...])` for rich results
5. If themed by location, call `useLocationTheme(computed(() => location.value?.slug))`
6. Add to `routeRules` in `nuxt.config.ts` → `{ prerender: true }`
7. Verify SSR: `curl http://localhost:9503/<path> | grep <expected-text>`
8. Commit: `feat(frontend): add <path> page`

### 22.2 Create an auth-gated page (SPA)

1. Create `app/pages/dashboard/<name>.vue`
2. `definePageMeta({ middleware: ['auth'], layout: 'dashboard' })`
3. Use `useApi()` composable for fetches (auto 401 → refresh)
4. No `useSeoMeta` needed (robots disallow covers it)
5. `routeRules` already covers `/dashboard/**` with `ssr: false`
6. Commit: `feat(frontend): add dashboard/<name>`

### 22.3 Add a new location

1. Admin UI → DB insert
2. Add CSS vars block to `app/assets/css/main.css` under the right mood section
3. After save: client POSTs `/api/revalidate { path: '/locations/<slug>' }`
4. Next visitor sees fresh page
5. Commit CSS changes: `feat(frontend): add theme for <slug> location`

### 22.4 Add a new locale

1. Add to `nuxt.config.ts` `i18n.locales` array
2. Create `i18n/locales/<code>.json` with all keys from `en.json` translated
3. Verify DB `*_translations` tables have rows for the new language column
4. Test `/<code>/` serves localized content
5. Commit: `feat(frontend): add <language> locale`

### 22.5 Debug a hydration mismatch

1. Open browser DevTools → Console → find the red Vue warning (names the component)
2. In that component, scan for: `Date`, `Math.random`, `window`, `navigator`, `localStorage` in template or setup top-level
3. Fix with one of:
   - `ref` + `onMounted` assign
   - `<ClientOnly>` wrapper + `#fallback` matching shape
   - Move to `.client.ts` plugin if it's third-party
4. Reload, verify warning is gone
5. Commit: `fix(frontend): hydration mismatch in <component>`

### 22.6 Add a server route (BFF)

1. Create `server/api/<path>.<method>.ts`
2. Use `defineEventHandler(async (event) => { ... })`
3. Validate input with `readValidatedBody(event, zodSchema.parse)` if it has a body
4. Call Flask with `flaskFetch(url, event, options)` — event threading is mandatory
5. Return JSON (just `return { ... }`)
6. Write a unit test in `tests/unit/` (TDD preferred)
7. Commit: `feat(frontend): add <path> server route`

### 22.7 Add rendering strategy for a new route

1. Decide strategy based on content volatility + SEO need (see §6 table)
2. Add entry to `routeRules` in `nuxt.config.ts`
3. If SSG: verify the route is linked from a prerendered page (or add to `nitro.prerender.routes`)
4. If ISR with on-demand: wire admin save → `/api/revalidate`
5. Commit: `feat(frontend): configure rendering for <path>`

### 22.8 Write a new composable

1. Create `app/composables/use<Name>.ts`
2. Export as named function: `export function useXxx() { ... }`
3. Use Nuxt auto-imports (no explicit `import` for `ref`, `computed`, etc.)
4. Guard client-only code with `if (!import.meta.client) return` if applicable
5. Return a plain object of refs/functions
6. Unit test in `tests/unit/useXxx.test.ts`
7. Commit: `feat(frontend): add useXxx composable`

### 22.9 Integrate a new Pinia store

1. Create `app/stores/<name>.ts`
2. Use **setup syntax**: `defineStore('name', () => { /* refs, computed, functions */ return {...} })`
3. In components: destructure with `storeToRefs(store)` for reactive state
4. Commit: `feat(frontend): add <name> Pinia store`

### 22.10 Promote a feature from ISR to SSG

1. Change `routeRules` entry from `{ swr: 300 }` → `{ prerender: true }`
2. Ensure admin save triggers `/api/revalidate` for the affected path
3. Verify build generates the static pages (`npm run build` + inspect `.output/public`)
4. Commit: `perf(frontend): prerender <route>`

---

## 23. Pattern library (Phase 3+)

Phase 3 established a set of cross-page patterns that every new
public-facing list/detail/error surface is expected to honour from
the first commit (no "we'll polish later" iteration). Review the
checklist before opening a PR that adds a page or component.

### 23.1 Preemptive-polish 7-point checklist (list / detail pages)

The pattern surfaced by tasks 3.6 → 3.6b → 3.7. After Task 3.6b the
design-system reviewer flagged zero blocking findings on Task 3.7
because the polish shape was applied up-front. Each point is easy to
forget in isolation; together they are the difference between a
reviewer-approved page and a design-system `b`-task rework.

1. **i18n everywhere.** No English literal in template or in
   `useSeoMeta(...)` (exception: brand-integrity strings like
   `ogTitle: "The Dreamer's Cave"`). Every user-visible string
   comes from `t('namespace.key')` or `$t('namespace.key')`.
   Pair the page with a plan amendment that adds keys to all 4
   locale JSONs in the same task.
2. **Semantic error colour.** Error branches use `text-error`
   (semantic state token, §14.5) — never `text-red-400` or any
   raw hex / default Tailwind palette token.
3. **Three-state template.** Always handle `error`, populated, and
   empty separately:
   ```vue
   <div v-if="error" role="alert" class="text-error">
     {{ t('x.error.load_failed') }}: {{ error.statusMessage }}
   </div>
   <div v-else-if="items && items.length" class="grid …">…</div>
   <div v-else class="text-white/70">{{ t('x.empty') }}</div>
   ```
   Skipping the empty state leaves a blank page on a legitimate
   zero-item response — indistinguishable from a silent failure.
4. **Null-guard optional fields.** When rendering DB-sourced text
   that may be `null`, gate the element with `v-if`:
   ```vue
   <p v-if="location.description">{{ location.description }}</p>
   ```
   Skipping the guard renders an empty `<p>` and shifts following
   content when data is missing.
5. **Locale-aware internal links.** Every `<NuxtLink :to="...">`
   pointing at an internal path goes through `useLocalePath()`:
   ```vue
   <script setup>
   const localePath = useLocalePath()
   </script>
   <NuxtLink :to="localePath(`/locations/${slug}`)">…</NuxtLink>
   ```
   Forgetting this on IT/FR/ES routes strips the locale prefix and
   sends users to the English page.
6. **Focus-visible ring on every interactive surface.** Buttons,
   links, and `NuxtLink` wrappers all carry the 5-class chain:
   ```
   focus-visible:outline-none focus-visible:ring-2
   focus-visible:ring-primary focus-visible:ring-offset-2
   focus-visible:ring-offset-dark
   ```
   Promotion to an `@layer components` alias is scheduled for
   whenever 5+ distinct consumers exist (TD-007 consolidation
   will formalize this — for now, copy the chain).
7. **Pure `@theme` tokens.** No raw hex in templates. No default
   Tailwind palette utilities (`text-red-400`, `bg-gray-700`,
   `text-blue-500`) — every colour is a TDC `@theme` token. If
   the token you need doesn't exist yet, add it in the same task
   (§14.5 semantic-token pattern).

Reference implementations:

- `frontend/app/pages/locations/index.vue` (Task 3.6b, list with
  grid card layout)
- `frontend/app/pages/events/index.vue` (Task 3.7, list with
  stacked `<ul>`)
- `frontend/app/pages/index.vue` (Task 3.5b, single-section home
  with SEO meta bound to i18n)
- `frontend/app/error.vue` (Task 3.2b, global error page with
  `role="alert"` and `<main>` landmark)

### 23.2 `role="alert"` standardization

Every error surface in TDC uses `role="alert"` on the container div
so screen readers announce it as a live region. This includes:

- `frontend/app/error.vue` (root error page)
- `frontend/app/pages/locations/index.vue` (list error branch)
- `frontend/app/pages/events/index.vue` (list error branch)

Add `role="alert"` to the container `<div>` that wraps the error
message, not to the text element inside. When adding a new page with
an error branch, include `role="alert"` from the first commit.

### 23.3 Controller micro-edit threshold

Scan row 31 codified a threshold for when the controller may edit a
file directly rather than dispatching a new implementer subagent.
Document it here so subagents know when their dispatch was
appropriate vs when a micro-edit would have sufficed.

**A change is eligible for controller micro-edit when ALL hold:**

- Change touches ≤3 lines.
- Change adds zero new behaviour (wraps existing behaviour, adds a
  guard, narrows a class list, swaps a string for an i18n key).
- Change does not introduce a new surface, new composable, new
  type, or new dependency.
- Change is verifiable by typecheck + existing tests (no new test
  needed).

**Phase 3 micro-edit precedents (all approved by user in situ):**

- `pages/index.vue` subtitle `text-xl md:text-2xl` → `text-2xl`
  (1-word removal for AA-large contrast).
- `pages/locations/index.vue` `NuxtLink :to="/locations/${slug}"` →
  `:to="localePath(\`/locations/${slug}\`)"` + `const localePath =
  useLocalePath()` in setup (2 lines).
- `useScrollAnimation.ts` reduced-motion guard (3-line early-return).

Anything more complex goes back through a subagent dispatch.

### 23.4 Plan authoring: check cross-task consistency up front

Phase 3 surfaced two plan-internal contradictions (scan §C.3):

- Task 3.2 layout referenced `<AppHeader />` (unprefixed) but Task 3.3
  placed the file at `app/components/common/AppHeader.vue`, which
  Nuxt 4 default naming registers as `<CommonAppHeader />`.
- Task 3.3 AppFooter template had `{{ new Date().getFullYear() }}`
  with a "stable across SSR and hydration" note — conflicting with
  CLAUDE.md SSR Rule #4 (non-negotiable forbiddance of `new Date()`
  in templates).

When authoring a plan, pre-check: (a) every component reference's
auto-import name matches its filesystem path under the configured
`components` rules, (b) every template fragment honours CLAUDE.md SSR
rules. Both contradictions cost implementation time that could have
been saved by a 10-minute consistency pass during plan authoring.

### 23.5 Date rendering — deferred to `useFormattedDate`

Raw ISO 8601 (`{{ event.starts_at }}`) is SSR-safe but developer-
shaped, not user-friendly. The safe locale-aware pattern is a
composable:

```typescript
// future: app/composables/useFormattedDate.ts  (TD-012)
export function useFormattedDate(iso: MaybeRef<string>, locale?: MaybeRef<string>) {
  // Run formatting inside computed() with a fixed timeZone (or an
  // explicit ref+onMounted pattern) so SSR and client produce
  // identical output. Unit-test the SSR/client parity.
}
```

Until TD-012 closes, pages render `<time :datetime="iso">{{ iso }}</time>`
— datetime attribute is machine-readable, the visible text is the raw
ISO. Acceptable for developer-shaped surfaces (events list) but blocks
on event detail + calendar pages.

---

## End of playbook

Maintenance:
- When a new pattern is adopted project-wide, update the corresponding section here AND cross-reference from the agent file.
- When a pattern is deprecated, remove it from both files.
- Keep the TOC line numbers roughly synced (run `grep -nE '^## [0-9]+' docs/frontend/nuxt-playbook.md` to check).
