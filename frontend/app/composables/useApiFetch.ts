import type { FetchError } from 'ofetch'
import type { UseFetchOptions } from 'nuxt/app'
import type { ApiResponse } from '~/types/api'

// Mirror of Nuxt's internal `KeysOf<T>` (not re-exported from `nuxt/app`,
// see node_modules/nuxt/dist/app/composables/asyncData.d.ts). Local copy
// keeps `UseApiFetchOptions` aligned with `useFetch`'s `PickKeys` slot.
type KeysOf<T> = Array<T extends T ? (keyof T extends string ? keyof T : never) : never>

/**
 * `useFetch` wrapper for Flask endpoints that return the canonical envelope
 * `{ success: true, data: <T> }` (per `backend/app/utils/responses.py`).
 *
 * Auto-unwraps `.data` so the consuming component receives `T` directly --
 * mirrors the BFF auth handlers (`server/api/auth/*`) which also unwrap.
 *
 * Use this for any GET /api/* call from a Vue page. Direct `useFetch` is OK
 * only for routes that intentionally bypass the envelope (e.g. third-party
 * APIs, or endpoints that pre-date the envelope convention -- there should
 * be none in TDC).
 *
 * Example:
 *   const { data: locations, error } = await useApiFetch<Location[]>('/api/locations')
 *   // locations.value is Location[] | null (NOT { success, data })
 */
// Narrowed options accepted by `useApiFetch`: same as Nuxt's `UseFetchOptions`
// but with `Method` pinned to `'get'` (these are read-only Flask GETs) and
// `DefaultT = T` so callers can supply `default: () => []` and `data.value`
// is `T` (never null). The two narrowings line up with the underlying
// `useFetch` overload we delegate to.
export type UseApiFetchOptions<T> = UseFetchOptions<
  ApiResponse<T>,
  T,
  KeysOf<T>,
  T,
  string,
  'get'
>

/**
 * Pure envelope-unwrap transform. Extracted so it can be unit-tested
 * without booting Nuxt's runtime (vitest cannot easily mock the auto-imported
 * `useFetch` that this composable delegates to). The composable below wires
 * it into `useFetch`'s `transform` slot.
 *
 * - Enveloped success (`{ success: true, data: T }`) -> returns `T`.
 * - Anything else (null, primitive, array, error envelope `{success:false}`)
 *   -> passes through unchanged so callers' existing error semantics still
 *   work. Error envelopes from Flask travel as non-2xx HTTP and are surfaced
 *   by `useFetch` as a `FetchError` (see `backend/app/utils/responses.py`
 *   `error()`), so they should never reach this transform; the strict check
 *   here is defense in depth for the case where Flask returns 200 with a
 *   non-success body (a TECH_DEBT trigger if observed).
 */
export function unwrapEnvelope<T>(response: ApiResponse<T> | unknown): T {
  if (
    response !== null &&
    typeof response === 'object' &&
    !Array.isArray(response) &&
    'success' in response &&
    (response as { success: unknown }).success === true &&
    'data' in response
  ) {
    return (response as ApiResponse<T>).data
  }
  return response as T
}

/**
 * Pure helper for picking the right `baseURL` for `useApiFetch`. Extracted
 * for the same reason as `unwrapEnvelope`: testable without booting the
 * Nuxt runtime, and locks the SSR-vs-client contract that bit two debug
 * cycles in Phase 4 (Vite's devProxy is dev-server-only and does NOT
 * intercept Nitro's internal $fetch during SSR; without an explicit
 * baseURL the SSR fetch falls through to the Vue page renderer and Vue
 * Router emits "Page not found: /api/locations" via router.afterEach).
 *
 * Contract:
 * - SSR (server=true) MUST resolve to a non-empty `flaskUrl` -- the SSR
 *   fetch is a real HTTP call straight to Flask (canonical BFF pattern;
 *   mirrors `server/utils/flask-client.ts`). Missing flaskUrl is a fatal
 *   misconfig and we throw so prod surfaces it loudly at first request
 *   instead of silently 404-ing every page.
 * - Client (server=false) returns `undefined` so the relative URL flows
 *   through Vite's devProxy (dev) or Apache (prod) to Flask.
 */
export function resolveApiBaseURL(
  isServer: boolean,
  flaskUrl: string | undefined,
): string | undefined {
  if (!isServer) return undefined
  if (!flaskUrl) {
    throw new Error(
      'useApiFetch: runtimeConfig.flaskUrl is empty -- set NUXT_FLASK_URL ' +
        'in the SSR environment so server-side fetches reach the Flask backend ' +
        'directly instead of falling through to the Nuxt page renderer.',
    )
  }
  return flaskUrl
}

export function useApiFetch<T>(
  url: string,
  options: UseApiFetchOptions<T> = {} as UseApiFetchOptions<T>,
) {
  // SSR-vs-client baseURL split (see `resolveApiBaseURL` for the contract
  // and the why). The pure helper is unit-tested separately so the
  // SSR/CSR distinction stays locked even if this delegating wrapper
  // changes shape later.
  const baseURL = resolveApiBaseURL(import.meta.server, useRuntimeConfig().flaskUrl)

  return useFetch<ApiResponse<T>, FetchError, string, 'get', ApiResponse<T>, T>(
    url,
    {
      baseURL,
      ...options,
      // Unwrap the envelope: if response is `{ success: true, data: T }`,
      // expose `data.value` as `T`. See `unwrapEnvelope` for the pure
      // implementation (separated for testability).
      transform: unwrapEnvelope<T>,
    },
  )
}
