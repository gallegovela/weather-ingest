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

Rows in this table can come from either of `ingest/daily_values.py`'s
two import modes — per station (`daily_values`) or all stations at
once (`daily_values_all_stations`, see
[`spec/ingest/DAILY_VALUES.md`](../../ingest/DAILY_VALUES.md), "Import
mode: all stations at once") — indistinguishably: this listing doesn't
track or filter by which mode produced a given row, since the table
itself doesn't record that (both modes upsert into the same columns).

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
2. **Gráfico Valores Diarios** — station/year/month-scoped charts over
   the same data. Route: `/climatological-values/chart` — flat, same
   criterion as above.

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

### 2. Daily values chart

- **Station filter**: dropdown with autocomplete, searchable by
  code/name, reusing the existing `GET /api/stations/stations`
  endpoint — same pattern as the station picker in `jobs`'s "Daily
  values" screen (see
  [`spec/control/module/jobs.md`](./jobs.md)), which the issue that
  introduced this screen explicitly asked to match.
- **Year selector**: options are the distinct years that have at least
  one imported `climatological_values` row for the selected station,
  in descending order; default value is the most recent of those
  years. Nothing is shown here (and the year selector has no options)
  until a station is selected.
- **Chart 1 — monthly counts (bar chart, 12 bars)**: one bar per month
  of the selected year, each showing the number of
  `climatological_values` rows imported for that station/month —
  i.e. how complete each month's import is, not a climate value.
- **Month selector**: dropdown with the 12 months of the selected
  year, **bidirectionally linked with chart 1**:
  - Clicking a bar in chart 1 sets the month dropdown to that month.
  - Changing the month dropdown highlights the corresponding bar in
    chart 1.
  - Either way, the currently selected month's bar is visually
    highlighted (distinct style) in chart 1.
- **Chart series for the selected month**: once station, year and
  month are all selected, the daily values for that month (fetched via
  the `values` endpoint below) drive a sequence of charts, one after
  another:
  - **Temperaturas**: line chart, 3 series — `mean_temperature`,
    `max_temperature`, `min_temperature`.
  - **Hora temperaturas extremas**: line chart, 2 series —
    `min_temperature_time`, `max_temperature_time`. Both are stored as
    `varchar` (see `spec/db/tables.md`), so each is **converted to
    minutes since midnight** to be plottable as a line.
  - **Insolación**: line chart, 1 series — `sunshine_hours`.
  - **Precipitación — decided: double column (bar) chart, not
    lines.** One series with `precipitation_mm`; a second series
    visually flags the days where `precipitation_raw` is the
    non-numeric sentinel `Ip` or `Acum` (see `spec/db/tables.md`)
    instead of plotting them as a value, since they aren't a
    measurement to compare against `precipitation_mm`. When the
    selected month contains at least one such day, a **legend
    explaining `Ip`/`Acum`** is shown, styled so it's clearly
    noticeable (e.g. a distinct badge/legend item) rather than easy to
    miss; if the month has none, the legend isn't shown.
  - **Humedad**: line chart, 2 series — `humidity_min`,
    `humidity_max`.
  - **Hora humedad extremas**: line chart, 2 series —
    `humidity_max_time`, `humidity_min_time`, same minutes-since-
    midnight conversion as the temperature extreme times above.
  - **Viento**: line chart, 1 series — `wind_mean_speed`.
  - **Gaps — decided, applies to every series above:** any `NULL`/
    missing value, and any `*_time` value that isn't `HH:MM` (e.g.
    `"Varias"`, see `spec/db/tables.md`), is rendered as a **gap** in
    its chart (a null point, not interpolated and not shown as zero).
    This includes the precipitation columns: a day with no numeric
    `precipitation_mm` and no `Ip`/`Acum` sentinel is a gap in both
    series.

## Data

Follows the layered architecture from `core.md`:

- **DAO** (`control/backend/modules/climatological_values/dao.py`):
  `SELECT` on `climatological_values` **joined with** `stations` (for
  `name`/`province`), with pagination and the received filters, in
  plain SQL (`psycopg` v3, no ORM). Read-only: no insert/update/delete
  here, that's `ingest/daily_values.py`'s job (see
  `spec/ingest/DAILY_VALUES.md`). Also adds the two aggregation queries
  needed by the "Daily values chart" screen (distinct years and
  monthly counts for a station, see below), both filtering on
  `station_code` and grouping on `date`, using the existing composite
  primary key (`station_code`, `date`) — no extra index needed.
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
  every native column. Also reused (unpaginated, or with `page_size`
  large enough to cover a month) by the "Daily values chart" screen to
  fetch a selected month's daily rows for its charts, filtering by
  `station_code` plus a `date_from`/`date_to` range spanning that
  month — no new endpoint needed for this, same reuse criterion
  `jobs.md` already applies for its overlap check.
- `GET /api/climatological-values/years?station_code=...` — distinct
  years with at least one imported row for that station, descending.
  Feeds the chart screen's year selector.
- `GET /api/climatological-values/monthly-counts?station_code=...&year=...`
  — one row count per month (12 values) of `climatological_values` for
  that station/year. Feeds chart 1 (monthly counts bar chart) on the
  chart screen.

## Pending decisions

- Default sort order (currently: most recent `date` first, then
  `station_code`) — revisit if real usage shows a more useful default.
