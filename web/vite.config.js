import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'multi-entry-point-server',
      configureServer(server) {
        // Hack to get dev server to work with multiple entry points
        server.middlewares.use((req, res, next) => {
          if(req.url.startsWith("/data/")) {
            req.url = "/data/"
          }
          if(req.url.startsWith("/tsx/")) {
            req.url = "/tsx/"
          }
          next()
        })
      }
    }
  ],
  appType: 'mpa',
  base: '/',
  build: {
   sourcemap: true,
   rollupOptions: {
      input: {
        tsx: resolve(__dirname, 'tsx/index.html'),
        data: resolve(__dirname, 'data/index.html')
      }
    }
  },
})
