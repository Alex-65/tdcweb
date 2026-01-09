import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    port: 9503,
    host: '0.0.0.0',
    strictPort: true,

    // Proxy API requests to Flask backend
    proxy: {
      '/api': {
        target: 'http://localhost:9502',
        changeOrigin: true,
        secure: false,
      },
    },

    // HMR configuration
    hmr: {
      overlay: true,
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['vue', 'vue-router', 'pinia'],
          'gsap': ['gsap'],
        },
      },
    },
  },

  // Environment variable prefix
  envPrefix: 'VITE_',
})
