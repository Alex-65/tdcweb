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
 * Implementation note: `$fetch` and `useRuntimeConfig` are read off
 * `globalThis` rather than invoked as bare identifiers. In Nitro (prod)
 * both live on globalThis, so behavior is identical. In unit tests we
 * install the same names on globalThis, side-stepping the Nuxt
 * auto-import Vite transform that would otherwise rewrite the bare
 * identifiers into imports from `nuxt/app` (which require a running
 * Nuxt instance).
 */
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
