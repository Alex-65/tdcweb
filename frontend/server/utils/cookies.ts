/**
 * cookies.ts — Auth cookie helpers for the Nuxt BFF.
 *
 * The Dreamer's Cave uses a Hybrid BFF auth pattern (spec §8):
 *   - Flask issues and validates JWTs.
 *   - Nuxt's `server/api/auth/**` handlers receive raw tokens from Flask
 *     and write them back to the browser as HttpOnly cookies. Subsequent
 *     requests hit Nuxt with the cookies, `server/middleware/auth-forward`
 *     (Task 2.7) reads `tdc_access`, and `flaskFetch` (Task 2.6) attaches
 *     it as `Authorization: Bearer <jwt>` on every outbound Flask call.
 *
 * Two cookies, two scopes (spec §8.2):
 *   - `tdc_access` (15 min, SameSite=Lax, Path=/):
 *     sent on every request — page loads, API calls, etc. — so the BFF can
 *     forward auth.
 *   - `tdc_refresh` (7 days, SameSite=Strict, Path=/api/auth):
 *     only sent when the browser hits `/api/auth/*` (login, logout,
 *     refresh, me). Scoped path means the refresh token never leaks to
 *     arbitrary page renders, and SameSite=Strict blocks CSRF-style
 *     cross-site refresh attempts.
 *
 * The Secure flag is gated on `NODE_ENV === 'production'` so the dev
 * server over plain HTTP can still set cookies. Do not hardcode true/false
 * — that bit must stay environment-driven.
 *
 * Refresh token rotation (spec §8.3) is NOT implemented here. It lives in
 * the `/api/auth/refresh` handler (Task 4.1/4.2): each refresh call hits
 * Flask, which rotates the token server-side, and the handler calls
 * `setRefreshCookie` to overwrite the browser cookie with the new value.
 * This file only provides the write/read primitives.
 *
 * deleteCookie path matching: browsers match Set-Cookie path to deletion
 * path exactly. Calling `deleteCookie(event, 'tdc_refresh')` with no
 * options leaves the cookie alive because the default path `/` does not
 * match the Set-Cookie path `/api/auth`. `clearAuthCookies` always passes
 * the correct path per cookie — do NOT "simplify" it.
 *
 * Implementation note — h3 imports: we import `setCookie`, `deleteCookie`,
 * `getCookie` from 'h3' at module-eval time AND check for globalThis
 * overrides at call-time. Rationale matches auth-forward.ts:
 *   1. Nitro's prod bundle does not universally expose h3 helpers on
 *      globalThis, so a bare-identifier auto-import pattern fails.
 *   2. Vitest specs stub these names on globalThis before importing this
 *      module; the stubs win when present.
 *
 * Related:
 *   - server/middleware/auth-forward.ts (Task 2.7) — consumes
 *     TDC_ACCESS_COOKIE.
 *   - server/api/auth/*.post.ts (Task 4.x) — will use every helper here.
 *   - Spec §8.2 (cookie contract), §8.3 (rotation), CLAUDE.md
 *     § Project Constants.
 */
import type { H3Event } from 'h3'
import {
  setCookie as h3SetCookie,
  deleteCookie as h3DeleteCookie,
  getCookie as h3GetCookie,
} from 'h3'

export const TDC_ACCESS_COOKIE = 'tdc_access'
export const TDC_REFRESH_COOKIE = 'tdc_refresh'
export const TDC_ACCESS_TTL_SECONDS = 900 // 15 min
export const TDC_REFRESH_TTL_SECONDS = 604800 // 7 days
export const TDC_REFRESH_COOKIE_PATH = '/api/auth'

type SetCookieFn = (
  event: H3Event,
  name: string,
  value: string,
  options?: Record<string, unknown>,
) => void
type DeleteCookieFn = (event: H3Event, name: string, options?: Record<string, unknown>) => void
type GetCookieFn = (event: H3Event, name: string) => string | undefined

const resolveSetCookie = (): SetCookieFn => {
  const stubbed = (globalThis as unknown as { setCookie?: SetCookieFn }).setCookie
  return stubbed ?? (h3SetCookie as unknown as SetCookieFn)
}

const resolveDeleteCookie = (): DeleteCookieFn => {
  const stubbed = (globalThis as unknown as { deleteCookie?: DeleteCookieFn }).deleteCookie
  return stubbed ?? (h3DeleteCookie as unknown as DeleteCookieFn)
}

const resolveGetCookie = (): GetCookieFn => {
  const stubbed = (globalThis as unknown as { getCookie?: GetCookieFn }).getCookie
  return stubbed ?? (h3GetCookie as GetCookieFn)
}

const isProd = (): boolean => process.env.NODE_ENV === 'production'

/**
 * Write the short-lived access JWT as an HttpOnly cookie readable by every
 * server route (Path=/). SameSite=Lax permits top-level navigations (link
 * clicks) to carry the cookie, which is required so the initial SSR page
 * render is authenticated.
 */
export const setAccessCookie = (event: H3Event, token: string): void => {
  resolveSetCookie()(event, TDC_ACCESS_COOKIE, token, {
    httpOnly: true,
    secure: isProd(),
    sameSite: 'lax',
    path: '/',
    maxAge: TDC_ACCESS_TTL_SECONDS,
  })
}

/**
 * Write the long-lived refresh JWT as an HttpOnly cookie scoped to
 * /api/auth. SameSite=Strict + narrow path means the refresh token is only
 * ever transmitted to our auth endpoints.
 */
export const setRefreshCookie = (event: H3Event, token: string): void => {
  resolveSetCookie()(event, TDC_REFRESH_COOKIE, token, {
    httpOnly: true,
    secure: isProd(),
    sameSite: 'strict',
    path: TDC_REFRESH_COOKIE_PATH,
    maxAge: TDC_REFRESH_TTL_SECONDS,
  })
}

/**
 * Remove both auth cookies. The `path` passed to deleteCookie MUST match
 * the `path` used when the cookie was set, or the browser keeps the
 * cookie alive. Called from `/api/auth/logout` and on any auth failure
 * that should force re-login.
 */
export const clearAuthCookies = (event: H3Event): void => {
  const del = resolveDeleteCookie()
  del(event, TDC_ACCESS_COOKIE, { path: '/' })
  del(event, TDC_REFRESH_COOKIE, { path: TDC_REFRESH_COOKIE_PATH })
}

/**
 * Read the refresh token from the incoming request. Only meaningful inside
 * handlers mounted under `/api/auth/**` — other paths never receive it
 * because of the cookie's Path scope.
 */
export const getRefreshToken = (event: H3Event): string | undefined =>
  resolveGetCookie()(event, TDC_REFRESH_COOKIE)
