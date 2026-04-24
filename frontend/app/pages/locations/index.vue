<script setup lang="ts">
import type { Location } from '~/types/location'

const { t } = useI18n()
const localePath = useLocalePath()

const { data: locations, error } = await useFetch<Location[]>('/api/locations', {
  key: 'locations-list',
})

useSeoMeta({
  title: t('locations.title'),
  description: t('locations.seo.description'),
})
</script>

<template>
  <section class="max-w-7xl mx-auto px-6 py-16">
    <h1 class="text-5xl font-display font-bold mb-12">{{ t('locations.title') }}</h1>

    <div v-if="error" role="alert" class="text-error">
      {{ t('locations.error.load_failed') }}: {{ error.statusMessage }}
    </div>

    <div v-else-if="locations && locations.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <article
        v-for="location in locations"
        :key="location.id"
        class="border border-white/10 rounded-lg overflow-hidden hover:border-primary transition-colors"
      >
        <NuxtLink
          :to="localePath(`/locations/${location.slug}`)"
          class="block p-6 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-dark"
        >
          <h2 class="text-2xl font-display font-bold mb-2">{{ location.name }}</h2>
          <p v-if="location.description" class="text-white/70">{{ location.description }}</p>
        </NuxtLink>
      </article>
    </div>

    <div v-else class="text-white/70">
      {{ t('locations.empty') }}
    </div>
  </section>
</template>
