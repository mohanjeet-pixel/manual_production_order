import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/login':    { target: 'http://localhost:8000', changeOrigin: true },
      '/orders':   { target: 'http://localhost:8000', changeOrigin: true },
      '/batches':  { target: 'http://localhost:8000', changeOrigin: true },
      '/products': { target: 'http://localhost:8000', changeOrigin: true },
      '/approve':  { target: 'http://localhost:8000', changeOrigin: true },
      '/reject':   { target: 'http://localhost:8000', changeOrigin: true },
      '/health':   { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
