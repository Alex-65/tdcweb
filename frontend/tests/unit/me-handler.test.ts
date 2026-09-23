import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { H3Event, EventHandler } from 'h3'

// TD-016 closure (post-Phase-7 sweep). Mirrors `login-handler.test.ts`
// pattern: typed globalThis stubs install BEFORE the handler import.
// NEVER `as any` (Phase 3 Gap #1 codification).
const flaskFetchMock = vi.fn()

type DefineEventHandlerFn = <T extends EventHandler>(handler: T) => T
type FlaskFetchFn = typeof flaskFetchMock
type CreateErrorFn = (opts: { statusCode: number; statusMessage?: string }) => Error

;(globalThis as unknown as { defineEventHandler: DefineEventHandlerFn }).defineEventHandler =
  ((h) => h) as DefineEventHandlerFn
;(globalThis as unknown as { flaskFetch: FlaskFetchFn }).flaskFetch = flaskFetchMock
;(globalThis as unknown as { createError: CreateErrorFn }).createError = (opts) =>
  Object.assign(new Error(opts.statusMessage), opts)

import meHandler from '../../server/api/auth/me.get'

// Helper: build an H3Event with optional flaskHeaders. The handler's
// gate is `event.context.flaskHeaders !== undefined`, populated upstream
// by the auth-forward server middleware from the `tdc_access` cookie.
const eventWith = (flaskHeaders?: Record<string, string>): H3Event =>
  ({ context: flaskHeaders ? { flaskHeaders } : {} }) as unknown as H3Event

describe('GET /api/auth/me', () => {
  beforeEach(() => {
    flaskFetchMock.mockReset()
  })

  it('returns the unwrapped user when flaskHeaders are present', async () => {
    // Flask envelope per `backend/app/routes/api/auth.py:122`:
    // `success(g.current_user.to_dict())` -> `data` IS the User directly,
    // NOT nested under `data.user`. The handler unwraps to `{ user }`
    // for the conventional client shape.
    const user = {
      id: 7,
      email: 'a@b.c',
      username: 'au',
      role: 'user' as const,
    }
    flaskFetchMock.mockResolvedValue({ success: true, data: user })
    const event = eventWith({ Authorization: 'Bearer abc' })

    const result = await meHandler(event)

    expect(flaskFetchMock).toHaveBeenCalledWith('/api/auth/me', event)
    expect(result).toEqual({ user })
  })

  it('rejects with 401 when flaskHeaders are missing (guest request)', async () => {
    // The auth-forward middleware leaves `flaskHeaders` undefined when no
    // `tdc_access` cookie is present. Without that, Flask would reject
    // with 401 anyway, but the BFF short-circuits to save the round-trip
    // and to surface a uniform "Not authenticated" message.
    const event = eventWith(undefined)

    await expect(meHandler(event)).rejects.toThrow('Not authenticated')
    expect(flaskFetchMock).not.toHaveBeenCalled()
  })

  it('propagates Flask 401 if flaskHeaders are present but the token is invalid', async () => {
    // If the access cookie is structurally valid (non-empty) but Flask
    // rejects (expired, wrong signature, revoked), ofetch throws a
    // FetchError. The handler does not catch -- the client useAuth
    // composable will see the error, clear the store, and treat the
    // user as a guest. No silent envelope unwrap of error responses.
    flaskFetchMock.mockRejectedValue(
      Object.assign(new Error('UNAUTHORIZED'), { statusCode: 401 }),
    )
    const event = eventWith({ Authorization: 'Bearer stale' })

    await expect(meHandler(event)).rejects.toThrow()
  })
})
