<script setup lang="ts">
const localePath = useLocalePath()
const { locales, locale, setLocale } = useI18n()

const availableLocales = computed(() =>
  (locales.value as { code: string; name: string }[]).filter(l => l.code !== locale.value),
)
</script>

<template>
  <header class="sticky top-0 z-40 bg-dark/90 backdrop-blur border-b border-white/10">
    <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
      <NuxtLink :to="localePath('/')" class="text-2xl font-display font-bold">
        The Dreamer's Cave
      </NuxtLink>

      <nav class="hidden md:flex items-center gap-8">
        <NuxtLink :to="localePath('/locations')" class="hover:text-primary transition-colors" active-class="text-primary font-bold">{{ $t('nav.locations') }}</NuxtLink>
        <NuxtLink :to="localePath('/events')" class="hover:text-primary transition-colors" active-class="text-primary font-bold">{{ $t('nav.events') }}</NuxtLink>
        <NuxtLink :to="localePath('/artists')" class="hover:text-primary transition-colors" active-class="text-primary font-bold">{{ $t('nav.artists') }}</NuxtLink>
        <NuxtLink :to="localePath('/blog')" class="hover:text-primary transition-colors" active-class="text-primary font-bold">{{ $t('nav.blog') }}</NuxtLink>
      </nav>

      <div class="flex items-center gap-4">
        <select
          :value="locale"
          class="bg-transparent border border-white/20 rounded px-2 py-1 text-sm"
          @change="(e) => setLocale((e.target as HTMLSelectElement).value as typeof locale)"
        >
          <option :value="locale">{{ locale.toUpperCase() }}</option>
          <option v-for="l in availableLocales" :key="l.code" :value="l.code">
            {{ l.code.toUpperCase() }}
          </option>
        </select>

        <NuxtLink
          :to="localePath('/auth/login')"
          class="px-4 py-2 border border-primary text-primary hover:bg-primary hover:text-white rounded transition-colors text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-dark"
        >
          {{ $t('nav.login') }}
        </NuxtLink>
      </div>
    </div>
  </header>
</template>
