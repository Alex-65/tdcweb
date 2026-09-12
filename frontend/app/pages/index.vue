<script setup lang="ts">
const { t } = useI18n()

useSeoMeta({
  title: t('home.hero_title'),
  description: t('home.seo.description'),
  ogTitle: 'The Dreamer\'s Cave',
  ogDescription: t('home.seo.og_description'),
  ogType: 'website',
})
</script>

<template>
  <section class="relative min-h-screen flex items-center justify-center bg-hero-gradient">
    <div class="absolute inset-0 bg-dark/40 pointer-events-none" aria-hidden="true"></div>
    <div class="relative text-center px-6">
      <h1 class="text-6xl md:text-8xl font-display font-bold mb-6">
        {{ t('home.hero_title') }}
      </h1>
      <p class="text-2xl text-white/80">
        {{ t('home.hero_subtitle') }}
      </p>
    </div>
  </section>
</template>
