# Ingestion: Daily climatological values

## Objective

Ingestion script that fetches AEMET's daily climatological values
(temperature, precipitation, wind, pressure, humidity, sunshine) for a
given station and date range, and persists them in the local database
(`climatological_values` table, see
[`spec/db/tables.md`](../db/tables.md)).

Unlike the station inventory job, this one always runs with
**parameters** — a station and a date range — supplied by the job that
triggers it (see [`spec/control/module/jobs.md`](../control/module/jobs.md)
and [`spec/ingest/general.md`](./general.md)): there's no "import
everything" mode, the user picks what to import each time.

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

- **Chunking — decided:** when a job's `date_from`/`date_to` spans more
  than the safe window, the script splits it into sequential
  sub-requests of **180 days** each (a fixed, conservative margin under
  the ~6-month limit, avoiding edge cases around variable month
  lengths), executed one after another within the same job.
- **Rate limit:** AEMET limits API usage to roughly 50 requests/minute;
  exceeding it returns `estado: 429` in the response envelope, same
  shape as any other AEMET error. Unlike the station inventory job
  (`spec/ingest/STATIONS.md`, "no retries" decision), hitting this
  limit is an **expected, routine** occurrence for a multi-chunk
  request, not a rare failure — so this script retries a `429` with
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
| `indicativo`  | string        | Station code (redundant with the request's `estacion`, not stored — see `spec/db/tables.md`) | `3195` |
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

1. **Station/date**: use the job's own `station_code` (not `indicativo`
   from the response — they're the same value, but the job's param is
   the source of truth) and parse `fecha` as a date.
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
5. **Drop** `indicativo`, `nombre`, `provincia`, `altitud` from the
   response (redundant with `stations`, see `spec/db/tables.md`).

## Load strategy

- **Upsert** by (`station_code`, `date`): if the row already exists
  (e.g. re-importing an overlapping range) it's overwritten; if not,
  it's inserted. No change-history table — see `spec/db/tables.md`,
  "Design notes".
- The first time a row was inserted and the last time it was updated
  are recorded (`created_at`/`updated_at`, see `spec/db/tables.md`).

## Job flow (summary)

Executed by the job worker (`spec/ingest/general.md`) for a
`daily_values` job with `params = {station_code, date_from, date_to}`:

1. Split `[date_from, date_to]` into sequential ≤180-day chunks (see
   "Date range limit" above).
2. For each chunk, in order:
   1. Call the endpoint for that chunk and `station_code`.
   2. On `estado: 429`, retry with backoff (see "Date range limit").
   3. On any other AEMET error, or after exhausting retries, stop and
      mark the job `error` with the error detail — chunks already
      upserted stay in the database (partial progress isn't rolled
      back; the user can requeue the same range, which upserts
      idempotently).
   4. Decode as `ISO-8859-15`, parse the JSON array.
   5. Transform each record (see "Transformations to apply").
   6. Upsert each record into `climatological_values`.
3. Report totals (rows inserted/updated) back on the `ingest_jobs` row
   (`spec/db/tables.md`).

## Implementation

Script in `ingest/daily_values.py`, backed by the shared
`ingest/aemet_client.py` (two-step pattern + decoding — extended with
retry/backoff for `429`, see "Date range limit") and `ingest/db.py`.
Invoked by the job worker (`spec/ingest/general.md`), not run directly
on the command line like `ingest/stations.py` (though nothing prevents
calling it manually with explicit parameters for debugging).

## Additional decisions

- **Retries — decided: yes, for rate-limit (`429`) responses only.**
  Any other error fails the job immediately (same "no retries" spirit
  as `spec/ingest/STATIONS.md` for anything that isn't a routine,
  expected condition).
- **Chunking — decided: fixed 180-day windows.** See "Date range
  limit".
- **No change history — decided.** See `spec/db/tables.md`.
