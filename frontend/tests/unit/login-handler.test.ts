import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { H3Event, EventHandler } from 'h3'

// Mocks for the Nitro auto-imports the handler relies on. The handler uses
// bare identifiers (defineEventHandler, readValidatedBody, flaskFetch,
// setAccessCookie, setRefreshCookie, createError) which Nitro normally
// resolves at build time. In the vitest environment we install typed
// globalThis stubs so the bare identifiers resolve to our spies.
//
// Pattern: typed extension of globalThis (Phase 3 Gap #1 / scan row 5
// codification). NEVER `as any`.
const readValidatedBodyMock = vi.fn()
const flaskFetchMock = vi.fn()
const setAccessCookieMock = vi.fn()
const setRefreshCookieMock = vi.fn()

type DefineEventHandlerFn = <T extends EventHandler>(handler: T) => T
type ReadValidatedBodyFn = typeof readValidatedBodyMock
type FlaskFetchFn = typeof flaskFetchMock
type SetCookieFn = typeof setAccessCookieMock
type CreateErrorFn = (opts: { statusCode: number; statusMessage?: string }) => Error

;(globalThis as unknown as { defineEventHandler: DefineEventHandlerFn }).defineEventHandler =
  ((h) => h) as DefineEventHandlerFn
;(globalThis as unknown as { readValidatedBody: ReadValidatedBodyFn }).readValidatedBody =
  readValidatedBodyMock
;(globalThis as unknown as { flaskFetch: FlaskFetchFn }).flaskFetch = flaskFetchMock
;(globalThis as unknown as { setAccessCookie: SetCookieFn }).setAccessCookie =
  setAccessCookieMock
;(globalThis as unknown as { setRefreshCookie: SetCookieFn }).setRefreshCookie =
  setRefreshCookieMock
;(globalThis as unknown as { createError: CreateErrorFn }).createError = (opts) =>
  Object.assign(new Error(opts.statusMessage), opts)

import loginHandler from '../../server/api/auth/login.post'

describe('POST /api/auth/login', () => {
  beforeEach(() => {
    readValidatedBodyMock.mockReset()
    flaskFetchMock.mockReset()
    setAccessCookieMock.mockReset()
    setRefreshCookieMock.mockReset()
  })

  it('sets both cookies and returns the user on success', async () => {
    readValidatedBodyMock.mockResolvedValue({ email: 'a@b.c', password: 'pw' })
    // Flask response envelope per `backend/app/utils/responses.py`:
    // `{ success: true, data: <payload> }`. BFF unwraps `.data`.
    flaskFetchMock.mockResolvedValue({
      success: true,
      data: {
        access: 'acc',
        refresh: 'ref',
        user: { id: 1, email: 'a@b.c', username: 'u', role: 'user' },
      },
    })
    const event = {} as H3Event

    const result = await loginHandler(event)

    expect(setAccessCookieMock).toHaveBeenCalledWith(event, 'acc')
    expect(setRefreshCookieMock).toHaveBeenCalledWith(event, 'ref')
    expect(result).toEqual({ user: { id: 1, email: 'a@b.c', username: 'u', role: 'user' } })
  })

  it('rejects invalid body when validation throws', async () => {
    readValidatedBodyMock.mockRejectedValue(new Error('validation failed'))
    const event = {} as H3Event

    await expect(loginHandler(event)).rejects.toThrow()
  })
})
