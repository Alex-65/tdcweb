import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { User } from '../../app/types/user'

// Tests target the pure `buildAuthOps` helper extracted from `useAuth`.
// Same rationale as `tests/unit/useApiFetch.test.ts` lines 4-12: the
// `useAuth` composable consumes Nuxt auto-imports (`useAuthStore`,
// `useRequestFetch`, `storeToRefs`) which the unimport transformer
// rewrites to real module references, making them brittle to mock
// directly. The composable is a thin wire-up; all behaviour
// (fetchMe error swallow, login bubble, logout clear-on-failure) lives
// in `buildAuthOps` and is exhaustively covered here.
import { buildAuthOps, type AuthStoreLike } from '../../app/composables/useAuth'

const sampleUser: User = {
  id: 7,
  email: 'staff@tdc.club',
  username: 'staffer',
  avatar_name: null,
  role: 'staff',
  language: 'en',
  email_verified: true,
  email_notifications: true,
  created_at: '2026-01-01T00:00:00Z',
  last_login: null,
}

interface FakeStoreState {
  user: User | null
}

const buildFakeStore = (): AuthStoreLike & { state: FakeStoreState } => {
  const state: FakeStoreState = { user: null }
  return {
    state,
    setUser: (u) => { state.user = u },
    clear: () => { state.user = null },
  }
}

describe('buildAuthOps', () => {
  let store: ReturnType<typeof buildFakeStore>
  let fetcher: ReturnType<typeof vi.fn>

  beforeEach(() => {
    store = buildFakeStore()
    fetcher = vi.fn()
  })

  describe('login', () => {
    it('POSTs credentials, sets the store, and returns the user', async () => {
      fetcher.mockResolvedValue({ user: sampleUser })

      const { login } = buildAuthOps(store, fetcher)
      const result = await login('staff@tdc.club', 'pw')

      expect(fetcher).toHaveBeenCalledWith('/api/auth/login', {
        method: 'POST',
        body: { email: 'staff@tdc.club', password: 'pw' },
      })
      expect(result).toEqual(sampleUser)
      expect(store.state.user).toEqual(sampleUser)
    })

    it('bubbles BFF errors and leaves the store untouched', async () => {
      fetcher.mockRejectedValue(new Error('Invalid credentials'))

      const { login } = buildAuthOps(store, fetcher)
      await expect(login('bad@x.y', 'wrong')).rejects.toThrow('Invalid credentials')
      // No setUser call -- a failed retry must not wipe a previous
      // successful session that may already be in the store.
      expect(store.state.user).toBeNull()
    })

    it('does NOT clear an existing session on login failure', async () => {
      // Pre-populate (simulating a previous successful login).
      store.setUser(sampleUser)
      fetcher.mockRejectedValue(new Error('Invalid credentials'))

      const { login } = buildAuthOps(store, fetcher)
      await expect(login('bad@x.y', 'wrong')).rejects.toThrow()
      expect(store.state.user).toEqual(sampleUser)
    })
  })

  describe('logout', () => {
    it('POSTs to logout and clears the store on success', async () => {
      store.setUser(sampleUser)
      fetcher.mockResolvedValue({ success: true })

      const { logout } = buildAuthOps(store, fetcher)
      await logout()

      expect(fetcher).toHaveBeenCalledWith('/api/auth/logout', { method: 'POST' })
      expect(store.state.user).toBeNull()
    })

    it('clears the store even when the BFF call fails (try/finally)', async () => {
      // Resilience contract: the local UI must reflect logged-out state
      // regardless of whether the BFF round-trip succeeded. The BFF
      // handler itself already clears cookies in its `catch`, mirroring
      // this resilience server-side.
      store.setUser(sampleUser)
      fetcher.mockRejectedValue(new Error('network down'))

      const { logout } = buildAuthOps(store, fetcher)
      await expect(logout()).rejects.toThrow('network down')
      expect(store.state.user).toBeNull()
    })
  })

  describe('fetchMe', () => {
    it('hydrates the store on success and returns the user', async () => {
      fetcher.mockResolvedValue({ user: sampleUser })

      const { fetchMe } = buildAuthOps(store, fetcher)
      const result = await fetchMe()

      expect(fetcher).toHaveBeenCalledWith('/api/auth/me')
      expect(result).toEqual(sampleUser)
      expect(store.state.user).toEqual(sampleUser)
    })

    it('clears the store and returns null on 401 (graceful guest fallback)', async () => {
      // Pre-populate to verify clear-on-error: a stale session that the
      // backend has rejected must drop locally too.
      store.setUser(sampleUser)
      fetcher.mockRejectedValue(
        Object.assign(new Error('Not authenticated'), { statusCode: 401 }),
      )

      const { fetchMe } = buildAuthOps(store, fetcher)
      const result = await fetchMe()

      expect(result).toBeNull()
      expect(store.state.user).toBeNull()
    })

    it('does NOT throw on failure -- guest browsing must not crash', async () => {
      fetcher.mockRejectedValue(new Error('boom'))
      const { fetchMe } = buildAuthOps(store, fetcher)
      // Critical: route middleware calls fetchMe on every navigation.
      // If it threw, every page load would crash for unauthenticated
      // visitors instead of falling through to the guest UI.
      await expect(fetchMe()).resolves.toBeNull()
      expect(store.state.user).toBeNull()
    })

    it('clears a previously-set user when fetchMe fails (stale session drop)', async () => {
      store.setUser(sampleUser)
      fetcher.mockRejectedValue(new Error('network'))

      const { fetchMe } = buildAuthOps(store, fetcher)
      await fetchMe()
      expect(store.state.user).toBeNull()
    })
  })
})
