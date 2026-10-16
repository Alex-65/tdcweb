import { decideStaffOutcome } from '~/utils/auth-guard'

/**
 * Route guard: staff or admin.
 *
 * Role hierarchy: admin > staff > user. Admin satisfies any staff-only
 * requirement (mirrors `useAuthStore.isStaff` which returns true for
 * both `'staff'` and `'admin'`). Outcomes:
 *   - guest                -> redirect to /auth/login?redirect=...
 *   - regular user         -> 403 'Staff only'
 *   - staff or admin       -> pass through
 *
 * Decision logic lives in `~/utils/auth-guard.ts` (pure, unit-tested).
 *
 * Apply with `definePageMeta({ middleware: ['auth', 'staff'] })`.
 */
export default defineNuxtRouteMiddleware(async (to) => {
  const { user, fetchMe } = useAuth()

  if (!user.value) {
    await fetchMe()
  }

  const outcome = decideStaffOutcome(user.value, to.fullPath)
  if (outcome.kind === 'redirect') {
    return navigateTo(outcome.to)
  }
  if (outcome.kind === 'forbid') {
    throw createError({ statusCode: 403, statusMessage: outcome.statusMessage })
  }
})
