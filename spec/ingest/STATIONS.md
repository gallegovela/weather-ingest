# Ingestion: Climatological station inventory

## Objective

Ingestion script that fetches the full list of AEMET climatological
stations and persists it in the local database (`stations` table, see
[`spec/db/tables.md`](../db/tables.md)), so that the rest of the
ingestion jobs (daily climatological values, etc.) can reference valid
stations without depending on another API call.

## Data source

- **API:** AEMET OpenData
- **Endpoint:**
  `GET https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones`
- **Authentication:** `api_key` header, value taken from the
  `AEMET_API_KEY` key in the `config_values` table (see
  `spec/db/tables.md`), not from `.env`.
- **Frequency:** on demand for now. The station inventory changes very
  infrequently (occasional additions/removals/location changes), so
  it doesn't need to run daily. It can be scheduled later (e.g.
  weekly/monthly) if the need arises.

## API behavior (two-step pattern)

AEMET OpenData doesn't return the data directly on the first call.
The flow is:

1. **Initial request** to the endpoint above with `api_key`. Returns a
   small JSON with two temporary URLs:
   ```json
   {
     "descripcion": "exito",
     "estado": 200,
     "datos": "https://opendata.aemet.es/opendata/sh/xxxxxxxx",
     "metadatos": "https://opendata.aemet.es/opendata/sh/yyyyyyyy"
   }
   ```
   - `datos`: signed URL (no `api_key` needed) pointing to the actual
     content. Expires after a few minutes.
   - `metadatos`: URL with the description of the resource's fields.
2. **Second request** to the `datos` URL to get the JSON array with
   the stations.
3. (Optional, informational) Request to `metadatos` for the field
   descriptions — useful in development, not needed on every job run.

The script must handle errors from the first response (e.g. `estado
!= 200`, rate limit exceeded, invalid/expired token) and not assume
`datos` is always present.

## Character encoding

**Important:** the step-2 response (`datos`) is served with
`Content-Type: text/plain;charset=ISO-8859-15`, **not UTF-8**. If the
content is decoded assuming UTF-8 (the default behavior of many HTTP
libraries), accented characters and Ñ get corrupted (e.g. `SÓLLER` →
`S�LLER`).

The script must:

- Read the response content raw (bytes).
- Explicitly decode it as `ISO-8859-15` before parsing it as JSON.
- Re-encode/store as UTF-8 from that point on (DB, intermediate
  files, logs).

## Source fields (per station)

Per the resource's `metadatos`:

| Field        | Type (source) | Description                                   | Example         |
|--------------|---------------|--------------------------------------------------|-----------------|
| `indicativo` | string        | Climatological code of the station (identifier) | `B013X` |
| `nombre`     | string        | Station location/name                | `ESCORCA, LLUC` |
| `provincia`  | string        | Province where the station is located              | `ILLES BALEARS` |
| `latitud`    | string        | Latitude in `DDMMSSH` format (degrees, minutes, seconds, N/S hemisphere) | `394924N` |
| `longitud`   | string        | Longitude in `DDDMMSSH` format (degrees, minutes, seconds, E/W hemisphere) | `025309E` |
| `altitud`    | string        | Altitude in meters (comes as text, not numeric) | `490` |
| `indsinop`   | string        | Synoptic code. May come empty (`""`)  | `08304`         |

Notes:
- Every field comes typed as `string` in the source, even the numeric
  ones (`altitud`) — the script must convert them to the correct type
  before persisting.
- `indsinop` is optional: not every station has a synoptic code
  assigned.
- The expected volume is around 900-950 stations (921 in the initial
  check), so pagination isn't needed.

## Transformations to apply

1. **Coordinate parsing**: convert `latitud`/`longitud` from `DDMMSSH`
   format to decimal degrees (float), applying a negative sign when
   the hemisphere is `S` or `W`. The original text value is also kept
   for traceability.
2. **Altitude**: convert from string to integer (meters).
3. **`indsinop` normalization**: empty string → `NULL`.
4. **Trim** extra whitespace in text fields (`nombre`, `provincia`).

## Load strategy

- **Upsert**-style load by `indicativo` (the station's natural key):
  if the station already exists its data is updated; if not, it's
  inserted.
- Stations that stop appearing in the API's response on a given run
  aren't deleted (a station could temporarily disappear from the
  inventory without that meaning its associated history should be
  lost). This decision can be revisited later.
- The first time a station was seen and the last time it was updated
  are recorded (see audit columns in `spec/db/tables.md`).
- **Change history — decided:** before overwriting a station whose
  data (`nombre`, `provincia`, `latitud`, `longitud`, `altitud`,
  `indsinop`) has changed relative to what's already stored, a copy
  of the previous state is saved in `stations_history` (see
  `spec/db/tables.md`). No history is saved on inserts (new stations)
  nor when the upsert doesn't change any data.

## Script flow (summary)

1. Read `AEMET_API_KEY` from `config_values`.
2. Call the station inventory endpoint.
3. Validate the response (`estado == 200` and presence of `datos`).
4. Download the content from the `datos` URL.
5. Decode as `ISO-8859-15` and parse the resulting JSON.
6. Transform each record (coordinates, altitude, normalization).
7. Upsert each station into the `stations` table.
8. Log: number of stations received, inserted, updated and errors (if
   any).

## Implementation

Script in `ingest/stations.py`, backed by `ingest/aemet_client.py`
(two-step pattern + decoding) and `ingest/db.py` (`psycopg` v3
connection, no ORM). Run with: `python -m ingest.stations`.

## Additional decisions

- **Retries — decided: not implemented for now.** On a network or API
  failure the script simply fails; being an on-demand run (not an
  unattended process), it's rerun by hand if needed.
- **Change history — decided: yes.** See "Load strategy" and the
  `stations_history` table in `spec/db/tables.md`.
- **On-demand triggering from the control panel:** this job can be
  queued from the "Stations" screen of the panel's Jobs module (see
  `spec/control/module/jobs.md`), executed by the job worker described
  in `spec/ingest/general.md`, in addition to running it directly with
  `python -m ingest.stations`.
- **Periodic scheduling (cron/scheduler) — postponed, and not the same
  thing as the above.** The Jobs module only lets a user queue a run
  whenever they choose to; there's still no automatic periodic
  trigger. If that's ever needed, it'll be tackled once there's a full
  picture of what needs to run periodically.
