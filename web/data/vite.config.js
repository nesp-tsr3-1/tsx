import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  base: '/data/',
  build: {
   sourcemap: true,
  },
  server: {
    port: 3000
  },
})
