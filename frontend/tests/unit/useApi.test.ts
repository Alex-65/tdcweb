import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { FetchContext } from 'ofetch'

// Nuxt auto-imports `$fetch` from `#build/fetch` (not the global), so the
// mock replaces that module. `callMock` is the plain `$fetch(url)` call;
// each test sets its implementation.
const { createMock, callMock } = vi.hoisted(() => ({ createMock: vi.fn(), callMock: vi.fn() }))
vi.mock('#build/fetch', () => ({
  $fetch: Object.assign((url: string) => callMock(url), { create: createMock }),
}))

import { useApi, type RetryableFetchOptions } from '../../app/composables/useApi'

describe('useApi', () => {
  beforeEach(() => {
    createMock.mockReset()
    createMock.mockReturnValue(vi.fn())
    callMock.mockReset()
  })

  it('creates a $fetch instance with credentials: include', () => {
    useApi()
    expect(createMock).toHaveBeenCalledWith(
      expect.objectContaining({
        credentials: 'include',
      }),
    )
  })

  it('registers an onResponseError handler', () => {
    useApi()
    const opts = createMock.mock.calls[0]![0]
    expect(typeof opts.onResponseError).toBe('function')
  })

  it('onResponseError triggers refresh and retries once on 401', async () => {
    const refreshFetch = vi.fn().mockResolvedValue({})
    const retriedFetch = vi.fn().mockResolvedValue({ ok: true })
    callMock.mockImplementation(
      (url: string) => url === '/api/auth/refresh' ? refreshFetch(url) : retriedFetch(url),
    )

    useApi()
    const opts = createMock.mock.calls[0]![0]
    const options: RetryableFetchOptions = {}
    const context = {
      response: { status: 401 },
      request: '/api/foo',
      options,
    } as unknown as FetchContext & { response: { status: number } }
    await opts.onResponseError(context)

    expect(refreshFetch).toHaveBeenCalledWith('/api/auth/refresh')
    expect(options._retry).toBe(true)
  })

  it('onResponseError does NOT retry when already retried', async () => {
    const refreshFetch = vi.fn()
    callMock.mockImplementation(() => refreshFetch())

    useApi()
    const opts = createMock.mock.calls[0]![0]
    const options: RetryableFetchOptions = { _retry: true }
    const context = {
      response: { status: 401 },
      request: '/api/foo',
      options,
    } as unknown as FetchContext & { response: { status: number } }
    await opts.onResponseError(context)
    expect(refreshFetch).not.toHaveBeenCalled()
  })
})
