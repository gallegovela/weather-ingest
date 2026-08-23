# control/frontend

SPA en React (Vite) del panel de control. Ver
[`spec/control/core.md`](../../spec/control/core.md) y
[`spec/control/module/`](../../spec/control/module/) para la especificación
completa.

## Desarrollo

```
npm install
npm run dev
```

El servidor de desarrollo de Vite expone un proxy de `/api` hacia
`control/backend/` (`http://localhost:8000`, ver `vite.config.js`), así
que hay que tener el backend arrancado en paralelo (`cd ../backend &&
uvicorn main:app --reload`).

## Build de producción

```
npm run build
```
