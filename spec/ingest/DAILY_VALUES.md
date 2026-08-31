# Ingestion: Daily climatological values

## Objective

Ingestion script that fetches AEMET's daily climatological values
(temperature, precipitation, wind, pressure, humidity, sunshine) for a
given station and date range, and persists them in the local database
(`climatological_values` table, see
[`spec/db/tables.md`](../db/tables.md)).

Unlike the station inventory job, this one always runs with
**parameters** — at least a date range, and, depending on the import
mode, a station — supplied by the job that triggers it (see
[`spec/control/module/jobs.md`](../control/module/jobs.md) and
[`spec/ingest/general.md`](./general.md)): the user picks what to
import each time. Two import modes share the same table, transform and
load logic (see "Import mode: all stations at once" below):

- **Per station** (`job_type` `daily_values`): one station, one date
  range.
- **All stations at once** (`job_type` `daily_values_all_stations`):
  every station AEMET has data for, one date range.

## Data source

- **API:** AEMET OpenData
- **Endpoint:**
  `GET https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/{fechaIniStr}/fechafin/{fechaFinStr}/estacion/{idema}`
- **Authentication:** `api_key` header, same as the rest of `ingest/`
  — value taken from the `AEMET_API_KEY` key in `config_values` (see
  `spec/db/tables.md`), not `.env`.
- **Path parameters** (not query string):
  - `fechaIniStr` / `fechaFinStr`: `AAAA-MM-DDTHH:MM:SSUTC`, e.g.
    `2024-01-01T00:00:00UTC`.
  - `estacion` (`idema`): station code. The endpoint accepts several
    comma-separated codes in one call, but this job always passes
    exactly one — one job's `params` is one station (see
    `spec/control/module/jobs.md`).

## API behavior (two-step pattern)

Same two-step pattern as the station inventory (see
[`spec/ingest/STATIONS.md`](./STATIONS.md)): an initial request returns
an `{estado, datos, metadatos}` envelope, and the actual records are
fetched from the `datos` URL, `ISO-8859-15` encoded. Reused as-is from
`ingest/aemet_client.py`.

## Date range limit — verified against the live API

**The endpoint rejects a request spanning more than ~6 months**, with
an HTTP `200` whose body has `estado: 404` and
`descripcion: "El rango de fechas no puede ser superior a 6 meses"`
(confirmed empirically; some third-party docs report a stricter 15-day
limit, which does **not** match what the live API actually enforces
for this endpoint).

- **No chunking in this script — decided.** The Jobs module enforces
  `SCHEDULER_MAX_DATE_RANGE` (`config_values`, seeded at `180` days —
  see `spec/db/tables.md` and `spec/control/module/jobs.md`) when a
  `daily_values` job is created: a job's range can never exceed it. As
  long as that config value stays under AEMET's real ~6-month limit
  (not DB-enforced — an operational assumption, not a constraint the
  database can check), every job this script processes fits in a
  **single** AEMET request; there's no internal splitting to do here
  (contrast with the earlier version of this document, which chunked
  internally — that's now handled once, at job-creation time, instead
  of inside every run).
- **Rate limit:** AEMET limits API usage to roughly 50 requests/minute;
  exceeding it returns `estado: 429` in the response envelope, same
  shape as any other AEMET error. With one worker running one job at a
  time (`spec/ingest/general.md`), this is unlikely but not impossible
  if jobs queue up back-to-back — so this script retries a `429` with
  backoff (fixed short delay, small number of attempts) before giving
  up and marking the job `error`.

## Character encoding

Same as the station inventory job: `datos` is served as
`ISO-8859-15`, decoded explicitly (see `spec/ingest/STATIONS.md`,
"Character encoding" — handled by the shared `ingest/aemet_client.py`).

## Source fields (per station/day)

Per the resource's live `metadatos` (fetched directly from the API to
confirm this table, rather than relying on third-party summaries):

| Field         | Type (source) | Description                                             | Example       |
|---------------|---------------|-----------------------------------------------------------|---------------|
| `fecha`       | string        | Day, `AAAA-MM-DD`                                          | `2024-01-01`  |
| `indicativo`  | string        | Station code; matches the request's `estacion` param for this job, and is what `transform()` reads to populate `station_code` (see "Transformations to apply") | `3195` |
| `nombre`, `provincia`, `altitud` | string | Station metadata, redundant with `stations` (not stored) | — |
| `tmed`        | string (float, comma decimal) | Daily mean temperature (°C)               | `"6,6"`       |
| `prec`        | string (float, comma decimal, or sentinel) | Daily precipitation (mm); `Ip` = trace (<0.1mm); `Acum` = accumulated over several days | `"0,0"`, `"Ip"` |
| `tmin` / `horatmin` | string / string | Minimum temperature (°C) and its time (UTC)         | `"3,8"` / `"08:50"` |
| `tmax` / `horatmax` | string / string | Maximum temperature (°C) and its time (UTC)         | `"9,4"` / `"15:40"` |
| `dir`         | string (float) | Direction of max wind gust (tens of degrees); `88` = no data, `99` = variable | `"23"` |
| `velmedia`    | string (float) | Daily mean wind speed (m/s)                              | `"1,4"`       |
| `racha` / `horaracha` | string / string | Max wind gust speed (m/s) and its time (UTC)      | `"6,4"` / `"15:50"` |
| `sol`         | string (float) | Sunshine duration (hours)                                | —             |
| `presMax` / `horaPresMax` | string / string | Max pressure (hPa) and its time (UTC, rounded)  | `"945,1"` / `"23"` |
| `presMin` / `horaPresMin` | string / string | Min pressure (hPa) and its time (UTC, rounded)  | `"940,8"` / `"03"` |
| `hrMedia`     | string (float) | Daily mean relative humidity (%)                         | `"85"`        |
| `hrMax` / `horaHrMax` | string / string | Max relative humidity (%) and its time (UTC)      | `"99"` / `"Varias"` |
| `hrMin` / `horaHrMin` | string / string | Min relative humidity (%) and its time (UTC)      | `"62"` / `"15:30"` |
| `pintMax` / `horaPintMax` | string / string | Max precipitation intensity (mm/h) and its time; `-0,3` = inappreciable | `"0,0"` |

Notes:
- **Every field except `fecha`/`indicativo`/`nombre`/`provincia`/`altitud`
  is optional** (`requerido: false` in `metadatos`) — a station may
  lack a given sensor (e.g. no `sol`), in which case the field is
  simply absent from that record, not `null`.
- **Decimal comma**: numeric-looking fields use `,` as the decimal
  separator (e.g. `"6,6"`), not `.` — must be replaced before parsing
  to `float`. This wasn't needed for the station inventory job (its
  numeric-looking fields, like `altitud`, don't use decimals).
- **`hora*` fields aren't always a time**: observed in real data,
  `horaHrMax` can be `"Varias"` (the extreme value was reached more
  than once that day) instead of `HH:MM`.

## Transformations to apply

1. **Station/date**: use `indicativo` from the response as
   `station_code` (the same value as the job's own `station_code`
   param, but `transform()` reads it off the response rather than off
   `params` — this also makes `transform()` reusable as-is for the
   "all stations" import mode below, where there's no single
   `station_code` param to fall back on) and parse `fecha` as a date.
2. **Numeric fields** (`tmed`, `tmin`, `tmax`, `dir`, `velmedia`,
   `racha`, `sol`, `presMax`, `presMin`, `hrMedia`, `hrMax`, `hrMin`,
   `pintMax`): replace `,` with `.`, convert to `float`; absent field →
   `NULL`.
3. **`prec`**: keep the raw string as-is in `precipitation_raw`;
   additionally attempt the same comma→dot float conversion for
   `precipitation_mm`, storing `NULL` there (only there) when the raw
   value isn't a plain number (`Ip`, `Acum`) — see
   `spec/db/tables.md` for why.
4. **`hora*` fields**: stored as-is (`varchar`), no parsing — see
   "Source fields" notes above.
5. **Drop** `nombre`, `provincia`, `altitud` from the response
   (redundant with `stations`, see `spec/db/tables.md`); `indicativo`
   is kept — see point 1.

## Load strategy

- **Upsert** by (`station_code`, `date`): if the row already exists
  (e.g. re-importing an overlapping range) it's overwritten; if not,
  it's inserted. No change-history table — see `spec/db/tables.md`,
  "Design notes". Never duplicated: guaranteed by the table's
  composite primary key (`station_code`, `date`) plus `ON CONFLICT
  (station_code, date) DO UPDATE`, covered by an integration test (see
  `spec/testing.md`, "Known exceptions") rather than trusted on
  reading alone.
- The first time a row was inserted and the last time it was updated
  are recorded (`created_at`/`updated_at`, see `spec/db/tables.md`).

## Job flow (summary)

Executed by the job worker (`spec/ingest/general.md`) for a
`daily_values` job with `params = {station_code, date_from, date_to}`
(already ≤ `SCHEDULER_MAX_DATE_RANGE`, see "Date range limit" above):

1. Call the endpoint once for `[date_from, date_to]` and `station_code`.
2. On `estado: 429`, retry with backoff (see "Date range limit").
3. On any other AEMET error, or after exhausting retries, mark the job
   `error` with the error detail.
4. Decode as `ISO-8859-15`, parse the JSON array.
5. Transform each record (see "Transformations to apply").
6. Upsert each record into `climatological_values`.
7. Report totals (rows inserted/updated) back on the `ingest_jobs` row
   (`spec/db/tables.md`).

## Import mode: all stations at once

Second import mode of this same job (`job_type`
`daily_values_all_stations`), triggered from a dedicated screen in the
Jobs module (see `spec/control/module/jobs.md`): instead of a single
station, one call covers every station AEMET has data for, for the
same date range.

- **Endpoint:**
  `GET https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/{fechaIniStr}/fechafin/{fechaFinStr}/todasestaciones`
  — same two-step pattern, authentication, encoding and `metadatos`
  shape as the per-station endpoint (same underlying resource,
  aggregated across stations rather than filtered to one).
- **`params = {date_from, date_to}`** — no `station_code`: `indicativo`
  in each returned record is what identifies the station a given row
  belongs to (see "Transformations to apply" above, point 1 — this is
  exactly why that logic already reads `indicativo` off the response
  instead of off `params`, rather than being duplicated here).
- **Same `transform()` and `UPSERT_SQL`, unchanged**: since
  `station_code` already comes from `indicativo`, every other field is
  parsed identically to the per-station mode. This mode is a different
  endpoint and a different `params` shape, not a different transform.
- **Date range limit — pending empirical verification.** The per-day,
  all-stations volume returned by this endpoint (~900-950 stations ×
  each day in range) is much larger than a single station's, so the
  limit AEMET enforces here is expected to be materially shorter than
  the per-station endpoint's ~6 months (see "Date range limit" above)
  — must be confirmed against the live API (same methodology already
  used for the per-station limit: call the real endpoint, don't trust
  third-party docs) before this is relied on anywhere. Until verified,
  treated as **unknown, not assumed equal to `SCHEDULER_MAX_DATE_RANGE`**.
- **Row-level error handling**: same as the per-station mode — a
  single record's upsert failing (e.g. an `indicativo` with no matching
  `stations` row, which would violate the `station_code` foreign key)
  is caught per-row, counted in `errors`, and doesn't abort the rest of
  the batch (see "Job flow (summary)" above, and `ingest/daily_values.py`'s
  existing per-record `try`/`except` in `run_import`).
- **Same rate-limit retry** as the per-station mode (`429` with
  backoff, see "Date range limit" above) — same shared
  `ingest/aemet_client.py`.
- **Implementation — decided: same module, new function.** A new
  `run_import_all_stations(params)` in `ingest/daily_values.py`,
  reusing `transform()`/`UPSERT_SQL` as-is, rather than a separate
  module — the transform/load logic is identical, only the endpoint
  and the `params` shape differ (see `CLAUDE.md`, "Code conventions":
  each ingestion script owns its own transform/load, which here is
  genuinely one shared implementation, not two).

## Implementation

Both import modes live in `ingest/daily_values.py` (`run_import` for
the per-station mode, `run_import_all_stations` for the "all stations"
mode — see above), backed by the shared `ingest/aemet_client.py`
(two-step pattern + decoding — extended with retry/backoff for `429`,
see "Date range limit") and `ingest/db.py`. Invoked by the job worker
(`spec/ingest/general.md`), not run directly on the command line like
`ingest/stations.py` (though nothing prevents calling either function
manually with explicit parameters for debugging).

## Additional decisions

- **Retries — decided: yes, for rate-limit (`429`) responses only.**
  Any other error fails the job immediately (same "no retries" spirit
  as `spec/ingest/STATIONS.md` for anything that isn't a routine,
  expected condition).
- **No internal chunking — decided.** A job's range is capped at
  `SCHEDULER_MAX_DATE_RANGE` before it's ever created (see "Date range
  limit" and `spec/control/module/jobs.md`).
- **No change history — decided.** See `spec/db/tables.md`.
