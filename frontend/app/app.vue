<script setup lang="ts">
useHead({
  titleTemplate: (title) => (title ? `${title} — The Dreamer's Cave` : `The Dreamer's Cave — You Can See The Music`),
  htmlAttrs: { lang: 'en' },
  link: [{ rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }],
})

useSeoMeta({
  ogSiteName: "The Dreamer's Cave",
  twitterCard: 'summary_large_image',
})
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
