# Tablas de la base de datos

Este documento recoge el diseño de las tablas del proyecto. Se irá
ampliando a medida que se añadan nuevos elementos (valores
climatológicos diarios, etc.).

Motor de base de datos: PostgreSQL (ver `spec/db/general.md`).

## Tabla `estaciones`

Almacena el inventario de estaciones climatológicas de AEMET,
alimentada por el proceso de importación descrito en
[`spec/importa/ESTACIONES.md`](../importa/ESTACIONES.md).

Clave natural: `indicativo` (código de estación asignado por AEMET).

| Columna              | Tipo           | Nulo | Descripción                                                                 |
|----------------------|----------------|------|------------------------------------------------------------------------------|
| `indicativo`         | `varchar`      | No   | Indicativo climatológico de la estación (clave primaria). Ej. `B013X`.       |
| `nombre`             | `varchar`      | No   | Nombre/ubicación de la estación. Ej. `ESCORCA, LLUC`.                         |
| `provincia`          | `varchar`      | No   | Provincia donde reside la estación.                                          |
| `latitud`            | `varchar`      | No   | Latitud original tal como la envía AEMET, formato `GGMMSSH`. Ej. `394924N`.  |
| `longitud`           | `varchar`      | No   | Longitud original tal como la envía AEMET, formato `GGGMMSSH`. Ej. `025309E`.|
| `latitud_decimal`    | `decimal`      | No   | Latitud convertida a grados decimales (derivada de `latitud`).              |
| `longitud_decimal`   | `decimal`      | No   | Longitud convertida a grados decimales (derivada de `longitud`).            |
| `altitud`            | `integer`      | No   | Altitud de la estación en metros.                                           |
| `indsinop`           | `varchar`      | Sí   | Indicativo sinóptico de la estación (no todas lo tienen).                    |
| `fecha_alta`         | `timestamp`    | No   | Fecha/hora en que la estación se vio por primera vez en el inventario.       |
| `fecha_actualizacion`| `timestamp`    | No   | Fecha/hora de la última vez que se actualizaron sus datos.                   |

### Notas de diseño

- **Clave primaria**: `indicativo`. Es el identificador estable que
  usa AEMET para referenciar la estación en el resto de endpoints
  (por ejemplo, al pedir valores climatológicos diarios de una
  estación concreta), por lo que otras tablas futuras referenciarán
  esta columna como clave foránea.
- **Coordenadas duplicadas (texto + decimal)**: se conserva el valor
  original de AEMET (`latitud`/`longitud` en formato `GGMMSSH`) por
  trazabilidad y depuración, además de la versión ya convertida a
  grados decimales (`latitud_decimal`/`longitud_decimal`), que es la
  que se usará en cálculos, mapas y filtros geográficos.
- **`indsinop` opcional**: se normaliza el valor vacío (`""`) que
  devuelve la API como `NULL`.
- **Sin borrado físico**: el proceso de importación no elimina filas
  cuando una estación deja de aparecer en el inventario de AEMET; solo
  inserta o actualiza (upsert). Si en el futuro se necesita marcar
  estaciones como inactivas, se añadirá una columna de estado
  (ej. `activa boolean`) en vez de borrar el registro.
- **Auditoría**: `fecha_alta` se fija una única vez, en la primera
  inserción; `fecha_actualizacion` se refresca en cada upsert,
  aunque los datos no hayan cambiado, para saber cuándo fue la
  última sincronización con la API.

### Implementación

Migración: `db/migrations/versions/20260822_2051_f54155bc39b7_create_estaciones.py`.
`latitud_decimal`/`longitud_decimal` implementadas como `NUMERIC(9,6)`
(precisión de ~0.11 m, más que suficiente para coordenadas de
estaciones).

### Pendiente de definir

- Si se añade un identificador técnico autonumérico (`id`) además de
  la clave natural `indicativo`, en función de cómo lo requieran las
  tablas que referencien a `estaciones`.
- Índices adicionales (ej. por `provincia` si se filtra a menudo por
  esa columna).
