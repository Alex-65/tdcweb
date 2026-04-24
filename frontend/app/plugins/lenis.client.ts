/**
 * Lenis smooth-scroll client-only plugin.
 *
 * - The `.client.ts` suffix excludes this plugin from the SSR bundle.
 *   Lenis reaches for `window`, `document`, and `requestAnimationFrame`
 *   on construction — it cannot run server-side.
 * - We sync Lenis's RAF via `gsap.ticker.add(...)` rather than spinning up
 *   a separate `requestAnimationFrame` loop. Two independent RAF loops
 *   drift out of sync and produce visible jitter. Single ticker = single
 *   source of truth. See CLAUDE.md § SSR Client-Only Rules #2 and
 *   docs/frontend/nuxt-playbook.md §9.
 * - `gsap.ticker.lagSmoothing(0)` disables GSAP's frame-drop compensation
 *   so Lenis sees real elapsed time per tick.
 * - On `/admin/*` and `/dashboard/*` routes we stop Lenis. Data tables,
 *   form scroll-into-view, and keyboard navigation depend on native
 *   browser scroll — smooth-scroll interferes.
 * - Depends on the GSAP plugin (`app/plugins/gsap.client.ts`) already
 *   having registered `$gsap` on the Nuxt app. Plugin loading order is
 *   alphabetical: `gsap` < `lenis`, so this is fine without explicit
 *   ordering config.
 */
import Lenis from 'lenis'

export default defineNuxtPlugin((nuxtApp) => {
  const lenis = new Lenis({
    duration: 1.2,
    smoothWheel: true,
  })

  const { $gsap } = nuxtApp as unknown as { $gsap: typeof import('gsap').gsap }
  $gsap.ticker.add((time: number) => lenis.raf(time * 1000))
  $gsap.ticker.lagSmoothing(0)

  const router = useRouter()
  router.beforeEach((to) => {
    if (to.path.startsWith('/admin') || to.path.startsWith('/dashboard')) {
      lenis.stop()
    } else {
      lenis.start()
    }
  })

  return {
    provide: {
      lenis,
    },
  }
})
