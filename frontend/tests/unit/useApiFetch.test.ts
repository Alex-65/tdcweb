import { describe, it, expect } from 'vitest'

// Test the pure helpers extracted from `useApiFetch`.
// Why pure helpers instead of mocking `useFetch`: the @nuxt/test-utils
// transformer rewrites bare `useFetch` references inside `app/composables/*.ts`
// to a direct import path that the `nuxt` package's `exports` field does not
// expose, so `vi.mock('nuxt/dist/app/composables/fetch.js', ...)` fails with
// "Missing specifier". Mocking via `#app` / `nuxt/app` does not intercept the
// rewritten reference. Rather than fight the framework with a brittle, version-
// coupled hack, the composable delegates both non-trivial decisions
// (envelope unwrap + baseURL resolution) to pure functions tested here.
import { unwrapEnvelope, resolveApiBaseURL } from '../../app/composables/useApiFetch'

describe('unwrapEnvelope (useApiFetch transform)', () => {
  it('unwraps `{ success: true, data: T }` to T', () => {
    const sample = { success: true as const, data: [{ id: 1 }, { id: 2 }] }
    expect(unwrapEnvelope<Array<{ id: number }>>(sample)).toEqual([
      { id: 1 },
      { id: 2 },
    ])
  })

  it('preserves the data identity (no copy)', () => {
    const inner = [{ id: 42 }]
    const sample = { success: true as const, data: inner }
    expect(unwrapEnvelope<typeof inner>(sample)).toBe(inner)
  })

  it('passes a non-enveloped object through (no `data` key)', () => {
    const raw = [{ id: 99 }]
    expect(unwrapEnvelope<typeof raw>(raw)).toBe(raw)
  })

  it('passes null through defensively', () => {
    expect(unwrapEnvelope<null>(null)).toBeNull()
  })

  it('passes primitives through defensively', () => {
    expect(unwrapEnvelope<string>('plain string')).toBe('plain string')
    expect(unwrapEnvelope<number>(42)).toBe(42)
  })

  it('unwraps even when meta is present', () => {
    const sample = {
      success: true as const,
      data: { id: 1 },
      meta: { page: 1, per_page: 20, total: 1 },
    }
    expect(unwrapEnvelope<{ id: number }>(sample)).toEqual({ id: 1 })
  })

  // Strictness coverage: an error envelope `{success:false, error:...}`
  // should NOT be unwrapped (no `data` key, and `success !== true`).
  // Compliant Flask returns these with non-2xx status so useFetch surfaces
  // them as FetchError before reaching this transform; this is defense in
  // depth for the case where the backend ever returns a 200 + error body.
  it('passes an error envelope through unchanged (success:false)', () => {
    const sample = { success: false as const, error: 'bad request' }
    expect(unwrapEnvelope<typeof sample>(sample)).toBe(sample)
  })

  // Edge case: an object with `data` but `success !== true` is NOT a
  // canonical envelope and should pass through.
  it('does not unwrap when success is missing or not literally true', () => {
    const noSuccess = { data: [1, 2, 3] }
    expect(unwrapEnvelope<typeof noSuccess>(noSuccess)).toBe(noSuccess)

    const truthyButNotTrue = { success: 1 as unknown as true, data: [1] }
    expect(unwrapEnvelope<typeof truthyButNotTrue>(truthyButNotTrue)).toBe(truthyButNotTrue)
  })

  // Arrays can have a `data` property in JS (it's just an indexed slot or
  // a custom field), so the prior loose `'data' in response` check would
  // have falsely unwrapped them. The strict guard rejects arrays.
  it('passes arrays through (never confused with envelopes)', () => {
    const arr = [{ id: 1 }, { id: 2 }]
    expect(unwrapEnvelope<typeof arr>(arr)).toBe(arr)
  })
})

// SSR-vs-client baseURL contract. This was the source of two debug cycles
// in Phase 4: Vite's devProxy is dev-only and does NOT intercept Nitro's
// internal SSR $fetch, so SSR requests with a relative URL fall through to
// the page renderer and Vue Router emits "Page not found: /api/...". The
// helper must (a) return undefined on the client (keep relative for proxy)
// and (b) return the configured flaskUrl on SSR, throwing if the env is
// missing so the misconfig surfaces loudly at first request.
describe('resolveApiBaseURL (useApiFetch SSR contract)', () => {
  it('returns undefined on the client regardless of flaskUrl', () => {
    expect(resolveApiBaseURL(false, 'http://localhost:9502')).toBeUndefined()
    expect(resolveApiBaseURL(false, undefined)).toBeUndefined()
    expect(resolveApiBaseURL(false, '')).toBeUndefined()
  })

  it('returns the configured flaskUrl on SSR', () => {
    expect(resolveApiBaseURL(true, 'http://localhost:9502')).toBe(
      'http://localhost:9502',
    )
    expect(resolveApiBaseURL(true, 'http://flask.internal:9500')).toBe(
      'http://flask.internal:9500',
    )
  })

  it('throws on SSR if flaskUrl is missing (defensive misconfig guard)', () => {
    expect(() => resolveApiBaseURL(true, undefined)).toThrow(/flaskUrl is empty/)
    expect(() => resolveApiBaseURL(true, '')).toThrow(/flaskUrl is empty/)
  })
})
