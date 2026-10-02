<script setup lang="ts">
import type { NuxtError } from '#app'

defineProps<{ error: NuxtError }>()
const handleError = () => clearError({ redirect: '/' })
</script>

<template>
  <main class="min-h-screen flex items-center justify-center bg-dark text-white">
    <div class="text-center px-6" role="alert">
      <h1 class="text-6xl font-display font-bold mb-4">{{ error.statusCode }}</h1>
      <p class="text-xl mb-8">{{ error.statusMessage || $t('errors.message_fallback') }}</p>
      <button
        class="px-6 py-3 bg-primary hover:bg-secondary rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-dark focus-visible:outline-none"
        @click="handleError"
      >
        {{ $t('errors.back_to_home') }}
      </button>
    </div>
  </main>
</template>
