---
name: tdc-frontend
description: Create Vue.js 3 frontend code for The Dreamer's Cave. Use for components, composables, stores, animations, and theming.
---

# TDC Frontend Developer

Expert agent for creating Vue.js 3 frontend code for The Dreamer's Cave virtual music club website.

## Trigger

Use this skill when:
- User asks to create or modify frontend code
- User says "/frontend", "/tdc-frontend", "/vue", or "/component"
- User asks to create Vue components, composables, or stores
- User wants to implement animations, theming, or i18n
- User asks about GSAP, Tailwind, or TipTap

## Project Context

**The Dreamer's Cave** - Website for a virtual music club in Second Life.
**Motto:** "You Can See The Music"

### Tech Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| Framework | Vue.js 3 | Composition API, `<script setup>` |
| Build | Vite | Fast HMR, optimized builds |
| Styling | Tailwind CSS | Utility-first, dark theme |
| Animations | GSAP + ScrollTrigger | Apple-style scroll animations |
| Smooth Scroll | Lenis | Smooth scrolling library |
| State | Pinia | Vue 3 state management |
| i18n | Vue I18n | EN, IT, FR, ES |
| Icons | Lucide Vue | Consistent icon set |
| WYSIWYG | TipTap | Rich text editor |

### File Structure

```
frontend/
├── src/
│   ├── assets/
│   │   ├── images/
│   │   ├── videos/
│   │   └── fonts/
│   │
│   ├── components/
│   │   ├── common/           # Shared components
│   │   │   ├── AppHeader.vue
│   │   │   ├── AppFooter.vue
│   │   │   ├── AppNav.vue
│   │   │   ├── LanguageSwitcher.vue
│   │   │   ├── LoadingSpinner.vue
│   │   │   ├── Modal.vue
│   │   │   └── Toast.vue
│   │   │
│   │   ├── landing/          # Landing page sections
│   │   │   ├── HeroSection.vue
│   │   │   ├── LocationsPreview.vue
│   │   │   ├── EventsCarousel.vue
│   │   │   ├── TechShowcase.vue
│   │   │   └── PatreonCTA.vue
│   │   │
│   │   ├── locations/        # Location components
│   │   │   ├── LocationCard.vue
│   │   │   ├── LocationGallery.vue
│   │   │   └── LocationMap.vue
│   │   │
│   │   ├── events/           # Event components
│   │   │   ├── EventCard.vue
│   │   │   ├── EventCalendar.vue
│   │   │   └── EventCountdown.vue
│   │   │
│   │   ├── artists/          # Artist components
│   │   │   ├── ArtistCard.vue
│   │   │   └── ArtistGallery.vue
│   │   │
│   │   ├── blog/             # Blog components
│   │   │   ├── PostCard.vue
│   │   │   └── PostContent.vue
│   │   │
│   │   ├── auth/             # Auth components
│   │   │   ├── LoginForm.vue
│   │   │   ├── RegisterForm.vue
│   │   │   └── OAuthButtons.vue
│   │   │
│   │   ├── user/             # User profile components
│   │   │   ├── ProfileForm.vue
│   │   │   └── NotificationSettings.vue
│   │   │
│   │   └── admin/            # Admin components
│   │       ├── AdminSidebar.vue
│   │       ├── DataTable.vue
│   │       ├── MediaPicker.vue
│   │       └── WysiwygEditor.vue
│   │
│   ├── composables/
│   │   ├── useAuth.js
│   │   ├── useApi.js
│   │   ├── useScrollAnimations.js
│   │   ├── useTheme.js
│   │   └── useI18n.js
│   │
│   ├── stores/
│   │   ├── auth.js
│   │   ├── locations.js
│   │   ├── events.js
│   │   ├── artists.js
│   │   └── ui.js
│   │
│   ├── views/
│   │   ├── LandingPage.vue
│   │   ├── LocationsPage.vue
│   │   ├── LocationDetailPage.vue
│   │   ├── EventsPage.vue
│   │   ├── ArtistsPage.vue
│   │   ├── BlogPage.vue
│   │   ├── LoginPage.vue
│   │   └── admin/
│   │       └── DashboardPage.vue
│   │
│   ├── router/
│   │   └── index.js
│   │
│   ├── i18n/
│   │   ├── en.json
│   │   ├── it.json
│   │   ├── fr.json
│   │   ├── es.json
│   │   └── index.js
│   │
│   ├── styles/
│   │   ├── main.css
│   │   ├── animations.css
│   │   └── themes/
│   │       ├── base.css
│   │       └── locations.css
│   │
│   ├── utils/
│   │   ├── api.js
│   │   ├── date.js
│   │   └── validators.js
│   │
│   ├── App.vue
│   └── main.js
│
├── public/
├── index.html
├── vite.config.js
├── tailwind.config.js
└── package.json
```

## Instructions

### Phase 1: Component Pattern (Vue 3 Composition API)

Always use `<script setup>` syntax:

```vue
<script setup>
/**
 * LocationCard - Displays a location with mood-based theming.
 *
 * Features:
 * - Dynamic theme based on location mood
 * - GSAP entrance animation
 * - Accessible keyboard navigation
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { gsap } from 'gsap'
import { MapPin, Users } from 'lucide-vue-next'

// ============================================
// Props
// ============================================
const props = defineProps({
  /**
   * Location data object from API
   */
  location: {
    type: Object,
    required: true,
    validator: (loc) => loc.slug && loc.name
  },
  /**
   * Enable entrance animation
   */
  animated: {
    type: Boolean,
    default: true
  },
  /**
   * Card size variant
   */
  size: {
    type: String,
    default: 'medium',
    validator: (v) => ['small', 'medium', 'large'].includes(v)
  }
})

// ============================================
// Emits
// ============================================
const emit = defineEmits({
  /**
   * Emitted when card is selected
   * @param {string} slug - Location slug
   */
  select: (slug) => typeof slug === 'string'
})

// ============================================
// Composables
// ============================================
const router = useRouter()
const { t } = useI18n()

// ============================================
// Refs
// ============================================
const cardRef = ref(null)
const isHovered = ref(false)
let animation = null

// ============================================
// Computed
// ============================================
const themeStyles = computed(() => ({
  '--location-primary': props.location.theme?.primary_color || '#06b6d4',
  '--location-secondary': props.location.theme?.secondary_color || '#8b5cf6',
  '--location-accent': props.location.theme?.accent_color || '#22c55e',
  '--location-dark': props.location.theme?.dark_color || '#0a0a0f',
  '--location-gradient': props.location.theme?.css_gradient ||
    'linear-gradient(135deg, var(--location-primary), var(--location-secondary))'
}))

const sizeClasses = computed(() => ({
  small: 'h-48',
  medium: 'h-64',
  large: 'h-96'
}[props.size]))

// ============================================
// Methods
// ============================================
const handleClick = () => {
  emit('select', props.location.slug)
  router.push(`/locations/${props.location.slug}`)
}

const handleKeydown = (event) => {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    handleClick()
  }
}

// ============================================
// Lifecycle - Animation Setup
// ============================================
onMounted(() => {
  if (props.animated && cardRef.value) {
    // Initial state
    gsap.set(cardRef.value, {
      opacity: 0,
      y: 50,
      scale: 0.95
    })

    // Entrance animation
    animation = gsap.to(cardRef.value, {
      opacity: 1,
      y: 0,
      scale: 1,
      duration: 0.8,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: cardRef.value,
        start: 'top 85%',
        toggleActions: 'play none none reverse'
      }
    })
  }
})

onUnmounted(() => {
  // IMPORTANT: Always cleanup GSAP animations
  if (animation) {
    animation.kill()
  }
})
</script>

<template>
  <article
    ref="cardRef"
    :style="themeStyles"
    :class="[
      'location-card group relative overflow-hidden rounded-2xl cursor-pointer',
      'transition-transform duration-300 hover:scale-[1.02]',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
      'focus-visible:ring-[var(--location-primary)]',
      sizeClasses
    ]"
    tabindex="0"
    role="button"
    :aria-label="t('locations.viewLocation', { name: location.name })"
    @click="handleClick"
    @keydown="handleKeydown"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
  >
    <!-- Background gradient -->
    <div
      class="absolute inset-0 bg-gradient-to-br opacity-80 transition-opacity duration-300 group-hover:opacity-100"
      :style="{ background: 'var(--location-gradient)' }"
    />

    <!-- Dark overlay for text readability -->
    <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />

    <!-- Content -->
    <div class="relative h-full flex flex-col justify-end p-6 text-white">
      <!-- Mood badge -->
      <span
        class="absolute top-4 right-4 px-3 py-1 text-xs font-medium rounded-full"
        :class="{
          'bg-cyan-500/20 text-cyan-300': location.mood_category === 'cosmic_tech',
          'bg-amber-500/20 text-amber-300': location.mood_category === 'warm_intimate',
          'bg-purple-500/20 text-purple-300': location.mood_category === 'hybrid'
        }"
      >
        {{ t(`locations.mood.${location.mood_category}`) }}
      </span>

      <!-- Location name -->
      <h3 class="text-2xl font-bold mb-2 drop-shadow-lg">
        {{ location.name }}
      </h3>

      <!-- Tagline -->
      <p
        v-if="location.tagline"
        class="text-sm text-white/80 line-clamp-2 mb-4"
      >
        {{ location.tagline }}
      </p>

      <!-- Meta info -->
      <div class="flex items-center gap-4 text-sm text-white/70">
        <span class="flex items-center gap-1">
          <Users class="w-4 h-4" aria-hidden="true" />
          {{ t('locations.capacity', { count: location.capacity }) }}
        </span>
        <span
          v-if="location.slurl"
          class="flex items-center gap-1"
        >
          <MapPin class="w-4 h-4" aria-hidden="true" />
          {{ t('locations.inSecondLife') }}
        </span>
      </div>
    </div>

    <!-- Hover glow effect -->
    <div
      class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
      :style="{
        background: `radial-gradient(circle at 50% 50%, var(--location-primary), transparent 70%)`,
        mixBlendMode: 'overlay'
      }"
    />
  </article>
</template>

<style scoped>
.location-card {
  /* Inherit theme variables from parent or use defaults */
  --location-primary: v-bind('themeStyles["--location-primary"]');
  --location-secondary: v-bind('themeStyles["--location-secondary"]');
}

/* Reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  .location-card {
    transition: none;
  }
}
</style>
```

### Phase 2: Composable Pattern

```javascript
/**
 * useScrollAnimations - GSAP scroll animation utilities.
 *
 * Provides:
 * - Smooth scrolling with Lenis
 * - Hero parallax effects
 * - Reveal animations on scroll
 * - Parallax background effects
 *
 * @example
 * const { initSmoothScroll, animateHero } = useScrollAnimations()
 * onMounted(() => {
 *   initSmoothScroll()
 *   animateHero(heroRef.value)
 * })
 */
import { ref, onUnmounted } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import Lenis from '@studio-freight/lenis'

// Register GSAP plugins
gsap.registerPlugin(ScrollTrigger)

export function useScrollAnimations() {
  // Track all animations for cleanup
  const animations = ref([])
  const triggers = ref([])
  let lenis = null

  /**
   * Initialize Lenis smooth scrolling.
   * Call once on app/page mount.
   */
  const initSmoothScroll = () => {
    lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
      touchMultiplier: 2
    })

    // Connect Lenis to GSAP ScrollTrigger
    lenis.on('scroll', ScrollTrigger.update)

    gsap.ticker.add((time) => {
      lenis.raf(time * 1000)
    })

    gsap.ticker.lagSmoothing(0)
  }

  /**
   * Destroy Lenis instance.
   */
  const destroySmoothScroll = () => {
    if (lenis) {
      lenis.destroy()
      lenis = null
    }
  }

  /**
   * Create hero section parallax animation.
   *
   * @param {HTMLElement} element - Hero container element
   * @param {Object} options - Animation options
   */
  const animateHero = (element, options = {}) => {
    if (!element) return

    const {
      videoSelector = '.hero-video',
      textSelector = '.hero-text',
      scaleEnd = 1.2,
      opacityEnd = 0
    } = options

    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: element,
        start: 'top top',
        end: 'bottom top',
        scrub: true,
        pin: options.pin ?? false
      }
    })

    const video = element.querySelector(videoSelector)
    const text = element.querySelector(textSelector)

    if (video) {
      tl.to(video, { scale: scaleEnd, opacity: opacityEnd }, 0)
    }

    if (text) {
      tl.to(text, { y: -100, opacity: opacityEnd }, 0)
    }

    animations.value.push(tl)
    triggers.value.push(tl.scrollTrigger)

    return tl
  }

  /**
   * Create staggered reveal animation on scroll.
   *
   * @param {HTMLElement|HTMLElement[]} elements - Elements to animate
   * @param {Object} options - Animation options
   */
  const animateReveal = (elements, options = {}) => {
    if (!elements) return

    const elementsArray = Array.isArray(elements) ? elements : [elements]
    if (elementsArray.length === 0) return

    const {
      y = 100,
      opacity = 0,
      duration = 1,
      stagger = 0.2,
      ease = 'power3.out',
      start = 'top 85%',
      once = true
    } = options

    const anim = gsap.from(elementsArray, {
      y,
      opacity,
      duration,
      stagger,
      ease,
      scrollTrigger: {
        trigger: elementsArray[0],
        start,
        toggleActions: once ? 'play none none none' : 'play reverse play reverse'
      }
    })

    animations.value.push(anim)
    if (anim.scrollTrigger) {
      triggers.value.push(anim.scrollTrigger)
    }

    return anim
  }

  /**
   * Create parallax effect for element.
   *
   * @param {HTMLElement} element - Element to animate
   * @param {number} speed - Parallax speed (0-1)
   */
  const animateParallax = (element, speed = 0.5) => {
    if (!element) return

    const anim = gsap.to(element, {
      y: () => window.innerHeight * speed,
      ease: 'none',
      scrollTrigger: {
        trigger: element,
        start: 'top bottom',
        end: 'bottom top',
        scrub: true
      }
    })

    animations.value.push(anim)
    triggers.value.push(anim.scrollTrigger)

    return anim
  }

  /**
   * Create fade-in animation.
   *
   * @param {HTMLElement} element - Element to animate
   * @param {Object} options - Animation options
   */
  const animateFadeIn = (element, options = {}) => {
    if (!element) return

    const {
      duration = 0.8,
      delay = 0,
      ease = 'power2.out'
    } = options

    return gsap.fromTo(element,
      { opacity: 0 },
      { opacity: 1, duration, delay, ease }
    )
  }

  /**
   * Cleanup all animations and triggers.
   * MUST be called in onUnmounted.
   */
  const cleanup = () => {
    // Kill all ScrollTriggers
    triggers.value.forEach(trigger => {
      if (trigger) trigger.kill()
    })
    triggers.value = []

    // Kill all animations
    animations.value.forEach(anim => {
      if (anim) anim.kill()
    })
    animations.value = []

    // Destroy Lenis
    destroySmoothScroll()
  }

  // Auto cleanup on unmount
  onUnmounted(cleanup)

  return {
    // Smooth scroll
    initSmoothScroll,
    destroySmoothScroll,

    // Animations
    animateHero,
    animateReveal,
    animateParallax,
    animateFadeIn,

    // Manual cleanup
    cleanup
  }
}
```

### Phase 3: Theme Composable

```javascript
/**
 * useTheme - Location-based theming system.
 *
 * Manages CSS custom properties based on current location.
 *
 * @example
 * const { setLocationTheme, clearTheme } = useTheme()
 * setLocationTheme(location)
 */
import { ref, watch, onUnmounted } from 'vue'

// Default dark theme
const DEFAULT_THEME = {
  '--color-bg': '#0a0a0f',
  '--color-surface': '#141420',
  '--color-text': '#ffffff',
  '--color-text-muted': '#a0a0b0',
  '--color-primary': '#06b6d4',
  '--color-secondary': '#8b5cf6',
  '--color-accent': '#22c55e'
}

// Location theme presets (from mood guide)
const LOCATION_THEMES = {
  dreamerscave: {
    '--color-primary': '#0891b2',
    '--color-secondary': '#06b6d4',
    '--color-accent': '#22c55e',
    '--color-accent-warm': '#eab308',
    '--color-dark': '#0c1222',
    '--gradient-hero': 'linear-gradient(135deg, #0891b2, #22c55e, #eab308)'
  },
  dreamerscave2: {
    '--color-primary': '#1e3a8a',
    '--color-secondary': '#3b82f6',
    '--color-accent': '#8b5cf6',
    '--color-accent-warm': '#ec4899',
    '--color-dark': '#0f172a',
    '--gradient-hero': 'linear-gradient(135deg, #1e3a8a, #8b5cf6, #ec4899)'
  },
  dreamvision: {
    '--color-primary': '#06b6d4',
    '--color-secondary': '#22c55e',
    '--color-accent': '#facc15',
    '--color-glow': '#ffffff',
    '--color-dark': '#020617',
    '--gradient-hero': 'linear-gradient(135deg, #06b6d4, #22c55e, #facc15)'
  },
  evanescence: {
    '--color-primary': '#fbbf24',
    '--color-secondary': '#0ea5e9',
    '--color-accent': '#06b6d4',
    '--color-glow': '#fef3c7',
    '--color-dark': '#0c1222',
    '--gradient-hero': 'radial-gradient(ellipse at center, #fef3c7, #fbbf24, #0ea5e9, #0c1222)'
  },
  livemagic: {
    '--color-primary': '#dc2626',
    '--color-secondary': '#f97316',
    '--color-accent': '#8b5cf6',
    '--color-accent-green': '#22c55e',
    '--color-dark': '#030712',
    '--gradient-hero': 'linear-gradient(135deg, #dc2626, #f97316, #8b5cf6)'
  },
  lounge: {
    '--color-primary': '#a855f7',
    '--color-secondary': '#ec4899',
    '--color-accent': '#f59e0b',
    '--color-concrete': '#57534e',
    '--color-dark': '#1c1917',
    '--gradient-hero': 'linear-gradient(135deg, #a855f7, #ec4899, #f59e0b)'
  },
  arquipelago: {
    '--color-primary': '#14b8a6',
    '--color-secondary': '#92400e',
    '--color-accent': '#f97316',
    '--color-water': '#06b6d4',
    '--color-dark': '#134e4a',
    '--gradient-hero': 'linear-gradient(135deg, #14b8a6, #06b6d4, #f97316)'
  },
  noahsark: {
    '--color-primary': '#d97706',
    '--color-secondary': '#92400e',
    '--color-accent': '#14b8a6',
    '--color-gold': '#fbbf24',
    '--color-dark': '#451a03',
    '--gradient-hero': 'linear-gradient(135deg, #d97706, #fbbf24, #14b8a6)'
  },
  jazzclub: {
    '--color-primary': '#92400e',
    '--color-secondary': '#78350f',
    '--color-accent': '#14b8a6',
    '--color-gold': '#d97706',
    '--color-dark': '#1c1917',
    '--gradient-hero': 'linear-gradient(135deg, #92400e, #991b1b, #14b8a6)'
  }
}

export function useTheme() {
  const currentTheme = ref(null)
  const currentLocation = ref(null)

  /**
   * Apply CSS custom properties to document root.
   *
   * @param {Object} theme - Theme object with CSS properties
   */
  const applyTheme = (theme) => {
    const root = document.documentElement

    // Apply each property
    Object.entries(theme).forEach(([key, value]) => {
      root.style.setProperty(key, value)
    })

    currentTheme.value = theme
  }

  /**
   * Set theme based on location.
   *
   * @param {Object|string} location - Location object or slug
   */
  const setLocationTheme = (location) => {
    const slug = typeof location === 'string' ? location : location?.slug

    if (!slug) {
      clearTheme()
      return
    }

    // Normalize slug (remove spaces, lowercase)
    const normalizedSlug = slug.toLowerCase().replace(/[^a-z0-9]/g, '')

    // Get preset or use location's custom theme
    let theme = LOCATION_THEMES[normalizedSlug]

    // If location has custom theme data, use it
    if (typeof location === 'object' && location.theme) {
      theme = {
        '--color-primary': location.theme.primary_color,
        '--color-secondary': location.theme.secondary_color,
        '--color-accent': location.theme.accent_color,
        '--color-dark': location.theme.dark_color,
        '--gradient-hero': location.theme.css_gradient
      }
    }

    if (theme) {
      // Merge with defaults
      applyTheme({ ...DEFAULT_THEME, ...theme })
      currentLocation.value = slug

      // Set data attribute for CSS targeting
      document.documentElement.setAttribute('data-location', normalizedSlug)
    }
  }

  /**
   * Clear location theme and restore defaults.
   */
  const clearTheme = () => {
    applyTheme(DEFAULT_THEME)
    currentLocation.value = null
    document.documentElement.removeAttribute('data-location')
  }

  /**
   * Get current theme values.
   */
  const getTheme = () => currentTheme.value

  // Cleanup on unmount
  onUnmounted(() => {
    clearTheme()
  })

  return {
    currentTheme,
    currentLocation,
    setLocationTheme,
    clearTheme,
    getTheme,
    LOCATION_THEMES
  }
}
```

### Phase 4: Pinia Store Pattern

```javascript
/**
 * Locations Store - Manages location data and theming.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useApi } from '@/composables/useApi'
import { useTheme } from '@/composables/useTheme'

export const useLocationsStore = defineStore('locations', () => {
  // ============================================
  // State
  // ============================================
  const locations = ref([])
  const currentLocation = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // ============================================
  // Composables
  // ============================================
  const api = useApi()
  const { setLocationTheme, clearTheme } = useTheme()

  // ============================================
  // Getters (computed)
  // ============================================
  const locationsByMood = computed(() => {
    const grouped = {
      cosmic_tech: [],
      warm_intimate: [],
      hybrid: []
    }

    locations.value.forEach(loc => {
      if (grouped[loc.mood_category]) {
        grouped[loc.mood_category].push(loc)
      }
    })

    return grouped
  })

  const activeLocations = computed(() =>
    locations.value.filter(loc => loc.is_active)
  )

  const getBySlug = computed(() => (slug) =>
    locations.value.find(loc => loc.slug === slug)
  )

  // ============================================
  // Actions
  // ============================================

  /**
   * Fetch all locations from API.
   *
   * @param {string} lang - Language code
   */
  async function fetchAll(lang = 'en') {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/locations', { params: { lang } })
      locations.value = response.data
    } catch (err) {
      error.value = err.message
      console.error('Failed to fetch locations:', err)
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch single location by slug.
   *
   * @param {string} slug - Location slug
   * @param {string} lang - Language code
   */
  async function fetchBySlug(slug, lang = 'en') {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/locations/${slug}`, { params: { lang } })
      currentLocation.value = response.data

      // Apply location theme
      setLocationTheme(response.data)

      return response.data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear current location and theme.
   */
  function clearCurrent() {
    currentLocation.value = null
    clearTheme()
  }

  /**
   * Reset store state.
   */
  function $reset() {
    locations.value = []
    currentLocation.value = null
    loading.value = false
    error.value = null
    clearTheme()
  }

  return {
    // State
    locations,
    currentLocation,
    loading,
    error,

    // Getters
    locationsByMood,
    activeLocations,
    getBySlug,

    // Actions
    fetchAll,
    fetchBySlug,
    clearCurrent,
    $reset
  }
})
```

### Phase 5: API Composable

```javascript
/**
 * useApi - API client composable.
 *
 * Features:
 * - Axios instance with interceptors
 * - JWT token handling
 * - Language header injection
 * - Error transformation
 */
import { ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

export function useApi() {
  const loading = ref(false)
  const error = ref(null)

  // Create axios instance
  const client = axios.create({
    baseURL: BASE_URL,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json'
    }
  })

  // Request interceptor
  client.interceptors.request.use((config) => {
    const authStore = useAuthStore()
    const { locale } = useI18n()

    // Add JWT token if available
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }

    // Add language header
    config.headers['Accept-Language'] = locale.value

    return config
  })

  // Response interceptor
  client.interceptors.response.use(
    (response) => {
      // API returns { success, data, meta }
      if (response.data?.success) {
        return response.data
      }
      return response.data
    },
    (err) => {
      const authStore = useAuthStore()

      // Handle 401 - Unauthorized
      if (err.response?.status === 401) {
        authStore.logout()
      }

      // Transform error
      const message = err.response?.data?.error || err.message || 'Unknown error'
      error.value = message

      return Promise.reject(new Error(message))
    }
  )

  /**
   * GET request.
   */
  const get = async (url, config = {}) => {
    loading.value = true
    error.value = null
    try {
      return await client.get(url, config)
    } finally {
      loading.value = false
    }
  }

  /**
   * POST request.
   */
  const post = async (url, data = {}, config = {}) => {
    loading.value = true
    error.value = null
    try {
      return await client.post(url, data, config)
    } finally {
      loading.value = false
    }
  }

  /**
   * PUT request.
   */
  const put = async (url, data = {}, config = {}) => {
    loading.value = true
    error.value = null
    try {
      return await client.put(url, data, config)
    } finally {
      loading.value = false
    }
  }

  /**
   * DELETE request.
   */
  const del = async (url, config = {}) => {
    loading.value = true
    error.value = null
    try {
      return await client.delete(url, config)
    } finally {
      loading.value = false
    }
  }

  return {
    client,
    loading,
    error,
    get,
    post,
    put,
    del
  }
}
```

### Phase 6: TipTap WYSIWYG Editor

```vue
<script setup>
/**
 * WysiwygEditor - TipTap rich text editor wrapper.
 *
 * Features:
 * - Rich text formatting
 * - Image insertion
 * - Link editing
 * - HTML output
 */
import { ref, watch, onBeforeUnmount } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'
import {
  Bold, Italic, Strikethrough, Code,
  List, ListOrdered, Quote, Undo, Redo,
  Link as LinkIcon, Image as ImageIcon
} from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Write something...'
  },
  editable: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue'])

// ============================================
// Editor Setup
// ============================================
const editor = useEditor({
  content: props.modelValue,
  editable: props.editable,
  extensions: [
    StarterKit,
    Image.configure({
      HTMLAttributes: {
        class: 'rounded-lg max-w-full'
      }
    }),
    Link.configure({
      openOnClick: false,
      HTMLAttributes: {
        class: 'text-cyan-400 hover:text-cyan-300 underline'
      }
    }),
    Placeholder.configure({
      placeholder: props.placeholder
    })
  ],
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML())
  }
})

// Sync prop changes
watch(() => props.modelValue, (value) => {
  if (editor.value && value !== editor.value.getHTML()) {
    editor.value.commands.setContent(value, false)
  }
})

// Cleanup
onBeforeUnmount(() => {
  editor.value?.destroy()
})

// ============================================
// Toolbar Actions
// ============================================
const addImage = () => {
  const url = window.prompt('Image URL')
  if (url) {
    editor.value.chain().focus().setImage({ src: url }).run()
  }
}

const addLink = () => {
  const url = window.prompt('Link URL')
  if (url) {
    editor.value.chain().focus().setLink({ href: url }).run()
  }
}

// Toolbar button config
const toolbarButtons = [
  { icon: Bold, action: () => editor.value.chain().focus().toggleBold().run(), isActive: () => editor.value?.isActive('bold'), label: 'Bold' },
  { icon: Italic, action: () => editor.value.chain().focus().toggleItalic().run(), isActive: () => editor.value?.isActive('italic'), label: 'Italic' },
  { icon: Strikethrough, action: () => editor.value.chain().focus().toggleStrike().run(), isActive: () => editor.value?.isActive('strike'), label: 'Strikethrough' },
  { icon: Code, action: () => editor.value.chain().focus().toggleCode().run(), isActive: () => editor.value?.isActive('code'), label: 'Code' },
  { type: 'divider' },
  { icon: List, action: () => editor.value.chain().focus().toggleBulletList().run(), isActive: () => editor.value?.isActive('bulletList'), label: 'Bullet list' },
  { icon: ListOrdered, action: () => editor.value.chain().focus().toggleOrderedList().run(), isActive: () => editor.value?.isActive('orderedList'), label: 'Numbered list' },
  { icon: Quote, action: () => editor.value.chain().focus().toggleBlockquote().run(), isActive: () => editor.value?.isActive('blockquote'), label: 'Quote' },
  { type: 'divider' },
  { icon: LinkIcon, action: addLink, isActive: () => editor.value?.isActive('link'), label: 'Add link' },
  { icon: ImageIcon, action: addImage, label: 'Add image' },
  { type: 'divider' },
  { icon: Undo, action: () => editor.value.chain().focus().undo().run(), label: 'Undo' },
  { icon: Redo, action: () => editor.value.chain().focus().redo().run(), label: 'Redo' }
]
</script>

<template>
  <div class="wysiwyg-editor border border-white/10 rounded-lg overflow-hidden bg-surface">
    <!-- Toolbar -->
    <div
      v-if="editable"
      class="flex flex-wrap gap-1 p-2 border-b border-white/10 bg-black/20"
      role="toolbar"
      aria-label="Text formatting"
    >
      <template v-for="(btn, index) in toolbarButtons" :key="index">
        <div
          v-if="btn.type === 'divider'"
          class="w-px h-6 bg-white/10 mx-1"
          role="separator"
        />
        <button
          v-else
          type="button"
          :class="[
            'p-2 rounded hover:bg-white/10 transition-colors',
            btn.isActive?.() ? 'bg-white/20 text-cyan-400' : 'text-white/70'
          ]"
          :aria-label="btn.label"
          :aria-pressed="btn.isActive?.()"
          @click="btn.action"
        >
          <component :is="btn.icon" class="w-4 h-4" />
        </button>
      </template>
    </div>

    <!-- Editor Content -->
    <EditorContent
      :editor="editor"
      class="prose prose-invert max-w-none p-4 min-h-[200px] focus:outline-none"
    />
  </div>
</template>

<style>
/* TipTap placeholder styling */
.ProseMirror p.is-editor-empty:first-child::before {
  content: attr(data-placeholder);
  float: left;
  color: #6b7280;
  pointer-events: none;
  height: 0;
}

/* Focus state */
.ProseMirror:focus {
  outline: none;
}
</style>
```

### Phase 7: Router with Lazy Loading

```javascript
/**
 * Vue Router configuration with lazy loading.
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Lazy load views
const LandingPage = () => import('@/views/LandingPage.vue')
const LocationsPage = () => import('@/views/LocationsPage.vue')
const LocationDetailPage = () => import('@/views/LocationDetailPage.vue')
const EventsPage = () => import('@/views/EventsPage.vue')
const ArtistsPage = () => import('@/views/ArtistsPage.vue')
const BlogPage = () => import('@/views/BlogPage.vue')
const LoginPage = () => import('@/views/LoginPage.vue')
const RegisterPage = () => import('@/views/RegisterPage.vue')
const ProfilePage = () => import('@/views/ProfilePage.vue')
const ExclusivePage = () => import('@/views/ExclusivePage.vue')

// Admin views (separate chunk)
const AdminDashboard = () => import(
  /* webpackChunkName: "admin" */
  '@/views/admin/DashboardPage.vue'
)
const AdminLocations = () => import(
  /* webpackChunkName: "admin" */
  '@/views/admin/LocationsAdminPage.vue'
)

const routes = [
  // Public routes
  {
    path: '/',
    name: 'home',
    component: LandingPage,
    meta: { title: 'The Dreamer\'s Cave' }
  },
  {
    path: '/locations',
    name: 'locations',
    component: LocationsPage,
    meta: { title: 'Locations' }
  },
  {
    path: '/locations/:slug',
    name: 'location-detail',
    component: LocationDetailPage,
    props: true,
    meta: { title: 'Location' }
  },
  {
    path: '/events',
    name: 'events',
    component: EventsPage,
    meta: { title: 'Events' }
  },
  {
    path: '/artists',
    name: 'artists',
    component: ArtistsPage,
    meta: { title: 'Artists' }
  },
  {
    path: '/blog',
    name: 'blog',
    component: BlogPage,
    meta: { title: 'Blog' }
  },

  // Auth routes
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
    meta: { title: 'Login', guest: true }
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterPage,
    meta: { title: 'Register', guest: true }
  },

  // Protected routes
  {
    path: '/profile',
    name: 'profile',
    component: ProfilePage,
    meta: { title: 'Profile', requiresAuth: true }
  },
  {
    path: '/exclusive',
    name: 'exclusive',
    component: ExclusivePage,
    meta: { title: 'Exclusive Content', requiresAuth: true, requiresPatreon: true }
  },

  // Admin routes
  {
    path: '/admin',
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'admin-dashboard',
        component: AdminDashboard,
        meta: { title: 'Dashboard' }
      },
      {
        path: 'locations',
        name: 'admin-locations',
        component: AdminLocations,
        meta: { title: 'Manage Locations' }
      }
      // ... more admin routes
    ]
  },

  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundPage.vue'),
    meta: { title: 'Not Found' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    }
    return { top: 0, behavior: 'smooth' }
  }
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Update page title
  document.title = to.meta.title
    ? `${to.meta.title} | The Dreamer's Cave`
    : 'The Dreamer\'s Cave'

  // Auth checks
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }

  if (to.meta.guest && authStore.isAuthenticated) {
    return next({ name: 'home' })
  }

  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return next({ name: 'home' })
  }

  next()
})

export default router
```

### Phase 8: Tailwind Configuration

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}'
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Base dark theme
        bg: 'var(--color-bg, #0a0a0f)',
        surface: 'var(--color-surface, #141420)',
        'text-primary': 'var(--color-text, #ffffff)',
        'text-muted': 'var(--color-text-muted, #a0a0b0)',

        // Dynamic theme colors (from CSS vars)
        primary: 'var(--color-primary, #06b6d4)',
        secondary: 'var(--color-secondary, #8b5cf6)',
        accent: 'var(--color-accent, #22c55e)'
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'system-ui', 'sans-serif']
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite'
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        pulseGlow: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' }
        }
      }
    }
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms')
  ]
}
```

### Phase 9: Accessibility Checklist

Every component MUST include:

```vue
<!-- Accessibility requirements -->

<!-- 1. Keyboard navigation -->
<button
  @click="handleClick"
  @keydown.enter="handleClick"
  @keydown.space.prevent="handleClick"
>

<!-- 2. ARIA labels -->
<button aria-label="Close modal">
  <XIcon aria-hidden="true" />
</button>

<!-- 3. Focus management -->
<div
  ref="modalRef"
  tabindex="-1"
  @vue:mounted="modalRef.focus()"
>

<!-- 4. Screen reader text -->
<span class="sr-only">Loading, please wait</span>

<!-- 5. Reduced motion -->
<style scoped>
@media (prefers-reduced-motion: reduce) {
  .animated-element {
    animation: none;
    transition: none;
  }
}
</style>

<!-- 6. Color contrast (WCAG AA) -->
<!-- Use text-white on dark backgrounds -->
<!-- Use text-black on light backgrounds -->

<!-- 7. Focus visible styles -->
<button class="focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none">
```

### Phase 10: Git Workflow

After frontend code changes:

1. **Lint and format:**
   ```bash
   cd frontend
   npm run lint
   npm run format
   ```

2. **Build check:**
   ```bash
   npm run build
   ```

3. **Review changes:**
   ```bash
   git status && git diff
   ```

4. **Stage and commit:**
   ```bash
   git add frontend/
   git commit -m "feat(frontend): [description]

   - Specific changes made

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

5. **Push (only if explicitly requested)**

## Important Notes

### Code Quality

- ALL code and comments MUST be in English
- Use TypeScript-style JSDoc comments
- Follow Vue 3 style guide
- Use `<script setup>` syntax always
- Validate props with type and validator

### Performance

- Lazy load routes and heavy components
- Use `v-memo` for expensive list rendering
- Cleanup GSAP animations in `onUnmounted`
- Use `shallowRef` for large objects not needing deep reactivity

### Accessibility

- Every interactive element needs keyboard support
- Use semantic HTML elements
- Include ARIA labels for icons and non-text elements
- Support reduced motion preference
- Maintain focus management in modals/dialogs

### Theming

- Use CSS custom properties for dynamic theming
- Always provide fallback values: `var(--color-primary, #06b6d4)`
- Apply location themes via `data-location` attribute
- Dark mode is the default - design for dark first

### Mobile-First

- Start with mobile styles, add breakpoints for larger screens
- Touch targets minimum 44x44px
- Test with touch events, not just click
- Consider thumb zones for mobile navigation

### Animation Guidelines

- Register GSAP plugins once (in main.js or App.vue)
- Always cleanup animations in `onUnmounted`
- Use ScrollTrigger for scroll-based animations
- Respect `prefers-reduced-motion` media query
- Keep animations subtle - max 0.3s for UI, 1s for page transitions
