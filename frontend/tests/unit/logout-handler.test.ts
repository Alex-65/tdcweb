import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { H3Event, EventHandler } from 'h3'

// TD-016 closure (post-Phase-7 sweep). Mirrors `login-handler.test.ts`:
// typed globalThis stubs install BEFORE the handler import so the bare
// auto-import identifiers in the handler resolve to our spies. NEVER
// `as any` (Phase 3 Gap #1 codification).
const flaskFetchMock = vi.fn()
const clearAuthCookiesMock = vi.fn()

type DefineEventHandlerFn = <T extends EventHandler>(handler: T) => T
type FlaskFetchFn = typeof flaskFetchMock
type ClearAuthCookiesFn = typeof clearAuthCookiesMock

;(globalThis as unknown as { defineEventHandler: DefineEventHandlerFn }).defineEventHandler =
  ((h) => h) as DefineEventHandlerFn
;(globalThis as unknown as { flaskFetch: FlaskFetchFn }).flaskFetch = flaskFetchMock
;(globalThis as unknown as { clearAuthCookies: ClearAuthCookiesFn }).clearAuthCookies =
  clearAuthCookiesMock

import logoutHandler from '../../server/api/auth/logout.post'

describe('POST /api/auth/logout', () => {
  beforeEach(() => {
    flaskFetchMock.mockReset()
    clearAuthCookiesMock.mockReset()
  })

  it('forwards to Flask and clears cookies on success', async () => {
    flaskFetchMock.mockResolvedValue({ success: true, data: null })
    const event = {} as H3Event

    const result = await logoutHandler(event)

    expect(flaskFetchMock).toHaveBeenCalledWith('/api/auth/logout', event, {
      method: 'POST',
    })
    expect(clearAuthCookiesMock).toHaveBeenCalledWith(event)
    expect(result).toEqual({ success: true })
  })

  it('still clears cookies and returns success when Flask call throws', async () => {
    // The handler intentionally swallows Flask failures so the local UI
    // logs out even if the remote Flask is unreachable. The BFF cookie
    // clear is the source of truth for the browser session.
    flaskFetchMock.mockRejectedValue(new Error('connection refused'))
    const event = {} as H3Event

    const result = await logoutHandler(event)

    expect(flaskFetchMock).toHaveBeenCalledWith('/api/auth/logout', event, {
      method: 'POST',
    })
    expect(clearAuthCookiesMock).toHaveBeenCalledWith(event)
    expect(result).toEqual({ success: true })
  })

  it('clears cookies even if Flask returns 401 (already logged out upstream)', async () => {
    // ofetch surfaces non-2xx as a thrown FetchError. The handler must
    // not propagate it -- a 401 from Flask just means the session was
    // already invalid; the client still wants its local cookies cleared.
    flaskFetchMock.mockRejectedValue(
      Object.assign(new Error('UNAUTHORIZED'), { statusCode: 401 }),
    )
    const event = {} as H3Event

    const result = await logoutHandler(event)

    expect(clearAuthCookiesMock).toHaveBeenCalledWith(event)
    expect(result).toEqual({ success: true })
  })
})
