# Module: Metrics

## Objective

Let an authenticated user browse the climatological metrics already
computed by `ingest/metrics.py` into the `climatological_metrics`
table (see [`spec/db/tables.md`](../../db/tables.md)): the daily
temperature range and the day-over-day temperature differences (see
[`spec/ingest/METRICS.md`](../../ingest/METRICS.md)). Like `stations`
and `climatological_values`, it's a **read-only** module: it doesn't
allow creating, editing, or deleting metrics from the panel — that
data is managed by the `metrics` ingestion job, triggered (manually or
automatically) from the [`jobs`](./jobs.md) module ("Planificador"),
not from here. The third requested metric (total rainy days in an
imported period) isn't browsable here, since it isn't a per-day table
row — it's visible on the `metrics` job's own history row instead (see
`spec/control/module/jobs.md`).

## Menu

One entry under the side menu's **"Datos ingestados" → "AEMET"**
grouping (see "Application structure" in `core.md`), sharing that
section with [`stations`](./stations.md) and
[`climatological_values`](./climatological_values.md), all three being
data imported/derived from AEMET:

1. **Métricas** — paginated table with a filter per field. Route:
   `/metrics/values`, matching `GET /api/metrics/values` (same
   route-mirrors-endpoint criterion as `climatological_values`'s
   listing screen) — flat, not nested, per `core.md`'s "route
   structure doesn't mirror the menu's nesting".

## Screens

### 1. Metrics list

- **Paginated table** with every row from `climatological_metrics`,
  joined with `stations` to also show that row's station's
  **identifying data** (`station_code`, `name`, `province`) — same
  reasoning as `climatological_values`'s listing: that data isn't
  duplicated on `climatological_metrics` itself (see
  `spec/db/tables.md`), so this listing joins the two.
- **Filter per field**, following the cross-cutting convention set in
  `core.md` ("Paginated listings with filters"):
  - Text ("contains"): `station_code`.
  - Numeric (range, min/max): `temperature_range`,
    `max_temperature_diff_prev_day`, `min_temperature_diff_prev_day`.
  - Dates (range): `date`, `created_at`, `updated_at`.
  - `name`/`province` (joined from `stations`) are **not** filterable
    here, same decision and reasoning as
    `climatological_values.md`'s listing.
- **Incoming station filter — decided**, same mechanism as
  `climatological_values`: reachable with `station_code` pre-applied
  as a filter via `?station_code=<code>`, read once on mount.

## Data

Follows the layered architecture from `core.md`:

- **DAO** (`control/backend/modules/metrics/dao.py`): `SELECT` on
  `climatological_metrics` **joined with** `stations` (for
  `name`/`province`), with pagination and the received filters, in
  plain SQL (`psycopg` v3, no ORM). Read-only: no insert/update/delete
  here, that's `ingest/metrics.py`'s job (see
  `spec/ingest/METRICS.md`).
- **Service** (`service.py`): validates filter/pagination parameters
  and delegates to the DAO; no other business logic, same criteria as
  `stations`/`climatological_values`.
- **Control** (`router.py`): exposes the endpoint.

### Endpoints (REST API)

Following the contract set in `core.md`:

- `GET /api/metrics/values` — paginated, filtered listing (`page`,
  `page_size`, and one query parameter per filterable field listed
  above, plus `station_code` for the incoming-filter link). Each item
  includes the joined `name`/`province` alongside every native column.

## Pending decisions

None.
