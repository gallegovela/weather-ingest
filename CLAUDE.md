# weather

## Especificación del proyecto

Toda la especificación y definición detallada del proyecto (scripts
de importación, tablas de base de datos, y lo que se vaya añadiendo)
está documentada en los ficheros `.md` dentro de las distintas
secciones de la carpeta `spec/` (ej. `spec/importa/`, `spec/db/`).

**Antes de trabajar en cualquier parte del proyecto hay que revisar
por completo esta documentación** para tener una visión completa y
actualizada del proyecto, no solo la sección que parezca relevante
a simple vista.

## Resumen del proyecto

App en Python que importa información meteorológica desde una API externa
(script/job de ingesta). El objetivo, alcance detallado y destino de los
datos se irán definiendo en este documento a medida que avancemos.

- **Tipo de app:** script / job de ingesta (no es un servicio web por ahora)
- **Lenguaje:** Python
- **API de origen:** TBD — pendiente de elegir (ej. OpenWeatherMap, AEMET,
  Open-Meteo, etc.)
- **Destino de los datos:** TBD — ¿archivo, base de datos, otro sistema?
- **Frecuencia de ingesta:** TBD — ¿bajo demanda, cron, scheduler?

## Estructura del proyecto

```
db/                  # Módulo autocontenido de construcción de BD (Alembic).
                     # Ver spec/db/general.md.
importa/             # Scripts de ingesta (uno por recurso de origen).
├── requirements.txt # Dependencias propias del módulo de ingesta.
├── config.py        # Carga de .env (AEMET_API_KEY, DATABASE_URL).
├── aemet_client.py  # Cliente genérico del patrón de dos pasos de AEMET.
├── db.py            # Conexión psycopg (SQL puro, sin ORM).
└── estaciones.py     # Job: inventario de estaciones (spec/importa/ESTACIONES.md).
control/             # Panel de control (SPA + API). Ver spec/control/.
├── backend/          # API FastAPI (capas servicio + DAO), entorno virtual
│                     # y requirements.txt propios, independiente del resto.
│   ├── main.py        # Arranque FastAPI, monta el router de cada módulo.
│   ├── core/           # Transversal: config (.env), conexión a Postgres,
│                       # validación de sesión (core/auth.py).
│   └── modulos/        # Un módulo = una carpeta (seguridad, estaciones, ...),
│                       # cada una con router.py/servicio.py/dao.py/esquemas.py.
└── frontend/         # SPA React (Vite), node_modules propio, independiente.
    ├── vite.config.js  # Proxy de /api hacia control/backend en desarrollo.
    └── src/
        ├── app/         # Transversal: Layout (menú lateral), Login,
        │                # RequireAuth (guard de sesión), apiClient.
        └── modulos/      # Un módulo = una carpeta (seguridad, estaciones, ...),
                          # con sus pantallas y su <modulo>Api.js.
spec/                # Especificación del proyecto (ver arriba).
docker-compose.yml   # PostgreSQL local de desarrollo.
.env                 # Variables de entorno (no versionado).
```

Cada job de importación futuro (valores climatológicos diarios, etc.)
añade su propio módulo dentro de `importa/`, reutilizando
`aemet_client.py` y `db.py`. Cada módulo futuro del panel de control
añade su propia carpeta dentro de `control/backend/modulos/` y
`control/frontend/src/modulos/`, siguiendo el patrón fijado por el
módulo `estaciones` (ver `spec/control/core.md`).

## Setup / entorno

- **Gestor de dependencias:** `pip` + `venv` (un único `.venv/` en la
  raíz del proyecto para `db/`/`importa/`, no versionado).
  `control/backend/` tiene su propio `.venv/` independiente (ver
  `spec/control/core.md`), también no versionado. `control/frontend/`
  usa `npm` con su propio `node_modules/` (no versionado).
- **Variables de entorno** (fichero `.env` en la raíz, no versionado,
  compartido por `db/`, `importa/` y `control/backend/`):
  - `AEMET_API_KEY` — API key de AEMET OpenData.
  - `DATABASE_URL` — cadena de conexión a PostgreSQL, formato
    SQLAlchemy con el driver `psycopg` v3 explícito:
    `postgresql+psycopg://usuario:password@host:5432/bd`.
  - `CONTROL_SESSION_TTL_MINUTOS` — minutos de validez de una sesión
    del panel de control desde el login, sin renovación (por defecto
    `15` si no se define — ver `spec/control/core.md`).
- **Base de datos local:** `docker-compose.yml` levanta un PostgreSQL
  de desarrollo con las credenciales que ya están en `.env`
  (`weather`/`weather`/`weather`). Arrancar con `docker compose up -d`.
- **Instalación de dependencias:**
  ```
  source .venv/bin/activate
  pip install -r db/requirements.txt
  pip install -r importa/requirements.txt
  ```
  Para `control/backend/` (entorno virtual propio):
  ```
  cd control/backend
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
  Para `control/frontend/`:
  ```
  cd control/frontend
  npm install
  ```

## Comandos habituales

- `docker compose up -d` — levantar PostgreSQL local.
- `python db/migrate.py upgrade` — aplicar migraciones pendientes
  (ver `spec/db/general.md` para el resto de comandos de `migrate.py`).
- `python -m importa.estaciones` — importar/actualizar el inventario
  de estaciones climatológicas de AEMET.
- `cd control/backend && uvicorn main:app --reload` — arrancar la API
  del panel de control en desarrollo (con el `.venv` propio de
  `control/backend/` activado).
- `cd control/frontend && npm run dev` — arrancar la SPA del panel de
  control en desarrollo (necesita el backend arrancado en paralelo,
  ver `control/frontend/README.md`). Alternativa sin node local:
  `docker compose --profile dev up control-frontend-dev`.
- `docker compose build control-frontend` — construir la imagen de
  producción del frontend (build de Vite + nginx) sin necesitar node
  en local.

## Convenciones de código

- Español para nombres de tablas/columnas y para la documentación en
  `spec/`; el código Python (módulos, funciones, variables) también en
  español, siguiendo el dominio del proyecto.
- Cada script de importación es responsable de su propia transformación
  y carga (upsert); no hay ORM ni modelos compartidos con `db/`
  (que solo gestiona el esquema vía migraciones, ver
  `spec/db/general.md`).
- SQL puro con parámetros nombrados (`%(clave)s` de psycopg), sin
  query builders.

## Notas sobre la API externa

- **AEMET OpenData**, autenticación por cabecera `api_key`
  (`AEMET_API_KEY`).
- Patrón de dos pasos (petición inicial → URL temporal `datos` →
  contenido real) y codificación `ISO-8859-15` en la respuesta de
  datos: ver `spec/importa/ESTACIONES.md` para el detalle, encapsulado
  en `importa/aemet_client.py`.

## Decisiones y contexto adicional

- **PostgreSQL local vía Docker Compose** (`docker-compose.yml`, raíz
  del proyecto): no hay servidor de producción todavía, así que el
  entorno de desarrollo se levanta con un contenedor cuyas credenciales
  coinciden con `DATABASE_URL` en `.env`.
- **`DATABASE_URL` usa el esquema `postgresql+psycopg://`** (no
  `postgresql://` a secas): SQLAlchemy/Alembic necesitan el sufijo de
  dialecto para elegir el driver `psycopg` v3 en vez de `psycopg2`
  (que no está instalado).
- **Primera migración creada**: `create_estaciones`
  (`db/migrations/versions/20260822_2051_f54155bc39b7_create_estaciones.py`),
  con `latitud_decimal`/`longitud_decimal` como `NUMERIC(9,6)`
  (precisión suficiente para coordenadas en grados decimales).
- **Ingesta sin ORM ni SQLAlchemy**: `importa/` usa `psycopg` v3
  directamente con SQL puro (`INSERT ... ON CONFLICT`), independiente
  de `db/` (que solo gestiona el esquema).
- **Librería HTTP:** `requests`, por simplicidad (script síncrono, sin
  necesidad de concurrencia).
