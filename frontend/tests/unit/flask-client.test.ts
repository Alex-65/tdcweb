import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { H3Event } from 'h3'

// The util under test reaches for two globals that Nuxt normally auto-imports
// in a server-route context: $fetch and useRuntimeConfig. Tests run outside
// that context, so we install globals before importing the module.
const fetchMock = vi.fn()
;(globalThis as unknown as { $fetch: typeof fetchMock }).$fetch = fetchMock
;(globalThis as unknown as { useRuntimeConfig: () => { flaskUrl: string } }).useRuntimeConfig = () => ({
  flaskUrl: 'http://flask.test',
})

import { flaskFetch } from '../../server/utils/flask-client'

describe('flaskFetch', () => {
  beforeEach(() => {
    fetchMock.mockReset()
    fetchMock.mockResolvedValue({ ok: true })
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
})
