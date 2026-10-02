import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { H3Event, EventHandler } from 'h3'
import type { User } from '../../app/types/user'
import type { ApiResponse } from '../../app/types/api'

// Typed globalThis stubs (Phase 3 Gap #1 codification). The handler uses
// bare auto-import identifiers (readValidatedBody, flaskFetch, createError,
// useStorage) which Nitro provides at build time; in vitest we install
// typed stubs before importing the handler so the bare references resolve.
// NEVER `as any` -- mirror the pattern in login-handler.test.ts.

const readValidatedBodyMock = vi.fn()
const flaskFetchMock = vi.fn()
const useStorageMock = vi.fn()
const storageGetKeysMock = vi.fn<(base?: string) => Promise<string[]>>()
const storageRemoveItemMock = vi.fn<(key: string) => Promise<void>>()

type DefineEventHandlerFn = <T extends EventHandler>(handler: T) => T
type ReadValidatedBodyFn = typeof readValidatedBodyMock
type FlaskFetchFn = <T = unknown>(url: string, event: H3Event) => Promise<T>
type CreateErrorFn = (opts: { statusCode: number; statusMessage?: string }) => Error
type UseStorageFn = typeof useStorageMock

;(globalThis as unknown as { defineEventHandler: DefineEventHandlerFn }).defineEventHandler =
  ((h) => h) as DefineEventHandlerFn
;(globalThis as unknown as { readValidatedBody: ReadValidatedBodyFn }).readValidatedBody =
  readValidatedBodyMock
;(globalThis as unknown as { flaskFetch: FlaskFetchFn }).flaskFetch =
  flaskFetchMock as unknown as FlaskFetchFn
;(globalThis as unknown as { createError: CreateErrorFn }).createError = (opts) =>
  Object.assign(new Error(opts.statusMessage), opts)
;(globalThis as unknown as { useStorage: UseStorageFn }).useStorage = useStorageMock

// Default storage stub: every useStorage('cache:nitro:routes') call returns
// the same shape with our two spies.
useStorageMock.mockReturnValue({
  getKeys: storageGetKeysMock,
  removeItem: storageRemoveItemMock,
})

import revalidateHandler from '../../server/api/revalidate.post'

const adminMe = (): ApiResponse<User> => ({
  success: true,
  data: {
    id: 1,
    email: 'admin@tdc.club',
    username: 'admin',
    avatar_name: null,
    role: 'admin',
    language: 'en',
    email_verified: true,
    email_notifications: false,
    created_at: '2026-01-01T00:00:00Z',
    last_login: '2026-04-25T00:00:00Z',
  },
})

const userMe = (role: 'user' | 'staff'): ApiResponse<User> => ({
  ...adminMe(),
  data: { ...adminMe().data, role },
})

// Drives the handler's body validation: when given an input, return the
// callback's resolved value (or rethrow synchronously if it throws).
const passBody = (body: unknown) => {
  readValidatedBodyMock.mockImplementation(async (_event, parser: (i: unknown) => unknown) =>
    parser(body),
  )
}

describe('POST /api/revalidate', () => {
  beforeEach(() => {
    readValidatedBodyMock.mockReset()
    flaskFetchMock.mockReset()
    storageGetKeysMock.mockReset()
    storageRemoveItemMock.mockReset()
    storageGetKeysMock.mockResolvedValue([])
    storageRemoveItemMock.mockResolvedValue(undefined)
  })

  describe('auth gate', () => {
    it('returns 401 when flaskFetch rejects (no/invalid auth cookie)', async () => {
      flaskFetchMock.mockRejectedValue(new Error('401 from Flask'))
      passBody({ path: '/locations' })
      const event = {} as H3Event

      await expect(revalidateHandler(event)).rejects.toMatchObject({
        statusCode: 401,
      })
    })

    it('returns 403 when authenticated user has role "user"', async () => {
      flaskFetchMock.mockResolvedValue(userMe('user'))
      passBody({ path: '/locations' })
      const event = {} as H3Event

      await expect(revalidateHandler(event)).rejects.toMatchObject({
        statusCode: 403,
      })
    })

    it('returns 403 when authenticated user has role "staff"', async () => {
      flaskFetchMock.mockResolvedValue(userMe('staff'))
      passBody({ path: '/locations' })
      const event = {} as H3Event

      await expect(revalidateHandler(event)).rejects.toMatchObject({
        statusCode: 403,
      })
    })

    it('threads the H3Event through to flaskFetch (auth-forward integration)', async () => {
      flaskFetchMock.mockResolvedValue(adminMe())
      passBody({ path: '/locations' })
      const event = { context: { flaskHeaders: { Authorization: 'Bearer x' } } } as H3Event

      await revalidateHandler(event)

      expect(flaskFetchMock).toHaveBeenCalledWith('/api/auth/me', event)
    })
  })

  describe('body validation (admin caller)', () => {
    beforeEach(() => {
      flaskFetchMock.mockResolvedValue(adminMe())
    })

    it('rejects empty path', async () => {
      passBody({ path: '' })
      const event = {} as H3Event

      await expect(revalidateHandler(event)).rejects.toMatchObject({
        statusCode: 400,
      })
    })

    it('rejects path without leading slash', async () => {
      passBody({ path: 'locations' })
      const event = {} as H3Event

      await expect(revalidateHandler(event)).rejects.toMatchObject({
        statusCode: 400,
      })
    })

    it('rejects path containing ".."', async () => {
      passBody({ path: '/locations/../admin' })
      const event = {} as H3Event

      await expect(revalidateHandler(event)).rejects.toMatchObject({
        statusCode: 400,
      })
    })

    it('rejects path containing "//"', async () => {
      passBody({ path: '/locations//foo' })
      const event = {} as H3Event

      await expect(revalidateHandler(event)).rejects.toMatchObject({
        statusCode: 400,
      })
    })

    it('rejects path longer than 500 chars', async () => {
      passBody({ path: '/' + 'x'.repeat(501) })
      const event = {} as H3Event

      await expect(revalidateHandler(event)).rejects.toMatchObject({
        statusCode: 400,
      })
    })
  })

  describe('cache invalidation (admin caller, valid path)', () => {
    beforeEach(() => {
      flaskFetchMock.mockResolvedValue(adminMe())
    })

    it('returns { revalidated } and removes matching cache keys', async () => {
      // Nitro key shape (after unstorage normalization, with the
      // useStorage('cache:nitro:routes') prefix mount stripped):
      //   _:<escapedPathname>.<hash>.json
      // For /locations -> escapedPathname = "locations".
      storageGetKeysMock.mockResolvedValue([
        '_:locations.AbCdEfGhIj.json',
        '_:locations.XyZwUvTsRq.json',
        '_:events.UnrelatedKy.json', // must NOT be removed
      ])
      passBody({ path: '/locations' })
      const event = {} as H3Event

      const result = await revalidateHandler(event)

      expect(result).toEqual({ revalidated: '/locations' })
      expect(useStorageMock).toHaveBeenCalledWith('cache:nitro:routes')
      expect(storageGetKeysMock).toHaveBeenCalledWith('_')
      expect(storageRemoveItemMock).toHaveBeenCalledTimes(2)
      expect(storageRemoveItemMock).toHaveBeenCalledWith('_:locations.AbCdEfGhIj.json')
      expect(storageRemoveItemMock).toHaveBeenCalledWith('_:locations.XyZwUvTsRq.json')
      expect(storageRemoveItemMock).not.toHaveBeenCalledWith('_:events.UnrelatedKy.json')
    })

    it('returns 200 even when no cache entries exist for the path', async () => {
      storageGetKeysMock.mockResolvedValue([])
      passBody({ path: '/blog/some-post' })
      const event = {} as H3Event

      const result = await revalidateHandler(event)

      expect(result).toEqual({ revalidated: '/blog/some-post' })
      expect(storageRemoveItemMock).not.toHaveBeenCalled()
    })

    it('truncates pathname to 16 chars when matching (mirrors Nitro escapeKey)', async () => {
      // /locations/dreamerscave -> "locationsdreamer" (16 chars, slash stripped).
      storageGetKeysMock.mockResolvedValue([
        '_:locationsdreamer.HashOne.json',
        '_:locationsdreamer.HashTwo.json',
        '_:locations.OtherEntry.json', // shorter pathname, must NOT match
      ])
      passBody({ path: '/locations/dreamerscave' })
      const event = {} as H3Event

      await revalidateHandler(event)

      expect(storageRemoveItemMock).toHaveBeenCalledTimes(2)
      expect(storageRemoveItemMock).toHaveBeenCalledWith('_:locationsdreamer.HashOne.json')
      expect(storageRemoveItemMock).toHaveBeenCalledWith('_:locationsdreamer.HashTwo.json')
    })
  })
})
