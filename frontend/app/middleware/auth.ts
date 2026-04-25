import { decideAuthOutcome } from '~/utils/auth-guard'

/**
 * Route guard: any authenticated user.
 *
 * Lazy-loads the user once per session via `fetchMe`. The store is
 * per-request on SSR (Nuxt rebuilds Pinia for each request) and
 * persists across navigations on the client, so the `!user.value` guard
 * keeps `fetchMe` to one BFF round-trip per session.
 *
 * Decision logic lives in `~/utils/auth-guard.ts` (pure, unit-tested).
 * This wrapper only translates the outcome into the side-effect Nuxt
 * expects (`navigateTo` for a redirect, return for pass-through).
 *
 * Apply with `definePageMeta({ middleware: ['auth'] })`.
 */
export default defineNuxtRouteMiddleware(async (to) => {
  const { user, fetchMe } = useAuth()

  if (!user.value) {
    await fetchMe()
  }

  const outcome = decideAuthOutcome(user.value, to.fullPath)
  if (outcome.kind === 'redirect') {
    return navigateTo(outcome.to)
  }
})
