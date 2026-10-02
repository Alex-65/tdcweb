import type { gsap } from 'gsap'

export function useScrollAnimation() {
  const ctx = ref<ReturnType<typeof import('gsap').gsap.context> | null>(null)

  const animateReveal = (selector: string, options: Record<string, unknown> = {}) => {
    if (!import.meta.client) return
    // Respect user accessibility preference: skip reveal entirely when the
    // system signals reduced motion. Elements render at their natural CSS
    // state (no translate, no fade-in), consistent with the intent of the
    // prefers-reduced-motion media query.
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const { $gsap } = useNuxtApp() as unknown as { $gsap: typeof gsap }
    ctx.value = $gsap.context(() => {
      $gsap.from(selector, {
        y: 100,
        opacity: 0,
        duration: 1,
        stagger: 0.2,
        scrollTrigger: { trigger: selector, start: 'top 80%' },
        ...options,
      })
    })
  }

  onBeforeUnmount(() => {
    if (!import.meta.client) return
    ctx.value?.revert()
    const { $ScrollTrigger } = useNuxtApp() as unknown as {
      $ScrollTrigger: typeof import('gsap/ScrollTrigger').ScrollTrigger
    }
    $ScrollTrigger?.refresh()
  })

  return { animateReveal }
}
