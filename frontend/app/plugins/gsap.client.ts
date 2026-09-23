/**
 * GSAP client-only plugin.
 *
 * The `.client.ts` suffix excludes this plugin from the SSR bundle. GSAP
 * reaches for `window` on import, so it cannot run server-side.
 *
 * ScrollTrigger is registered here once — consumers use it via
 * `useNuxtApp().$gsap` / `$ScrollTrigger` in their composables.
 *
 * Animation cleanup is the CONSUMER's responsibility: wrap your animations
 * in `gsap.context(() => { ... })` and call `ctx.revert()` on
 * onBeforeUnmount. Without the context pattern, ScrollTrigger instances
 * leak across route navigations and fire on phantom selectors.
 * See docs/frontend/nuxt-playbook.md §8 and tdc-frontend-expert §Critical
 * Rules / SSR Safety.
 */
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

export default defineNuxtPlugin(() => {
  gsap.registerPlugin(ScrollTrigger)

  return {
    provide: {
      gsap,
      ScrollTrigger,
    },
  }
})
