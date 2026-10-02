<script setup lang="ts">
import type { Event } from '~/types/event'

const { t } = useI18n()

const { data: events, error } = await useApiFetch<Event[]>('/api/events', {
  key: 'events-list',
  query: { upcoming: 'true' },
})

useSeoMeta({
  title: t('events.title'),
  description: t('events.seo.description'),
})
</script>

<template>
  <section class="max-w-7xl mx-auto px-6 py-16">
    <h1 class="text-5xl font-display font-bold mb-12">{{ t('events.title') }}</h1>

    <div v-if="error" role="alert" class="text-error">
      {{ t('events.error.load_failed') }}: {{ error.statusMessage }}
    </div>

    <ul v-else-if="events && events.length" class="space-y-4">
      <li
        v-for="event in events"
        :key="event.id"
        class="border border-white/10 rounded-lg p-6"
      >
        <h2 class="text-2xl font-display font-bold mb-1">{{ event.title }}</h2>
        <time :datetime="event.starts_at" class="text-white/60 text-sm">{{ event.starts_at }}</time>
      </li>
    </ul>

    <div v-else class="text-white/70">
      {{ t('events.empty') }}
    </div>
  </section>
</template>
