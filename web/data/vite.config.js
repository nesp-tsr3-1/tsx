import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  test: {
    environment: "jsdom",
  },
  base: '/data/',
  build: {
    sourcemap: true
  },
  server: {
    port: 3000
  }
})
