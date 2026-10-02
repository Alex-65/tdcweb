import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { H3Event } from 'h3'

// auth-forward.ts uses two Nuxt/Nitro auto-imports: defineEventHandler and
// getCookie. We install mockable globals before importing the module, mirroring
// the pattern we use in flask-client.test.ts so the Vite transform does not try
// to resolve these to `nuxt/app`.
const getCookieMock = vi.fn<(event: H3Event, name: string) => string | undefined>()
;(globalThis as unknown as { getCookie: typeof getCookieMock }).getCookie = getCookieMock
;(globalThis as unknown as { defineEventHandler: <T>(h: T) => T }).defineEventHandler = (h) => h

import authForward from '../../server/middleware/auth-forward'

describe('auth-forward middleware', () => {
  beforeEach(() => {
    getCookieMock.mockReset()
  })

  it('sets event.context.flaskHeaders = { Authorization: "Bearer <jwt>" } when tdc_access cookie exists', async () => {
    getCookieMock.mockImplementation((_event, name) =>
      name === 'tdc_access' ? 'jwt-access-token' : undefined,
    )
    const event = { context: {} } as unknown as H3Event

    await (authForward as (event: H3Event) => Promise<void>)(event)

    expect(getCookieMock).toHaveBeenCalledWith(event, 'tdc_access')
    expect(event.context.flaskHeaders).toEqual({ Authorization: 'Bearer jwt-access-token' })
  })

  it('leaves event.context.flaskHeaders undefined when the cookie is missing', async () => {
    getCookieMock.mockReturnValue(undefined)
    const event = { context: {} } as unknown as H3Event

    await (authForward as (event: H3Event) => Promise<void>)(event)

    expect(event.context.flaskHeaders).toBeUndefined()
  })

  it('uses EXACTLY the key name "Authorization" (capital A) and the "Bearer " prefix (capital B, single space)', async () => {
    // Contract with Task 2.6 flaskFetch + Flask @jwt_required: the key must be
    // "Authorization" exactly, value must be "Bearer <token>" with that exact spacing.
    // Any lowercase / alternative name (X-Auth-Token, authorization) would silently
    // break auth end-to-end and flask-client.test.ts does not catch that.
    getCookieMock.mockImplementation((_event, name) =>
      name === 'tdc_access' ? 'abc' : undefined,
    )
    const event = { context: {} } as unknown as H3Event

    await (authForward as (event: H3Event) => Promise<void>)(event)

    const headers = event.context.flaskHeaders as Record<string, string> | undefined
    expect(headers).toBeDefined()
    expect(Object.keys(headers!)).toEqual(['Authorization'])
    expect(headers!.Authorization).toBe('Bearer abc')
    expect(headers!.Authorization.startsWith('Bearer ')).toBe(true)
  })
})
