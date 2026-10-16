import { describe, it, expect } from 'vitest'
import type { User } from '../../app/types/user'

// Tests target the pure helpers extracted from the auth/admin/staff
// route middleware. Same rationale as `tests/unit/useApiFetch.test.ts`
// lines 4-12: `defineNuxtRouteMiddleware` is a Nuxt auto-import macro
// that vitest cannot reliably intercept, so the role-decision logic and
// redirect-URL construction live in pure functions in `app/utils/auth-guard.ts`.
// The middleware files are thin wrappers that translate `GuardOutcome`
// values to `navigateTo` / `createError` / pass-through. Exhaustively
// testing the helpers here covers every branch the wrappers can take.
import {
  buildLoginRedirect,
  decideAuthOutcome,
  decideAdminOutcome,
  decideStaffOutcome,
} from '../../app/utils/auth-guard'

const baseUser: User = {
  id: 1,
  email: 'a@b.c',
  username: 'u',
  avatar_name: null,
  role: 'user',
  language: 'en',
  email_verified: true,
  email_notifications: true,
  created_at: '2026-01-01T00:00:00Z',
  last_login: null,
}

const userOf = (role: User['role']): User => ({ ...baseUser, role })

describe('buildLoginRedirect', () => {
  it('builds /auth/login?redirect=<encoded> for a simple path', () => {
    expect(buildLoginRedirect('/dashboard')).toBe('/auth/login?redirect=%2Fdashboard')
  })

  it('encodes query strings in the destination (preserves ? and =)', () => {
    // `?` and `=` MUST be percent-encoded so the login page's parser
    // sees `redirect=` ending at the right boundary.
    expect(buildLoginRedirect('/dashboard?tab=profile')).toBe(
      '/auth/login?redirect=%2Fdashboard%3Ftab%3Dprofile',
    )
  })

  it('encodes hashes', () => {
    expect(buildLoginRedirect('/blog/post#section-2')).toBe(
      '/auth/login?redirect=%2Fblog%2Fpost%23section-2',
    )
  })

  it('encodes ampersands so multiple query params survive the round-trip', () => {
    expect(buildLoginRedirect('/admin/users?role=staff&active=1')).toBe(
      '/auth/login?redirect=%2Fadmin%2Fusers%3Frole%3Dstaff%26active%3D1',
    )
  })

  it('encodes non-ASCII path segments (i18n locales)', () => {
    expect(buildLoginRedirect('/it/eventi/séance')).toBe(
      '/auth/login?redirect=%2Fit%2Feventi%2Fs%C3%A9ance',
    )
  })
})

describe('decideAuthOutcome', () => {
  it('redirects guests to login with encoded fullPath', () => {
    expect(decideAuthOutcome(null, '/dashboard?tab=profile')).toEqual({
      kind: 'redirect',
      to: '/auth/login?redirect=%2Fdashboard%3Ftab%3Dprofile',
    })
  })

  it('passes through any authenticated user (regular)', () => {
    expect(decideAuthOutcome(userOf('user'), '/dashboard')).toEqual({ kind: 'passthrough' })
  })

  it('passes through staff', () => {
    expect(decideAuthOutcome(userOf('staff'), '/dashboard')).toEqual({ kind: 'passthrough' })
  })

  it('passes through admin', () => {
    expect(decideAuthOutcome(userOf('admin'), '/dashboard')).toEqual({ kind: 'passthrough' })
  })
})

describe('decideAdminOutcome', () => {
  it('redirects guests to login (so they can authenticate first)', () => {
    expect(decideAdminOutcome(null, '/admin/users')).toEqual({
      kind: 'redirect',
      to: '/auth/login?redirect=%2Fadmin%2Fusers',
    })
  })

  it('forbids regular users with 403 Admin only (NO redirect)', () => {
    // Authenticated non-admins are KNOWN users who lack the role; a
    // silent redirect to /auth/login would imply auth failed and is
    // misleading. 403 is correct: they are who they say they are, just
    // under-privileged.
    expect(decideAdminOutcome(userOf('user'), '/admin/users')).toEqual({
      kind: 'forbid',
      statusMessage: 'Admin only',
    })
  })

  it('forbids staff users (staff is not admin)', () => {
    expect(decideAdminOutcome(userOf('staff'), '/admin/users')).toEqual({
      kind: 'forbid',
      statusMessage: 'Admin only',
    })
  })

  it('passes through admin', () => {
    expect(decideAdminOutcome(userOf('admin'), '/admin/users')).toEqual({ kind: 'passthrough' })
  })
})

describe('decideStaffOutcome', () => {
  it('redirects guests to login', () => {
    expect(decideStaffOutcome(null, '/staff/events')).toEqual({
      kind: 'redirect',
      to: '/auth/login?redirect=%2Fstaff%2Fevents',
    })
  })

  it('forbids regular users with 403 Staff only', () => {
    expect(decideStaffOutcome(userOf('user'), '/staff/events')).toEqual({
      kind: 'forbid',
      statusMessage: 'Staff only',
    })
  })

  it('passes through staff', () => {
    expect(decideStaffOutcome(userOf('staff'), '/staff/events')).toEqual({ kind: 'passthrough' })
  })

  it('passes through admin (admin counts as staff in the role hierarchy)', () => {
    // Mirrors `useAuthStore.isStaff`: `role === 'staff' || role === 'admin'`.
    // Admin must satisfy any staff-only requirement, otherwise an admin
    // could be locked out of staff-managed content.
    expect(decideStaffOutcome(userOf('admin'), '/staff/events')).toEqual({ kind: 'passthrough' })
  })
})
