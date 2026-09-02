import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      // Proxy /api to backend in dev mode (when not using mocks)
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  define: {
    // Make env variables available to browser code
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
  },
})
