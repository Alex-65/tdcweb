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
