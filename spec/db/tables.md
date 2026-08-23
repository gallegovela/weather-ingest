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

## Tabla `estaciones_historico`

Guarda el estado anterior de una estación cada vez que
`importa/estaciones.py` detecta, durante el upsert, que alguno de sus
datos ha cambiado respecto a lo ya almacenado (ver
[`spec/importa/ESTACIONES.md`](../importa/ESTACIONES.md)). No se
espera que los datos de una estación cambien con frecuencia, pero si
ocurre (cambio de ubicación, de altitud, etc.) queda constancia de
cómo era antes del cambio.

| Columna              | Tipo        | Nulo | Descripción                                                                 |
|-----------------------|-------------|------|--------------------------------------------------------------------------------|
| `id`                  | `bigint`    | No   | Identificador técnico autonumérico (clave primaria). No hay clave natural: cada fila es un evento de cambio, no una entidad. |
| `estacion_indicativo` | `varchar`   | No   | Clave foránea a `estaciones.indicativo`: estación a la que pertenece este histórico. |
| `nombre`              | `varchar`   | No   | Valor de `nombre` **antes** del cambio.                                       |
| `provincia`           | `varchar`   | No   | Valor de `provincia` antes del cambio.                                        |
| `latitud`             | `varchar`   | No   | Valor de `latitud` (formato `GGMMSSH`) antes del cambio.                      |
| `longitud`            | `varchar`   | No   | Valor de `longitud` (formato `GGGMMSSH`) antes del cambio.                    |
| `latitud_decimal`     | `decimal`   | No   | Valor de `latitud_decimal` antes del cambio.                                  |
| `longitud_decimal`    | `decimal`   | No   | Valor de `longitud_decimal` antes del cambio.                                 |
| `altitud`             | `integer`   | No   | Valor de `altitud` antes del cambio.                                          |
| `indsinop`            | `varchar`   | Sí   | Valor de `indsinop` antes del cambio.                                         |
| `fecha_cambio`        | `timestamp` | No   | Fecha/hora en la que se detectó el cambio (la `fecha_actualizacion` que tenía la fila en `estaciones` justo antes de sobreescribirla). |

### Notas de diseño

- **Snapshot completo, no diff por campo**: cada fila representa el
  estado íntegro de la estación justo antes de la actualización que lo
  sustituyó, no solo el campo que cambió. Es más simple de generar
  (una copia de la fila existente) y de consultar (el estado completo
  en cualquier punto del histórico), a costa de guardar columnas que
  no cambiaron junto a las que sí.
- **Solo se registra en actualizaciones, no en altas**: una estación
  nueva no tiene un "estado anterior" que guardar.
- **Detección de cambio basada en los campos de origen**: se compara
  únicamente `nombre`, `provincia`, `latitud`, `longitud`, `altitud`
  e `indsinop` (los campos que vienen de la API). `latitud_decimal` y
  `longitud_decimal` no se comparan aparte: son una función
  determinista de `latitud`/`longitud`, así que si estas no han
  cambiado, tampoco lo han hecho sus versiones decimales.
- **Sin clave natural**: a diferencia de `estaciones`, cada fila es un
  evento (una versión anterior), no una entidad con identidad propia,
  así que usa un `id` autonumérico según el criterio de
  `spec/db/general.md`.

## Tabla `control_usuarios`

Cuentas de acceso al panel de control, con el prefijo `control_`
acordado en [`spec/control/core.md`](../control/core.md) (única
excepción a la convención de "sin prefijos técnicos" de este
documento). Gestionada desde la sección de seguridad del panel (ver
[`spec/control/module/seguridad.md`](../control/module/seguridad.md)),
no por un proceso de importación.

| Columna              | Tipo        | Nulo | Descripción                                                                 |
|-----------------------|-------------|------|--------------------------------------------------------------------------------|
| `id`                   | `bigint`    | No   | Identificador técnico autonumérico (clave primaria).                          |
| `login`                | `varchar`   | No   | Identificador de acceso, formato email. Único.                                |
| `contrasena_hash`      | `varchar`   | No   | Hash Argon2id de la contraseña. Nunca se almacena en claro.                   |
| `fecha_alta`           | `timestamp` | No   | Fecha/hora de alta del usuario.                                               |
| `fecha_actualizacion`  | `timestamp` | No   | Fecha/hora de la última modificación (ej. cambio de contraseña).             |

### Notas de diseño

- **Clave primaria técnica, no `login`**: aunque `login` es único y
  estable en la práctica, la pantalla de edición de usuario
  (`spec/control/module/seguridad.md`) permite modificar los datos del
  usuario sin excluir explícitamente el propio `login`; usar un `id`
  autonumérico como clave primaria evita que una futura edición de
  `login` obligue a propagar el cambio a `control_sesiones` u otras
  tablas que lo referencien.
- **`login` único, formato email**: única validación de formato
  exigida (decidido en `spec/control/module/seguridad.md`); el formato
  se valida en la capa de servicio del backend (Pydantic), no con un
  `CHECK` en la base de datos.
- **`contrasena_hash`**: algoritmo Argon2id, decidido en
  `spec/control/core.md`. No hay columna de complejidad ni de
  histórico de contraseñas: no se exigen reglas adicionales.
- **Baja física**: eliminar un usuario es un `DELETE` real (decidido
  en `spec/control/module/seguridad.md`), sin columna de estado tipo
  `activo`.
- **Auditoría**: `fecha_alta` se fija en la creación; `fecha_actualizacion`
  se refresca en cada edición (incluido un cambio de contraseña), mismo
  criterio que el resto de tablas del proyecto (`spec/db/general.md`).
  Habilita además el filtro "por fecha de alta" previsto en el listado
  de usuarios (`spec/control/module/seguridad.md`).

### Pendiente de definir

- Ninguno adicional a los ya recogidos en
  `spec/control/module/seguridad.md`.

## Tabla `control_sesiones`

Sesiones de servidor del panel de control (token opaco, no JWT —
decidido en [`spec/control/core.md`](../control/core.md)). Una fila
por sesión activa o histórica.

| Columna              | Tipo        | Nulo | Descripción                                                                 |
|-----------------------|-------------|------|--------------------------------------------------------------------------------|
| `token`                | `varchar`   | No   | Identificador de sesión opaco, generado en el login (clave primaria).        |
| `control_usuario_id`   | `bigint`    | No   | Clave foránea a `control_usuarios.id`: usuario dueño de la sesión.           |
| `fecha_inicio`         | `timestamp` | No   | Fecha/hora del login que creó la sesión.                                     |

### Notas de diseño

- **Clave primaria natural**: el propio `token` es el identificador
  estable que la aplicación recibe en cada petición (cookie
  `httpOnly`/`secure`) para validar la sesión, por lo que se usa
  directamente como clave primaria en vez de añadir un `id` técnico.
- **Sin columna de expiración**: la sesión expira a los
  `CONTROL_SESSION_TTL_MINUTOS` (variable de entorno, por defecto 15,
  ver `spec/control/core.md`) contados desde `fecha_inicio`, calculado
  en cada petición por la capa de servicio de seguridad; no se
  almacena una fecha de expiración porque el TTL es configurable y
  cambiarlo no debe requerir reescribir sesiones ya creadas.
- **Sin renovación**: `fecha_inicio` no se actualiza con el uso
  (decidido en `spec/control/core.md`); la validez de la sesión se
  cuenta siempre desde el login.
- **Borrado en cascada**: al eliminar un usuario (`control_usuarios`,
  baja física) se eliminan también sus sesiones (`ON DELETE CASCADE`),
  para que un usuario dado de baja pierda el acceso de inmediato aunque
  tuviera una sesión todavía vigente.

### Pendiente de definir

- Ninguno adicional a los ya recogidos en `spec/control/core.md`.
