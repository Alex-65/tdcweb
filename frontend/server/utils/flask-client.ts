/**
 * flaskFetch — server-side wrapper around $fetch for Nitro handlers.
 *
 * Threads the H3Event through so the auth-forward middleware's
 * event.context.flaskHeaders (populated from the `tdc_access` HttpOnly
 * cookie, Task 2.7) is attached to every outbound call. Caller-provided
 * headers win on key conflicts — use sparingly, mainly for Content-Type
 * overrides, not to hand-roll auth.
 *
 * Usage:
 *   export default defineEventHandler((event) =>
 *     flaskFetch<User>('/api/auth/me', event),
 *   )
 *
 * baseURL is read per-call from runtimeConfig so env changes (dev vs prod)
 * don't require a server restart beyond the usual Nitro reload.
 *
 * Implementation note — stub-first + fallback-import pattern:
 * Each dependency (`$fetch`, `useRuntimeConfig`) is resolved at call time
 * through a helper that checks `globalThis` first, then falls back to a
 * module-eval-time import (for `$fetch`) or throws an explicit error (for
 * `useRuntimeConfig`, which has no clean module fallback). Vitest specs
 * install globalThis stubs before importing this module, so the stubs win
 * in tests. In prod, Nitro's bundle does not universally expose these on
 * globalThis (Task 2.7 review confirmed h3 helpers live as regular module
 * bindings in the dev build — the same applies to $fetch), so the imported
 * ofetch `$fetch` provides a robust fallback. This mirrors the pattern in
 * server/middleware/auth-forward.ts and server/utils/cookies.ts.
 */
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
