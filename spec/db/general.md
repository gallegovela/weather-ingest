# Construcción de la base de datos (PostgreSQL + Alembic)

Este documento describe cómo se construye y versiona el esquema de
la base de datos del proyecto. Complementa a
[`spec/db/tables.md`](./tables.md), donde se documenta el diseño de
cada tabla: aquí se documenta el **mecanismo** (herramienta, rutas,
convenciones y flujo de trabajo), no el contenido de las tablas.

## Motor de base de datos

- **Motor:** PostgreSQL.
- **Herramienta de migraciones:** [Alembic](https://alembic.sqlalchemy.org/),
  usado en modo **SQL puro** (migraciones escritas a mano con
  `op.execute(...)` / helpers de `alembic.op`), **sin** necesidad de
  definir modelos ORM de SQLAlchemy. Alembic se usa únicamente como
  motor de versionado y aplicación de migraciones.

## Independencia respecto al resto de la aplicación

La construcción de la base de datos es un módulo **autocontenido**,
independiente del código de ingesta (scripts de importación). Vive
en su propia carpeta en la raíz del proyecto y no comparte código,
dependencias de import ni ciclo de vida con el resto de la app: se
puede crear/migrar la base de datos sin ejecutar ni importar nada
del resto del proyecto, y viceversa.

## Estructura de directorios

Todas las rutas son relativas a la raíz del proyecto
(`/var/www/weather`):

```
db/                             # Módulo independiente de construcción de BD
├── alembic.ini                 # Configuración de Alembic (lee DATABASE_URL del entorno)
├── requirements.txt            # Dependencias propias de este módulo (alembic, psycopg, python-dotenv)
├── migrate.py                  # Script de actualización (wrapper de entrada, ver más abajo)
└── migrations/
    ├── env.py                  # Entry point de Alembic: conexión a BD y contexto de migración
    ├── script.py.mako          # Plantilla usada al generar nuevas migraciones
    └── versions/                # Una tabla/cambio documentado en spec/db/tables.md = una migración
        ├── 20260822_1030_a1b2c3_create_estaciones.py
        └── ...
```

- `db/` es hermana de `spec/`, `.env`, `CLAUDE.md`, etc. en la raíz
  del proyecto — no cuelga de ningún futuro `src/` de la aplicación.
- `db/requirements.txt` se mantiene separado del/los `requirements.txt`
  de la app de ingesta, precisamente para que este módulo pueda
  instalarse y ejecutarse de forma aislada (por ejemplo, en un paso
  de despliegue distinto).

## Variables de entorno

Se reutiliza el mismo `.env` de la raíz del proyecto (no versionado).
Nuevas variables necesarias para este módulo:

| Variable       | Descripción                                              | Ejemplo                                              |
|----------------|-----------------------------------------------------------|-------------------------------------------------------|
| `DATABASE_URL` | Cadena de conexión a PostgreSQL usada por Alembic y por la app | `postgresql+psycopg://weather:******@localhost:5432/weather` |

**Nota sobre el esquema de la URL:** se usa `postgresql+psycopg://`
(no `postgresql://` a secas). SQLAlchemy elige `psycopg2` por defecto
para el esquema genérico `postgresql://`, y este proyecto usa
`psycopg` v3 (ver más abajo), que no está instalado — hay que ser
explícitos con el sufijo `+psycopg` del dialecto.

`db/alembic.ini` no contiene la cadena de conexión en claro: `env.py`
la lee de `DATABASE_URL` (cargando `.env` con `python-dotenv`) y se la
pasa a Alembic en tiempo de ejecución.

## Convenciones de nombres

### Tablas

- Minúsculas, en español, `snake_case`, en **plural** (ej.
  `estaciones`, `valores_climatologicos`).
- Nombre de la tabla = concepto de negocio, sin prefijos técnicos
  (nada de `tbl_`, `t_`, etc.).

### Columnas

- Minúsculas, en español, `snake_case`.
- **Clave primaria natural**: cuando el origen de datos ya trae un
  identificador estable y único (ej. `indicativo` de AEMET en
  `estaciones`), se usa esa columna como clave primaria en vez de
  crear un `id` artificial.
- **Clave primaria técnica**: si no existe una clave natural clara,
  se usa `id BIGINT GENERATED ALWAYS AS IDENTITY` (o `BIGSERIAL`).
- **Claves foráneas**: `<tabla_singular>_<columna_referenciada>`
  (ej. una futura tabla que referencie a `estaciones` usaría
  `estacion_indicativo`).
- **Columnas de auditoría** (obligatorias en toda tabla alimentada
  por un proceso de importación): `fecha_alta` (timestamp de primera
  inserción) y `fecha_actualizacion` (timestamp de la última
  sincronización), tal como se define en `spec/db/tables.md`.

### Índices y constraints

- Nombre de índice: `ix_<tabla>_<columna(s)>`.
- Nombre de constraint única: `uq_<tabla>_<columna(s)>`.
- Nombre de foreign key: `fk_<tabla_origen>_<tabla_destino>`.

### Ficheros de migración

- Se genera con `alembic revision -m "create_estaciones"` (o el
  wrapper `migrate.py new "create_estaciones"`, ver más abajo).
- Plantilla de nombre de fichero (configurada en `alembic.ini` vía
  `file_template`):
  `%%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s`
  → ejemplo: `20260822_1030_a1b2c3_create_estaciones.py`.
- Esto da nombres ordenables cronológicamente en el listado de
  directorio, además del hash de revisión (`rev`) que Alembic
  necesita internamente para el encadenado de migraciones.
- **Una migración = un cambio de esquema con entidad propia**: crear
  una tabla, añadir una columna, crear un índice... No se agrupan
  cambios sin relación en una misma migración.

## Script de actualización (`db/migrate.py`)

Wrapper de línea de comandos, pensado para no tener que recordar la
sintaxis completa de `alembic` ni sus flags de configuración:

| Comando                          | Equivale a                          | Uso                                                  |
|-----------------------------------|--------------------------------------|-------------------------------------------------------|
| `python db/migrate.py upgrade`    | `alembic -c db/alembic.ini upgrade head` | Aplica todas las migraciones pendientes.         |
| `python db/migrate.py downgrade`  | `alembic -c db/alembic.ini downgrade -1` | Revierte la última migración aplicada.           |
| `python db/migrate.py new "<mensaje>"` | `alembic -c db/alembic.ini revision -m "<mensaje>"` | Crea un nuevo fichero de migración vacío en `versions/`. |
| `python db/migrate.py current`    | `alembic -c db/alembic.ini current`  | Muestra la última migración aplicada en la BD actual. |
| `python db/migrate.py history`    | `alembic -c db/alembic.ini history`  | Lista el histórico completo de migraciones.          |

Este script es el único punto de entrada recomendado para tocar el
esquema; se evita ejecutar `alembic` directamente para no olvidar el
flag `-c db/alembic.ini` (el fichero de configuración no está en la
raíz del proyecto, sino dentro de `db/`).

## Flujo de trabajo para añadir/cambiar una tabla

1. Documentar (o actualizar) la tabla en `spec/db/tables.md`
   primero: columnas, tipos, claves, notas de diseño.
2. Generar la migración: `python db/migrate.py new "create_<tabla>"`.
3. Escribir el `upgrade()` (DDL de creación/alteración) y el
   `downgrade()` (DDL inverso) en el fichero generado, usando SQL
   puro (`op.execute(...)`) o los helpers de `alembic.op`
   (`op.create_table`, `op.add_column`, etc.) — ambos son válidos,
   se prioriza la claridad.
4. Aplicar la migración en local: `python db/migrate.py upgrade`.
5. Verificar con `python db/migrate.py current`.

## Construcción incremental

El esquema completo de la base de datos nunca se define de golpe:
se construye **exclusivamente** mediante la secuencia ordenada de
migraciones en `db/migrations/versions/`. Levantar una base de datos
nueva desde cero consiste siempre en el mismo comando
(`python db/migrate.py upgrade`), que reproduce el esquema aplicando
todas las migraciones en orden. No se crean tablas ni se aplican
cambios de esquema a mano ni por ningún otro medio.

## Estado de implementación

El módulo `db/` ya está implementado siguiendo esta especificación:
`db/alembic.ini`, `db/migrate.py`, `db/migrations/env.py`,
`db/migrations/script.py.mako` y `db/migrations/versions/`.
Dependencias instaladas en un entorno virtual propio del proyecto
(`.venv/`, no versionado) a partir de `db/requirements.txt`.

**Driver de conexión elegido:** `psycopg` v3 (paquete `psycopg[binary]`),
por ser el driver activamente mantenido y recomendado por SQLAlchemy
para PostgreSQL (`psycopg2` está en modo de mantenimiento).

Ya existe la primera migración real,
`create_estaciones`, que crea la tabla `estaciones` (ver
`spec/db/tables.md`). El servidor PostgreSQL de desarrollo se levanta
con `docker-compose.yml` (raíz del proyecto), con credenciales que
coinciden con `DATABASE_URL` en `.env`. Aún no hay un servidor de
producción.

## Entornos, permisos y backups — decidido

- **Gestión de entornos:** un único `DATABASE_URL` activo vía `.env`,
  sin soporte de múltiples entornos dentro del mismo `alembic.ini`.
  Local hoy, producción cuando exista un servidor; si en el futuro se
  necesita una base de datos de test, se resuelve con un `.env.test`
  cargado explícitamente, sin que "entorno" sea un concepto que
  Alembic tenga que conocer.
- **Usuario y permisos de PostgreSQL:** un único usuario compartido
  entre migraciones y aplicación (el mismo que ya usa
  `docker-compose.yml`, `weather`/`weather` en local). No se separa un
  usuario con privilegios de DDL de otro de solo lectura/escritura en
  runtime: esa separación no se justifica sin varios desarrolladores
  operando sobre la base de datos ni un requisito explícito de mínimo
  privilegio.
- **Backups:** no se implementa ninguna estrategia de backup/restore
  por ahora. Los datos del proyecto son recuperables (reimportables
  desde la API de AEMET), así que no se justifica esa complejidad
  adicional en este momento.
- **Servidor PostgreSQL de producción:** mismo patrón que en local —
  un contenedor `postgres` más añadido al `docker-compose.yml` del
  servidor de destino, coherente con la decisión de contenedorizar
  `control/backend/` y `control/frontend/` (ver
  [`spec/control/core.md`](../control/core.md)), no un servicio
  gestionado externo (RDS, Cloud SQL, etc.).
