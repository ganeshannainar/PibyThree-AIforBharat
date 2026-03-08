import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3007,
    watch: {
      usePolling: true,
      interval: 1000
    },
    proxy: {
      '/api': {
        target: 'http://13.201.63.10:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/static': {
        target: 'http://13.201.63.10:8000',
        changeOrigin: true
      },
      '/products': {
        target: 'http://13.201.63.10:8000',
        changeOrigin: true
      }
    }
  }
})
