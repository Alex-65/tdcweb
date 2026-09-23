import type { User } from '~/types/user'

/**
 * Pure helpers backing the `auth` / `admin` / `staff` route middleware.
 *
 * Why pure functions: the middleware files are thin wrappers around
 * `defineNuxtRouteMiddleware` (a Nuxt auto-import that vitest cannot
 * easily intercept; see `tests/unit/useApiFetch.test.ts` lines 4-12 for
 * the same rationale). Extracting the role-decision logic and the
 * redirect-URL construction into pure functions lets us unit-test
 * exhaustively without booting the Nuxt runtime, while the middleware
 * file just glues these helpers to `navigateTo` / `createError`.
 */

/**
 * Discriminated union describing what a guard decided to do, in terms
 * the middleware wrapper can translate to `navigateTo` / `createError` /
 * pass-through.
 *
 * `passthrough` -> wrapper returns nothing (route continues).
 * `redirect`    -> wrapper calls `navigateTo(payload.to)`.
 * `forbid`      -> wrapper throws `createError({ statusCode: 403, ... })`.
 */
export type GuardOutcome =
  | { kind: 'passthrough' }
  | { kind: 'redirect'; to: string }
  | { kind: 'forbid'; statusMessage: string }

/**
 * Build the `/auth/login?redirect=<encoded>` URL that the guards send
 * unauthenticated users to. We URL-encode the destination so paths
 * containing query strings (`/dashboard?tab=profile`), hashes, or any
 * non-ASCII characters survive the round-trip and the login page can
 * faithfully bounce the user back after success.
 *
 * `encodeURIComponent` is the right encoder for a query parameter value:
 * it escapes `?`, `&`, `=`, `#` and reserved chars that would otherwise
 * confuse the query parser on the receiving side. `URLSearchParams` is
 * an alternative but it would also encode `/` as %2F which, while
 * technically correct, is uglier in URLs and breaks naive log-grepping.
 */
export function buildLoginRedirect(fullPath: string): string {
  return `/auth/login?redirect=${encodeURIComponent(fullPath)}`
}

/**
 * Decide what `auth` middleware should do given the post-fetchMe user
 * state. `auth` allows ANY authenticated user; only guests get bounced.
 */
export function decideAuthOutcome(
  user: User | null,
  fullPath: string,
): GuardOutcome {
  if (!user) {
    return { kind: 'redirect', to: buildLoginRedirect(fullPath) }
  }
  return { kind: 'passthrough' }
}

/**
 * Decide what `admin` middleware should do. Guests bounce to login (so
 * they can authenticate and try again); authenticated non-admins get a
 * 403 (they're known users who simply lack the role -- redirecting them
 * to /auth/login would be a misleading UX).
 */
export function decideAdminOutcome(
  user: User | null,
  fullPath: string,
): GuardOutcome {
  if (!user) {
    return { kind: 'redirect', to: buildLoginRedirect(fullPath) }
  }
  if (user.role !== 'admin') {
    return { kind: 'forbid', statusMessage: 'Admin only' }
  }
  return { kind: 'passthrough' }
}

/**
 * Decide what `staff` middleware should do. Admin counts as staff
 * (matches `useAuthStore.isStaff` computed: `role === 'staff' || 'admin'`).
 * The role hierarchy is admin > staff > user, so admin must be allowed
 * anywhere staff is allowed.
 */
export function decideStaffOutcome(
  user: User | null,
  fullPath: string,
): GuardOutcome {
  if (!user) {
    return { kind: 'redirect', to: buildLoginRedirect(fullPath) }
  }
  if (user.role !== 'staff' && user.role !== 'admin') {
    return { kind: 'forbid', statusMessage: 'Staff only' }
  }
  return { kind: 'passthrough' }
}
