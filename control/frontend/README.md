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

### Alternativa sin node local: Docker

Si no se quiere instalar node en la máquina, el servicio
`control-frontend-dev` del `docker-compose.yml` de la raíz levanta el
mismo servidor de desarrollo de Vite (con hot-reload, montando este
directorio como volumen) dentro de un contenedor:

```
docker compose --profile dev up control-frontend-dev
```

Expone la SPA en `http://localhost:5173`. El backend (`control-backend`)
tiene que estar arrancado en paralelo (contenedor o local); el proxy de
`/api` apunta al contenedor `control-backend` en vez de `localhost`
cuando se ejecuta así (ver `VITE_PROXY_TARGET` en `docker-compose.yml`).

## Build de producción

```
npm run build
```
