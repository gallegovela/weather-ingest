# control/frontend

React SPA (Vite) for the control panel. See
[`spec/control/core.md`](../../spec/control/core.md) and
[`spec/control/module/`](../../spec/control/module/) for the full
specification.

## Development

```
npm install
npm run dev
```

Vite's dev server exposes an `/api` proxy to `control/backend/`
(`http://localhost:8000`, see `vite.config.js`), so the backend needs
to be running in parallel (`cd ../backend && uvicorn main:app --reload`).

### Alternative without local node: Docker

If you don't want to install node on the machine, the
`control-frontend-dev` service in the root `docker-compose.yml` starts
the same Vite dev server (with hot-reload, mounting this directory as
a volume) inside a container:

```
docker compose --profile dev up control-frontend-dev
```

Exposes the SPA at `http://localhost:5173`. The backend
(`control-backend`) needs to be running in parallel (container or
local); the `/api` proxy points to the `control-backend` container
instead of `localhost` when run this way (see `VITE_PROXY_TARGET` in
`docker-compose.yml`).

## Production build

```
npm run build
```
