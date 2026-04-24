import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import type { H3Event } from 'h3'

// Mock the ofetch module so we can verify the fallback path taken when
// globalThis.$fetch is absent (TD-009 resolution — see flask-client.ts
// JSDoc). vi.mock is hoisted above the ESM imports below.
const ofetchMock = vi.fn()
vi.mock('ofetch', () => ({
  $fetch: (url: string, opts?: unknown) => ofetchMock(url, opts),
}))

// The util under test resolves `$fetch` and `useRuntimeConfig` via a
// stub-first + fallback-import pattern. For the default happy-path tests we
// install globalThis stubs that win over the ofetch import. The fallback
// case deletes the globalThis.$fetch stub and asserts the ofetch mock was
// called instead.
const fetchMock = vi.fn()
;(globalThis as unknown as { $fetch: typeof fetchMock }).$fetch = fetchMock
;(globalThis as unknown as { useRuntimeConfig: () => { flaskUrl: string } }).useRuntimeConfig = () => ({
  flaskUrl: 'http://flask.test',
})

import { flaskFetch } from '../../server/utils/flask-client'

type GlobalWithFetch = { $fetch?: typeof fetchMock }
type GlobalWithRC = { useRuntimeConfig?: () => { flaskUrl: string } }

describe('flaskFetch', () => {
  beforeEach(() => {
    fetchMock.mockReset()
    fetchMock.mockResolvedValue({ ok: true })
    ofetchMock.mockReset()
    ofetchMock.mockResolvedValue({ ok: true })
  })

  it('forwards flaskHeaders from event.context and applies the configured baseURL', async () => {
    const event = {
      context: { flaskHeaders: { Authorization: 'Bearer token123' } },
    } as unknown as H3Event

    await flaskFetch('/api/user/favorites', event)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/user/favorites',
      expect.objectContaining({
        baseURL: 'http://flask.test',
        headers: expect.objectContaining({ Authorization: 'Bearer token123' }),
      }),
    )
  })

  it('works when event.context.flaskHeaders is missing (unauthenticated call)', async () => {
    const event = { context: {} } as unknown as H3Event

    await flaskFetch('/api/locations', event)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/locations',
      expect.objectContaining({ baseURL: 'http://flask.test' }),
    )
  })

  it('caller-provided headers override flaskHeaders on key conflict', async () => {
    const event = {
      context: { flaskHeaders: { Authorization: 'Bearer OLD' } },
    } as unknown as H3Event

    await flaskFetch('/api/x', event, { headers: { Authorization: 'Bearer NEW' } })

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/x',
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer NEW' }),
      }),
    )
  })

  describe('fallback: ofetch is used when globalThis.$fetch is absent', () => {
    let savedFetch: typeof fetchMock | undefined

    beforeEach(() => {
      // Remove the globalThis stub so resolveFetch() falls through to the
      // module-eval ofetch import. Save and restore around the test to
      // keep the other suites' fetchMock-based assertions working.
      const g = globalThis as unknown as GlobalWithFetch
      savedFetch = g.$fetch
      delete g.$fetch
    })

    afterEach(() => {
      const g = globalThis as unknown as GlobalWithFetch
      g.$fetch = savedFetch
    })

    it('calls the mocked ofetch $fetch with the expected baseURL and headers', async () => {
      const event = {
        context: { flaskHeaders: { Authorization: 'Bearer from-cookie' } },
      } as unknown as H3Event

      await flaskFetch('/api/via-fallback', event)

      expect(fetchMock).not.toHaveBeenCalled()
      expect(ofetchMock).toHaveBeenCalledTimes(1)
      expect(ofetchMock).toHaveBeenCalledWith(
        '/api/via-fallback',
        expect.objectContaining({
          baseURL: 'http://flask.test',
          headers: expect.objectContaining({ Authorization: 'Bearer from-cookie' }),
        }),
      )
    })
  })

  describe('error: explicit failure when globalThis.useRuntimeConfig is absent', () => {
    let savedRC: (() => { flaskUrl: string }) | undefined

    beforeEach(() => {
      const g = globalThis as unknown as GlobalWithRC
      savedRC = g.useRuntimeConfig
      delete g.useRuntimeConfig
    })

    afterEach(() => {
      const g = globalThis as unknown as GlobalWithRC
      g.useRuntimeConfig = savedRC
    })

    it('throws a typed Error explaining the missing runtime config binding', () => {
      const event = { context: {} } as unknown as H3Event

      expect(() => flaskFetch('/api/anything', event)).toThrow(
        'flaskFetch: useRuntimeConfig is not available on globalThis; ' +
          'flaskFetch must be called from a Nitro server route where ' +
          'runtime config is bound',
      )
      expect(fetchMock).not.toHaveBeenCalled()
      expect(ofetchMock).not.toHaveBeenCalled()
    })
  })
})
