import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The dev server proxies /api to the backend so the browser only ever talks to
// one origin. Nginx does the same job in the production image (M4) and the
// Kubernetes Ingress does it in the cluster (M8). Because of this the frontend
// never needs to know the backend's address, and no CORS preflight happens.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': { target: 'http://localhost:8001', changeOrigin: true },
      '/health': { target: 'http://localhost:8001', changeOrigin: true },
    },
  },
  build: { outDir: 'dist', sourcemap: false },
})
