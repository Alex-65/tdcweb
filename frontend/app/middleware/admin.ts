import { decideAdminOutcome } from '~/utils/auth-guard'

/**
 * Route guard: admin only.
 *
 * Same fetchMe lazy-load as `auth`. Outcomes:
 *   - guest        -> redirect to /auth/login?redirect=...
 *   - non-admin    -> 403 'Admin only' (createError, surfaced on the
 *                     Nuxt error page; no silent redirect since the
 *                     user IS authenticated, just under-privileged)
 *   - admin        -> pass through
 *
 * Decision logic lives in `~/utils/auth-guard.ts` (pure, unit-tested).
 *
 * Apply with `definePageMeta({ middleware: ['auth', 'admin'] })`. The
 * `auth` middleware is included for layered semantics even though
 * `admin` would catch the guest case on its own; chaining keeps the
 * intent declarative.
 */
export default defineNuxtRouteMiddleware(async (to) => {
  const { user, fetchMe } = useAuth()

  if (!user.value) {
    await fetchMe()
  }

  const outcome = decideAdminOutcome(user.value, to.fullPath)
  if (outcome.kind === 'redirect') {
    return navigateTo(outcome.to)
  }
  if (outcome.kind === 'forbid') {
    throw createError({ statusCode: 403, statusMessage: outcome.statusMessage })
  }
})
