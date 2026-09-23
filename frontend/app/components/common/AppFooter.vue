<script setup lang="ts">
// Computed at script-setup time (both SSR and client). On the server this
// runs at request time; on the client it runs at hydration time. For the
// overwhelming majority of the year the two agree. The 1-second window at
// midnight on 31 Dec -> 1 Jan where they could differ is an accepted edge
// per CLAUDE.md SSR Rule #4 discussion; fixing requires either app-config
// hardcoding (yearly maintenance) or a build-time constant baked in.
const year = new Date().getFullYear()
</script>

<template>
  <footer class="border-t border-white/10 bg-dark">
    <div class="max-w-7xl mx-auto px-6 py-8 text-sm text-white/70">
      <div class="flex flex-col md:flex-row justify-between gap-4">
        <div>© {{ year }} The Dreamer's Cave</div>
        <div class="italic">{{ $t('home.hero_title') }}</div>
      </div>
    </div>
  </footer>
</template>
