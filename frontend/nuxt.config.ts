import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  compatibilityDate: '2026-04-01',

  future: {
    compatibilityVersion: 4,
  },

  modules: [
    '@nuxtjs/i18n',
    '@pinia/nuxt',
    '@vueuse/nuxt',
    '@nuxt/image',
    '@nuxtjs/seo',
    '@nuxtjs/robots',
    '@nuxtjs/sitemap',
  ],

  devtools: { enabled: true },

  // Tailwind CSS v4 via the official Vite plugin (CSS-first config).
  // The old `@nuxtjs/tailwindcss` module targets Tailwind v3 and conflicts
  // with v4 hoisted by @nuxt/ui / nuxt-og-image. See TECH_DEBT TD-006.
  vite: {
    plugins: [tailwindcss()],
  },

  css: ['~/assets/css/main.css'],

  // Flat component naming regardless of subfolder. `common/AppHeader.vue`
  // registers as `<AppHeader />`, not `<CommonAppHeader />`. Required for
  // `app/layouts/default.vue` (Task 3.2) to resolve `<AppHeader />` and
  // `<AppFooter />` at their planned `app/components/common/` locations.
  components: [
    { path: '~/components', pathPrefix: false },
  ],

  typescript: {
    strict: true,
    typeCheck: false, // CI job only; don't slow dev HMR
  },

  runtimeConfig: {
    flaskUrl: process.env.NUXT_FLASK_URL || 'http://localhost:9502',
    cookieSecret: process.env.NUXT_COOKIE_SECRET || 'dev-insecure-change-me',
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || '/api',
      siteUrl: process.env.NUXT_PUBLIC_SITE_URL || 'http://localhost:9503',
    },
  },

  nitro: {
    devProxy: {
      '/api': {
        target: process.env.NUXT_FLASK_URL || 'http://localhost:9502',
        changeOrigin: true,
      },
    },
    prerender: {
      crawlLinks: true,
      routes: ['/sitemap.xml'],
      failOnError: false,
    },
  },

  routeRules: {
    '/':                 { prerender: true },
    '/locations':        { prerender: true },
    '/locations/**':     { prerender: true },
    '/artists':          { prerender: true },
    '/artists/**':       { prerender: true },
    '/about':            { prerender: true },
    '/contact':          { prerender: true },

    '/events':           { swr: 300 },
    '/events/**':        { swr: 300 },
    '/blog':             { swr: 3600 },
    '/blog/**':          { swr: 3600 },

    '/auth/login':       { ssr: true, swr: false },
    '/auth/register':    { ssr: true, swr: false },
    '/auth/callback/**': { ssr: true, swr: false },

    '/dashboard':        { ssr: false },
    '/dashboard/**':     { ssr: false },
    '/admin':            { ssr: false },
    '/admin/**':         { ssr: false },

    '/**':               { ssr: true },
  },

  i18n: {
    locales: [
      { code: 'en', language: 'en-US', file: 'en.json', name: 'English' },
      { code: 'it', language: 'it-IT', file: 'it.json', name: 'Italiano' },
      { code: 'fr', language: 'fr-FR', file: 'fr.json', name: 'Français' },
      { code: 'es', language: 'es-ES', file: 'es.json', name: 'Español' },
    ],
    defaultLocale: 'en',
    strategy: 'prefix_except_default',
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: 'i18n_redirected',
      redirectOn: 'root',
      alwaysRedirect: false,
    },
    langDir: 'locales',
  },

  robots: {
    disallow: ['/dashboard', '/admin', '/api/auth'],
  },

  devServer: {
    host: '0.0.0.0',
    port: 9503,
  },
})
