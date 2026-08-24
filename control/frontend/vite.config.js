import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy de /api hacia control/backend en desarrollo: evita CORS y hace que
// la cookie de sesión (httpOnly/secure) se vea como same-origin, igual que
// hará nginx en producción (ver spec/control/core.md, "Despliegue").
// El target es configurable vía VITE_PROXY_TARGET porque en el servicio
// docker-compose de desarrollo (control-frontend-dev) el backend se
// resuelve por nombre de servicio (control-backend), no por localhost.
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
