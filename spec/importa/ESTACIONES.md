# Importación: Inventario de estaciones climatológicas

## Objetivo

Script de ingesta que obtiene el listado completo de estaciones
climatológicas de AEMET y lo persiste en la base de datos local
(tabla `estaciones`, ver [`spec/db/tables.md`](../db/tables.md)),
para que el resto de jobs de importación (valores climatológicos
diarios, etc.) puedan referenciar estaciones válidas sin depender
de otra llamada a la API.

## Origen de los datos

- **API:** AEMET OpenData
- **Endpoint:**
  `GET https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones`
- **Autenticación:** cabecera `api_key`, valor tomado de la variable
  de entorno `AEMET_API_KEY` (fichero `.env`, no versionado).
- **Frecuencia:** bajo demanda por ahora. El inventario de estaciones
  cambia con muy poca frecuencia (altas/bajas/cambios de ubicación
  ocasionales), por lo que no necesita ejecutarse a diario. Se podrá
  programar más adelante (ej. semanal/mensual) si se detecta la
  necesidad.

## Comportamiento de la API (patrón de dos pasos)

AEMET OpenData no devuelve los datos directamente en la primera
llamada. El flujo es:

1. **Petición inicial** al endpoint de arriba con `api_key`.
   Devuelve un JSON pequeño con dos URLs temporales:
   ```json
   {
     "descripcion": "exito",
     "estado": 200,
     "datos": "https://opendata.aemet.es/opendata/sh/xxxxxxxx",
     "metadatos": "https://opendata.aemet.es/opendata/sh/yyyyyyyy"
   }
   ```
   - `datos`: URL firmada (sin necesidad de `api_key`) que apunta al
     contenido real. Caduca pasados unos minutos.
   - `metadatos`: URL con la descripción de los campos del recurso.
2. **Segunda petición** a la URL de `datos` para obtener el array
   JSON con las estaciones.
3. (Opcional, informativo) Petición a `metadatos` para obtener la
   descripción de los campos — útil en desarrollo, no necesaria en
   cada ejecución del job.

El script debe manejar los errores de la primera respuesta (por
ejemplo `estado != 200`, límite de peticiones excedido, token
inválido/caducado) y no asumir que `datos` esté siempre presente.

## Codificación de caracteres

**Importante:** la respuesta del paso 2 (`datos`) se sirve con
`Content-Type: text/plain;charset=ISO-8859-15`, **no UTF-8**. Si se
decodifica el contenido asumiendo UTF-8 (comportamiento por defecto
de muchas librerías HTTP), los caracteres acentuados y la Ñ quedan
corruptos (ej. `SÓLLER` → `S�LLER`).

El script debe:

- Leer el contenido en crudo (bytes) de la respuesta.
- Decodificarlo explícitamente como `ISO-8859-15` antes de
  parsearlo como JSON.
- Volver a codificar/almacenar en UTF-8 a partir de ahí (BD, ficheros
  intermedios, logs).

## Campos de origen (por estación)

Según el `metadatos` del recurso:

| Campo       | Tipo (origen) | Descripción                                   | Ejemplo         |
|-------------|---------------|------------------------------------------------|-----------------|
| `indicativo`| string        | Indicativo climatológico de la estación (identificador) | `B013X` |
| `nombre`    | string        | Ubicación/nombre de la estación                | `ESCORCA, LLUC` |
| `provincia` | string        | Provincia donde reside la estación              | `ILLES BALEARS` |
| `latitud`   | string        | Latitud en formato `GGMMSSH` (grados, minutos, segundos, hemisferio N/S) | `394924N` |
| `longitud`  | string        | Longitud en formato `GGGMMSSH` (grados, minutos, segundos, hemisferio E/W) | `025309E` |
| `altitud`   | string        | Altitud en metros (viene como texto, no numérico) | `490` |
| `indsinop`  | string        | Indicativo sinóptico. Puede venir vacío (`""`)  | `08304`         |

Notas:
- Todos los campos vienen tipados como `string` en el origen, incluso
  los que son numéricos (`altitud`) — el script debe convertirlos al
  tipo correcto antes de persistir.
- `indsinop` es opcional: no todas las estaciones tienen indicativo
  sinóptico asignado.
- El volumen esperado es de en torno a 900-950 estaciones (921 en la
  comprobación inicial), por lo que no se requiere paginación.

## Transformaciones a aplicar

1. **Parseo de coordenadas**: convertir `latitud`/`longitud` del
   formato `GGMMSSH` a grados decimales (float), aplicando signo
   negativo cuando el hemisferio sea `S` o `W`. Se conserva también
   el valor original de texto por trazabilidad.
2. **Altitud**: convertir de string a entero (metros).
3. **Normalización de `indsinop`**: cadena vacía → `NULL`.
4. **Trim** de espacios sobrantes en textos (`nombre`, `provincia`).

## Estrategia de carga

- Carga de tipo **upsert** por `indicativo` (clave natural de la
  estación): si la estación ya existe se actualizan sus datos: si no
  existe, se inserta.
- No se eliminan estaciones que dejen de aparecer en la respuesta de
  la API en una ejecución dada (una estación podría desaparecer
  temporalmente del inventario sin que eso implique que debamos
  perder el histórico asociado a ella). Esta decisión se podrá
  revisar más adelante.
- Se registra cuándo fue la primera vez que se vio una estación y
  cuándo fue la última vez que se actualizó (ver columnas de
  auditoría en `spec/db/tables.md`).

## Flujo del script (resumen)

1. Leer `AEMET_API_KEY` desde `.env`.
2. Llamar al endpoint de inventario de estaciones.
3. Validar la respuesta (`estado == 200` y presencia de `datos`).
4. Descargar el contenido de la URL `datos`.
5. Decodificar como `ISO-8859-15` y parsear el JSON resultante.
6. Transformar cada registro (coordenadas, altitud, normalización).
7. Hacer upsert de cada estación en la tabla `estaciones`.
8. Registrar en log: número de estaciones recibidas, insertadas,
   actualizadas y errores (si los hubiera).

## Implementación

Script en `importa/estaciones.py`, apoyado en `importa/aemet_client.py`
(patrón de dos pasos + decodificación) e `importa/db.py` (conexión
`psycopg` v3, sin ORM). Ejecución: `python -m importa.estaciones`.

## Pendiente de definir

- Política de reintentos ante fallos de red o de la API.
- Si se necesita conservar histórico de cambios por estación (ej.
  cambio de ubicación/altitud) o basta con el estado actual.
- Programación periódica (cron/scheduler) una vez definido el
  mecanismo de ejecución del proyecto.
