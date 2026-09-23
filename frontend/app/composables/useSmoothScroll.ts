import type Lenis from 'lenis'

export function useSmoothScroll() {
  const scrollTo = (target: string | HTMLElement, options?: { offset?: number }) => {
    if (!import.meta.client) return
    // Respect user accessibility preference: skip programmatic smooth scroll
    // when reduced-motion is requested. Consumer fallback is browser-native
    // scrollIntoView / location hash if needed; this composable simply no-ops.
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const { $lenis } = useNuxtApp() as unknown as { $lenis: Lenis }
    $lenis?.scrollTo(target, options)
  }

  return { scrollTo }
}
