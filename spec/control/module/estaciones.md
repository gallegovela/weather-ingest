# Módulo: Estaciones

Primer módulo funcional del panel (más allá de `seguridad`, que es
especial y transversal — ver [`spec/control/core.md`](../core.md)).
**Es el módulo de referencia**: el patrón que fije aquí (capas,
listado paginado con filtros, consumo de la API desde React, mapa)
es el que se reutiliza al construir el resto de módulos.

## Objetivo

Permitir consultar el inventario de estaciones climatológicas ya
importado por `importa/estaciones.py` en la tabla `estaciones` (ver
[`spec/db/tables.md`](../../db/tables.md)), tanto en forma de listado
como visualmente en un mapa. Es un módulo de **solo consulta**: no
permite crear, editar ni eliminar estaciones desde el panel (esos
datos los gestiona el importador, no el panel de control).

## Menú

Dos entradas de primer nivel del módulo "Estaciones" en el menú
lateral (ver "Estructura de la aplicación" en `core.md`):

1. **Listado** — tabla paginada con filtros.
2. **Mapa** — mapa con las estaciones geolocalizadas.

## Pantallas

### 1. Listado de estaciones

- **Tabla paginada** con todas las estaciones de la tabla
  `estaciones`.
- **Filtro por cada campo** de la tabla, siguiendo la convención
  transversal fijada en `core.md` ("Listados paginados con filtros"):
  - Texto (`indicativo`, `nombre`, `provincia`, `indsinop`): filtro
    "contiene".
  - Numéricos (`altitud`, `latitud_decimal`, `longitud_decimal`):
    filtro por rango (mínimo/máximo).
  - Fechas (`fecha_alta`, `fecha_actualizacion`): filtro por rango de
    fechas.
  - `latitud`/`longitud` (texto original `GGMMSSH` de AEMET): filtro
    "contiene", igual que el resto de campos de texto.
- **Columnas responsive con fila expandible — decidido.** Todas las
  columnas de `estaciones` (ver `spec/db/tables.md`) están
  disponibles, pero según el ancho de pantalla la tabla oculta
  automáticamente las columnas que no caben (en vez de forzar scroll
  horizontal) — mismo comportamiento que la extensión *Responsive* de
  DataTables.js. Cada fila tiene un control de expandir (`+`) que,
  al pulsarlo, despliega los valores de las columnas ocultas en ese
  momento para esa fila. Qué columnas se ocultan primero no es una
  lista fija: depende del ancho disponible (se prioriza mantener
  visibles `indicativo`, `nombre` y `provincia`).

### 2. Mapa de estaciones

- Mapa con un **punto/marcador por estación**, posicionado con
  `latitud_decimal`/`longitud_decimal`.
- Al pinchar sobre un marcador se muestran los **detalles de esa
  estación** (los mismos campos que en el listado), para poder
  identificarla/consultarla sin salir del mapa.
- **Proveedor de mapa — decidido: OpenStreetMap**, mediante
  **Leaflet** (`react-leaflet`) como librería de mapas en
  `control/frontend/`. Se elige por ser gratuito y no requerir API
  key ni cuenta de facturación (a diferencia de Google Maps), a
  diferencia de Mapbox u otras opciones con cuota gratuita limitada.
- **Agrupación de marcadores (*clustering*) — decidido:** con las
  ~921 estaciones repartidas por España, a niveles de zoom alejados
  muchos marcadores quedarían solapados/amontonados. Se usa
  `react-leaflet-cluster` para agrupar marcadores próximos en un
  único círculo con el número de estaciones que contiene; al hacer
  zoom o pinchar sobre el grupo, se desglosa en los marcadores
  individuales.

## Datos

Sigue la arquitectura en capas de `core.md`:

- **DAO** (`control/backend/modulos/estaciones/dao.py`): consulta
  `SELECT` sobre la tabla `estaciones`, con paginación (`LIMIT`/
  `OFFSET`) y los filtros recibidos, en SQL puro (`psycopg` v3, sin
  ORM — mismo criterio que `importa/`).
- **Servicio** (`servicio.py`): valida los parámetros de filtro/
  paginación recibidos y delega en el DAO; no contiene lógica de
  negocio adicional más allá de eso, al ser un módulo de solo
  consulta.
- **Control** (`router.py`): expone los endpoints de la API.

### Endpoints (API REST)

Siguiendo el contrato fijado en `core.md`:

- `GET /api/estaciones/estaciones` — listado paginado y filtrado
  (parámetros `pagina`, `tamano_pagina`, y uno por campo filtrable
  según la convención transversal).
- **El mapa reutiliza el mismo endpoint, sin paginar — decidido.**
  Con `pagina`/`tamano_pagina` omitidos (o un valor que devuelva
  todas las filas), el mapa pide el conjunto completo de estaciones
  de una sola vez: con ~921 filas actuales no es un volumen que
  justifique paginar la petición del mapa. No se crea un endpoint
  propio para el mapa.

## Pendiente de definir

Sin pendientes abiertos en este módulo. El mapa **no lleva caja de
búsqueda propia** (decidido): pinchar sobre el marcador es suficiente
para consultar una estación, dado el volumen de datos manejable
(~921 estaciones).
