# Module: Climatological values

## Objective

Let an authenticated user browse the daily climatological values
already imported by `ingest/daily_values.py` into the
`climatological_values` table (see
[`spec/db/tables.md`](../../db/tables.md)). Like `stations`, it's a
**read-only** module: it doesn't allow creating, editing, or deleting
values from the panel — that data is managed by the ingestion job,
triggered from the [`jobs`](./jobs.md) module ("Planificador"), not
from here.

## Menu

One entry under the side menu's **"Datos ingestados" → "AEMET"**
grouping (see "Application structure" in `core.md`), sharing that
section with [`stations`](./stations.md), both being data imported
from AEMET:

1. **Valores Diarios** — paginated table with a filter per field.
   Route: `/climatological-values/values`, matching `GET
   /api/climatological-values/values` (same route-mirrors-endpoint
   criterion already used for `config`'s single screen,
   `/config/values` ↔ `GET /api/config/values`) — flat, not nested
   under `/data/aemet/...`, per `core.md`'s "route structure doesn't
   mirror the menu's nesting".

## Screens

### 1. Daily values list

- **Paginated table** with every row from `climatological_values`,
  joined with `stations` to also show that row's station's
  **identifying data** (`station_code`, `name`, `province`) — the
  table itself doesn't store those (see `spec/db/tables.md`, "Design
  notes": deliberately not duplicated), so this listing is the one
  place in the panel that joins the two.
- **Filter per field — decided, all 27 columns**, following the
  cross-cutting convention set in `core.md` ("Paginated listings with
  filters"):
  - Text ("contains"): `station_code`, `precipitation_raw`, and every
    `*_time` column (`min_temperature_time`, `max_temperature_time`,
    `wind_gust_time`, `pressure_max_time`, `pressure_min_time`,
    `humidity_max_time`, `humidity_min_time`,
    `precipitation_intensity_max_time`) — these can hold non-time text
    like `"Varias"` (see `spec/ingest/DAILY_VALUES.md`), so "contains"
    fits them better than an exact match.
  - Numeric (range, min/max): `mean_temperature`, `precipitation_mm`,
    `min_temperature`, `max_temperature`, `wind_gust_direction`,
    `wind_mean_speed`, `wind_gust_speed`, `sunshine_hours`,
    `pressure_max`, `pressure_min`, `humidity_mean`, `humidity_max`,
    `humidity_min`, `precipitation_intensity_max`.
  - Dates (range): `date`, `created_at`, `updated_at`.
  - `name`/`province` (joined from `stations`, not native columns of
    `climatological_values`) are **not** filterable here — decided:
    filtering by station is done through `station_code` (exact, or via
    the incoming-filter link below), and `stations`'s own listing
    already covers filtering by name/province if that's the starting
    point. Adding a second, redundant path to the same filter isn't
    worth the DAO complexity of filtering across the join.
- **Responsive columns with expandable row — decided, reused from
  `stations`.** With 27+ columns this is essential, not optional here:
  same pattern as `spec/control/module/stations.md` ("Station list"),
  `station_code`/`name`/`province`/`date` kept always visible, the
  rest hidden/revealed by width same as there.
- **Incoming station filter — decided.** Reachable with
  `station_code` pre-applied as a filter via a query string parameter
  (`?station_code=<code>`), read once on mount to seed the filter's
  initial value — same mechanism `stations`'s list and map link to
  this screen with (see `spec/control/module/stations.md`). Without
  the parameter, the screen opens with no filters applied, same as any
  other listing.

## Data

Follows the layered architecture from `core.md`:

- **DAO** (`control/backend/modules/climatological_values/dao.py`):
  `SELECT` on `climatological_values` **joined with** `stations` (for
  `name`/`province`), with pagination and the received filters, in
  plain SQL (`psycopg` v3, no ORM). Read-only: no insert/update/delete
  here, that's `ingest/daily_values.py`'s job (see
  `spec/ingest/DAILY_VALUES.md`).
- **Service** (`service.py`): validates filter/pagination parameters
  and delegates to the DAO; no other business logic, same criteria as
  `stations`.
- **Control** (`router.py`): exposes the endpoint.

### Endpoints (REST API)

Following the contract set in `core.md`:

- `GET /api/climatological-values/values` — paginated, filtered
  listing (`page`, `page_size`, and one query parameter per filterable
  field listed above, plus `station_code` for the incoming-filter
  link). Each item includes the joined `name`/`province` alongside
  every native column.

## Pending decisions

- Default sort order (currently: most recent `date` first, then
  `station_code`) — revisit if real usage shows a more useful default.
