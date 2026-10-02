import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { H3Event, EventHandler } from 'h3'

// TD-016 closure (post-Phase-7 sweep). Mirrors `login-handler.test.ts`
// pattern: typed globalThis stubs install BEFORE the handler import.
// NEVER `as any` (Phase 3 Gap #1 codification).
const flaskFetchMock = vi.fn()
const setAccessCookieMock = vi.fn()
const setRefreshCookieMock = vi.fn()
const getRefreshTokenMock = vi.fn()

type DefineEventHandlerFn = <T extends EventHandler>(handler: T) => T
type FlaskFetchFn = typeof flaskFetchMock
type SetCookieFn = typeof setAccessCookieMock
type GetRefreshTokenFn = typeof getRefreshTokenMock
type CreateErrorFn = (opts: { statusCode: number; statusMessage?: string }) => Error

;(globalThis as unknown as { defineEventHandler: DefineEventHandlerFn }).defineEventHandler =
  ((h) => h) as DefineEventHandlerFn
;(globalThis as unknown as { flaskFetch: FlaskFetchFn }).flaskFetch = flaskFetchMock
;(globalThis as unknown as { setAccessCookie: SetCookieFn }).setAccessCookie =
  setAccessCookieMock
;(globalThis as unknown as { setRefreshCookie: SetCookieFn }).setRefreshCookie =
  setRefreshCookieMock
;(globalThis as unknown as { getRefreshToken: GetRefreshTokenFn }).getRefreshToken =
  getRefreshTokenMock
;(globalThis as unknown as { createError: CreateErrorFn }).createError = (opts) =>
  Object.assign(new Error(opts.statusMessage), opts)

import refreshHandler from '../../server/api/auth/refresh.post'

describe('POST /api/auth/refresh', () => {
  beforeEach(() => {
    flaskFetchMock.mockReset()
    setAccessCookieMock.mockReset()
    setRefreshCookieMock.mockReset()
    getRefreshTokenMock.mockReset()
  })

  it('rotates both cookies on successful refresh', async () => {
    getRefreshTokenMock.mockReturnValue('old-refresh-jti')
    // Flask envelope per `backend/app/utils/responses.py`. The refresh
    // endpoint issues a NEW access token AND a NEW refresh token (jti
    // rotation; verified by `backend/tests/test_auth.py` cases for
    // `test_refresh_with_valid_refresh_returns_new_access_and_new_refresh`).
    flaskFetchMock.mockResolvedValue({
      success: true,
      data: { access: 'new-acc', refresh: 'new-ref' },
    })
    const event = {} as H3Event

    const result = await refreshHandler(event)

    expect(getRefreshTokenMock).toHaveBeenCalledWith(event)
    expect(flaskFetchMock).toHaveBeenCalledWith('/api/auth/refresh', event, {
      method: 'POST',
      headers: { Authorization: 'Bearer old-refresh-jti' },
    })
    expect(setAccessCookieMock).toHaveBeenCalledWith(event, 'new-acc')
    expect(setRefreshCookieMock).toHaveBeenCalledWith(event, 'new-ref')
    expect(result).toEqual({ success: true })
  })

  it('rejects with 401 when no refresh cookie is present', async () => {
    getRefreshTokenMock.mockReturnValue(undefined)
    const event = {} as H3Event

    await expect(refreshHandler(event)).rejects.toThrow('No refresh token')
    expect(flaskFetchMock).not.toHaveBeenCalled()
    expect(setAccessCookieMock).not.toHaveBeenCalled()
    expect(setRefreshCookieMock).not.toHaveBeenCalled()
  })

  it('does not rotate cookies if Flask rejects the refresh', async () => {
    // If Flask returns 401 (e.g. refresh token already used or expired),
    // ofetch throws a FetchError. The handler propagates it (no swallow),
    // so neither cookie should get rotated. The client must call
    // /api/auth/login fresh.
    getRefreshTokenMock.mockReturnValue('expired-refresh')
    flaskFetchMock.mockRejectedValue(
      Object.assign(new Error('UNAUTHORIZED'), { statusCode: 401 }),
    )
    const event = {} as H3Event

    await expect(refreshHandler(event)).rejects.toThrow()
    expect(setAccessCookieMock).not.toHaveBeenCalled()
    expect(setRefreshCookieMock).not.toHaveBeenCalled()
  })
})
