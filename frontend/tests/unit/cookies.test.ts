import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import type { H3Event } from 'h3'

// cookies.ts calls setCookie / deleteCookie / getCookie which are imported
// from 'h3'. Mirroring the pattern in auth-forward.test.ts, we install
// globalThis stubs BEFORE importing the module; cookies.ts prefers the
// stubs over the h3 module bindings when present. This avoids the ESM-
// hoisting issue where vi.mock would still leave bare-identifier imports
// unresolved during test-file transform.
const setCookieMock = vi.fn<(event: H3Event, name: string, value: string, opts?: unknown) => void>()
const deleteCookieMock = vi.fn<(event: H3Event, name: string, opts?: unknown) => void>()
const getCookieMock = vi.fn<(event: H3Event, name: string) => string | undefined>()

;(globalThis as unknown as { setCookie: typeof setCookieMock }).setCookie = setCookieMock
;(globalThis as unknown as { deleteCookie: typeof deleteCookieMock }).deleteCookie = deleteCookieMock
;(globalThis as unknown as { getCookie: typeof getCookieMock }).getCookie = getCookieMock

import {
  TDC_ACCESS_COOKIE,
  TDC_REFRESH_COOKIE,
  TDC_ACCESS_TTL_SECONDS,
  TDC_REFRESH_TTL_SECONDS,
  TDC_REFRESH_COOKIE_PATH,
  setAccessCookie,
  setRefreshCookie,
  clearAuthCookies,
  getRefreshToken,
} from '../../server/utils/cookies'

describe('cookies.ts — exported constants', () => {
  it('exposes the canonical cookie names and lifetimes expected by spec §8.2', () => {
    expect(TDC_ACCESS_COOKIE).toBe('tdc_access')
    expect(TDC_REFRESH_COOKIE).toBe('tdc_refresh')
    expect(TDC_ACCESS_TTL_SECONDS).toBe(900)
    expect(TDC_REFRESH_TTL_SECONDS).toBe(604800)
    expect(TDC_REFRESH_COOKIE_PATH).toBe('/api/auth')
  })
})

describe('setAccessCookie', () => {
  const originalNodeEnv = process.env.NODE_ENV

  beforeEach(() => {
    setCookieMock.mockReset()
  })

  afterEach(() => {
    process.env.NODE_ENV = originalNodeEnv
  })

  it('calls setCookie with name tdc_access, the token, and the baseline options', () => {
    process.env.NODE_ENV = 'development'
    const event = {} as H3Event

    setAccessCookie(event, 'jwt-access')

    expect(setCookieMock).toHaveBeenCalledTimes(1)
    const [eventArg, nameArg, valueArg, optsArg] = setCookieMock.mock.calls[0] as [
      H3Event,
      string,
      string,
      Record<string, unknown>,
    ]
    expect(eventArg).toBe(event)
    expect(nameArg).toBe('tdc_access')
    expect(valueArg).toBe('jwt-access')
    expect(optsArg).toMatchObject({
      httpOnly: true,
      sameSite: 'lax',
      path: '/',
      maxAge: 900,
    })
  })

  it('sets secure=true when NODE_ENV=production', () => {
    process.env.NODE_ENV = 'production'
    const event = {} as H3Event

    setAccessCookie(event, 'jwt-access')

    const optsArg = setCookieMock.mock.calls[0][3] as Record<string, unknown>
    expect(optsArg.secure).toBe(true)
  })

  it('sets secure=false when NODE_ENV is not production', () => {
    process.env.NODE_ENV = 'development'
    const event = {} as H3Event

    setAccessCookie(event, 'jwt-access')

    const optsArg = setCookieMock.mock.calls[0][3] as Record<string, unknown>
    expect(optsArg.secure).toBe(false)
  })
})

describe('setRefreshCookie', () => {
  const originalNodeEnv = process.env.NODE_ENV

  beforeEach(() => {
    setCookieMock.mockReset()
  })

  afterEach(() => {
    process.env.NODE_ENV = originalNodeEnv
  })

  it('calls setCookie with name tdc_refresh, the token, and strict/scoped options', () => {
    process.env.NODE_ENV = 'development'
    const event = {} as H3Event

    setRefreshCookie(event, 'jwt-refresh')

    expect(setCookieMock).toHaveBeenCalledTimes(1)
    const [eventArg, nameArg, valueArg, optsArg] = setCookieMock.mock.calls[0] as [
      H3Event,
      string,
      string,
      Record<string, unknown>,
    ]
    expect(eventArg).toBe(event)
    expect(nameArg).toBe('tdc_refresh')
    expect(valueArg).toBe('jwt-refresh')
    expect(optsArg).toMatchObject({
      httpOnly: true,
      sameSite: 'strict',
      path: '/api/auth',
      maxAge: 604800,
    })
  })

  it('sets secure=true in production', () => {
    process.env.NODE_ENV = 'production'
    const event = {} as H3Event

    setRefreshCookie(event, 'jwt-refresh')

    const optsArg = setCookieMock.mock.calls[0][3] as Record<string, unknown>
    expect(optsArg.secure).toBe(true)
  })
})

describe('clearAuthCookies', () => {
  beforeEach(() => {
    deleteCookieMock.mockReset()
  })

  it('deletes both cookies with matching paths — access at / and refresh at /api/auth', () => {
    // Critical: browsers require the deleteCookie path to match the Set-Cookie
    // path or the deletion silently no-ops. A missing path on the refresh
    // cookie would leave the refresh token alive client-side after logout.
    const event = {} as H3Event

    clearAuthCookies(event)

    expect(deleteCookieMock).toHaveBeenCalledTimes(2)

    const calls = deleteCookieMock.mock.calls as Array<[H3Event, string, Record<string, unknown>]>
    const byName = new Map(calls.map((c) => [c[1], c[2]]))

    expect(byName.get('tdc_access')).toMatchObject({ path: '/' })
    expect(byName.get('tdc_refresh')).toMatchObject({ path: '/api/auth' })
  })
})

describe('getRefreshToken', () => {
  beforeEach(() => {
    getCookieMock.mockReset()
  })

  it('delegates to getCookie(event, "tdc_refresh") and returns its value', () => {
    getCookieMock.mockImplementation((_event, name) =>
      name === 'tdc_refresh' ? 'refresh-value' : undefined,
    )
    const event = {} as H3Event

    const result = getRefreshToken(event)

    expect(getCookieMock).toHaveBeenCalledWith(event, 'tdc_refresh')
    expect(result).toBe('refresh-value')
  })

  it('returns undefined when no refresh cookie is present', () => {
    getCookieMock.mockReturnValue(undefined)
    const event = {} as H3Event

    expect(getRefreshToken(event)).toBeUndefined()
  })
})
