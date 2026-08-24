import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// /api proxy to control/backend in development: avoids CORS and makes
// the session cookie (httpOnly/secure) look same-origin, same as nginx
// will do in production (see spec/control/core.md, "Deployment").
// The target is configurable via VITE_PROXY_TARGET because in the
// development docker-compose service (control-frontend-dev) the
// backend resolves by service name (control-backend), not localhost.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      "/api": {
        target: process.env.VITE_PROXY_TARGET || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
})
