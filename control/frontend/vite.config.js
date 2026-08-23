import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy de /api hacia control/backend en desarrollo: evita CORS y hace que
// la cookie de sesión (httpOnly/secure) se vea como same-origin, igual que
// hará nginx en producción (ver spec/control/core.md, "Despliegue").
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
})
