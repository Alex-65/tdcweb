import type { User } from '~/types/user'

/**
 * Client-side auth composable. Wraps `useAuthStore` so the rest of the app
 * never reaches into Pinia directly, and centralises the three BFF calls
 * (`/api/auth/login`, `/api/auth/logout`, `/api/auth/me`) in one place.
 *
 * SSR cookie-forwarding contract for `fetchMe`:
 *   When this composable is invoked from a Nuxt route middleware during
 *   SSR (e.g. the `auth`/`admin`/`staff` guards), a raw `$fetch` does NOT
 *   forward the incoming request's `Cookie` header to the internal
 *   `/api/auth/me` Nitro route. The internal handler then sees no
 *   `tdc_access` cookie, the `auth-forward` server middleware leaves
 *   `event.context.flaskHeaders` undefined, and the chain returns 401 --
 *   so an authenticated user appears as a guest on every SSR pass and
 *   every protected page redirects to `/auth/login`.
 *
 *   `useRequestFetch()` returns a `$fetch` instance pre-bound to the
 *   current H3Event so SSR calls inherit the original request's cookies.
 *   On the client it's a no-op pass-through to `$fetch`. We use it for
 *   all three BFF calls for consistency, even though `login`/`logout`
 *   only ever run on the client (form submission handlers).
 *
 * Testing strategy:
 *   The Nuxt vitest environment auto-imports `useAuthStore`,
 *   `useRequestFetch`, `storeToRefs` via the unimport transformer, which
 *   makes intercepting them at test time fragile (see comments in
 *   `tests/unit/useApiFetch.test.ts` lines 4-12). The non-trivial
 *   behaviour therefore lives in the pure `buildAuthOps` helper below,
 *   which receives its dependencies as arguments and is exhaustively
 *   unit-tested in `tests/unit/useAuth.test.ts`. The exported
 *   `useAuth()` function is a thin wire-up of the auto-imports to the
 *   helper.
 */

/**
 * Minimal contract the auth helper needs from the Pinia store. Lets us
 * test `buildAuthOps` without booting Pinia / a Nuxt app instance.
 */
export interface AuthStoreLike {
  setUser: (u: User | null) => void
  clear: () => void
}

/**
 * Build the three BFF operations against an arbitrary store + fetch.
 * Pure: no Nuxt auto-imports, no globals, no side effects beyond what
 * the injected dependencies do. All three operations live here so the
 * fetchMe / login / logout error semantics (graceful guest fallback,
 * bubble login errors, clear-store-even-on-logout-failure) can be
 * tested in isolation.
 */
export function buildAuthOps(
  store: AuthStoreLike,
  fetcher: <T>(url: string, opts?: { method?: string; body?: unknown }) => Promise<T>,
) {
  /**
   * Hydrate the store from the BFF. Used by route middleware on first
   * navigation when the store is empty.
   *
   * Failure modes (401 from BFF when no/expired cookie, network error,
   * etc.) are swallowed by design: a guest visiting a public page must
   * not crash the request. The store is cleared so downstream computed
   * (`isAuthenticated`) correctly report guest status.
   */
  const fetchMe = async (): Promise<User | null> => {
    try {
      const response = await fetcher<{ user: User }>('/api/auth/me')
      store.setUser(response.user)
      return response.user
    } catch {
      store.clear()
      return null
    }
  }

  /**
   * POST credentials to the BFF. The BFF sets HttpOnly cookies (access
   * 15min Lax, refresh 7d Strict Path=/api/auth) and returns the user
   * payload. We mirror it into the store so the UI updates without a
   * follow-up `fetchMe` round-trip.
   *
   * Errors (400 validation, 401 bad credentials) bubble unchanged so the
   * caller's form can surface them; the store is left untouched so a
   * failed retry doesn't wipe a previous successful session.
   */
  const login = async (email: string, password: string): Promise<User> => {
    const response = await fetcher<{ user: User }>('/api/auth/login', {
      method: 'POST',
      body: { email, password },
    })
    store.setUser(response.user)
    return response.user
  }

  /**
   * POST to the BFF (which clears cookies and forwards to Flask) then
   * clear the local store. We clear unconditionally on completion via
   * `try/finally`: even if the BFF call throws (network blip), the
   * local UI must reflect a logged-out state. The BFF handler itself
   * already clears cookies in its `catch`, mirroring this resilience.
   */
  const logout = async (): Promise<void> => {
    try {
      await fetcher<{ success: true }>('/api/auth/logout', { method: 'POST' })
    } finally {
      store.clear()
    }
  }

  return { fetchMe, login, logout }
}

/**
 * Composable wrapper. Wires the Nuxt auto-imports (`useAuthStore`,
 * `useRequestFetch`, `storeToRefs`) to `buildAuthOps`, exposes the
 * reactive accessors, and returns a stable surface for components and
 * route middleware.
 */
export function useAuth() {
  const store = useAuthStore()
  const requestFetch = useRequestFetch()
  const { user, isAuthenticated, isAdmin, isStaff } = storeToRefs(store)

  // `useRequestFetch`'s call signature is the standard $fetch one
  // (`(url, opts?) => Promise<T>`). The narrow signature `buildAuthOps`
  // accepts is a structural subset, so the cast is type-safe.
  const ops = buildAuthOps(
    store,
    requestFetch as <T>(url: string, opts?: { method?: string; body?: unknown }) => Promise<T>,
  )

  return {
    user,
    isAuthenticated,
    isAdmin,
    isStaff,
    ...ops,
  }
}
