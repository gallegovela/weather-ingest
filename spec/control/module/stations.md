# Module: Stations

First functional module of the panel (beyond `security`, which is
special and cross-cutting — see
[`spec/control/core.md`](../core.md)). **It's the reference module**:
the pattern it sets here (layers, paginated listing with filters,
consuming the API from React, map) is the one reused when building
the rest of the modules.

## Objective

Allow browsing the climatological station inventory already imported
by `ingest/stations.py` into the `stations` table (see
[`spec/db/tables.md`](../../db/tables.md)), both as a listing and
visually on a map. It's a **read-only** module: it doesn't allow
creating, editing, or deleting stations from the panel (that data is
managed by the importer, not the control panel).

## Menu

Two entries under the side menu's **"Datos ingestados" → "AEMET"**
grouping (see "Application structure" in `core.md`) — not a top-level
entry of its own; `stations` shares that section with
[`climatological_values`](./climatological_values.md), both being data
imported from AEMET:

1. **List** — paginated table with filters.
2. **Map** — map with the geolocated stations.

## Screens

### 1. Station list

- **Paginated table** with every station from the `stations` table.
- **Filter per field** of the table, following the cross-cutting
  convention set in `core.md` ("Paginated listings with filters"):
  - Text (`station_code`, `name`, `province`, `synoptic_code`):
    "contains" filter.
  - Numeric (`altitude`, `latitude_decimal`, `longitude_decimal`):
    range filter (min/max).
  - Dates (`created_at`, `updated_at`): date-range filter.
  - `latitude`/`longitude` (AEMET's original `DDMMSSH` text): "contains"
    filter, same as the rest of text fields.
- **Responsive columns with expandable row — decided.** All of
  `stations`'s columns (see `spec/db/tables.md`) are available, but
  depending on screen width the table automatically hides columns
  that don't fit (instead of forcing horizontal scroll) — same
  behavior as DataTables.js's *Responsive* extension. Each row has an
  expand control (`+`) that, when clicked, reveals the values of that
  row's currently hidden columns. Which columns get hidden first
  isn't a fixed list: it depends on the available width (keeping
  `station_code`, `name` and `province` visible is prioritized).
  - **Bug fixed:** the expand control never revealed anything (on any
    screen width, not just mobile). Mantine's `Collapse` component
    renamed its visibility prop from `in` to `expanded` at some point
    before the installed v9 — the code still passed `in`, a prop
    `Collapse` no longer reads, so it always rendered collapsed
    regardless of the row's toggle state. Same underlying class of
    issue as the `DateInput` string-vs-`Date` bug found earlier: code
    written against an older assumption of a Mantine API that had
    since changed underneath it, never caught because nobody had
    clicked the control in a real browser until now.
- **`daily_values_count` column — decided.** Number of
  `climatological_values` rows already imported for that station (see
  [`spec/db/tables.md`](../../db/tables.md)). Not a stored column on
  `stations`: computed by the DAO at query time (see "Data" below),
  shown as one more optional column subject to the same
  responsive/expandable behavior as the rest. Gives a quick answer to
  "does this station have any daily values imported yet, and roughly
  how many" without leaving the listing.
- **Link to that station's daily values — decided.** Each row links to
  [`climatological_values`](./climatological_values.md)'s listing
  screen with that row's `station_code` pre-applied as a filter (see
  that module's spec, "Incoming station filter"), so a user can go
  straight from "this station" to "its imported values" without
  re-typing the code.

### 2. Station map

- Map with a **point/marker per station**, positioned with
  `latitude_decimal`/`longitude_decimal`.
- Clicking a marker shows that **station's details** (the same fields
  as in the listing), so it can be identified/checked without leaving
  the map.
  - **Bug fixed (mobile):** opening the detail popup could immediately
    close it again. Leaflet's `Popup` auto-pans the map by default to
    keep itself in view when it opens; on the small viewports where
    this matters most, that pan can land the marker back inside
    `MarkerClusterGroup`'s recompute radius, which re-clusters it away
    — unmounting the `Marker`/`Popup` right after they opened. Fixed
    by disabling the popup's `autoPan`.
  - **Same link to daily values as the list — decided**, added to the
    popup's content: consistent with the listing (see "Station list"
    above), no reason for the map's detail to offer less.
- **Map provider — decided: OpenStreetMap**, via **Leaflet**
  (`react-leaflet`) as the mapping library in `control/frontend/`.
  Chosen for being free and not requiring an API key or billing
  account (unlike Google Maps), unlike Mapbox or other options with a
  limited free quota.
- **Marker clustering — decided:** with ~921 stations spread across
  Spain, at zoomed-out levels many markers would overlap/pile up.
  `react-leaflet-cluster` is used to group nearby markers into a
  single circle showing the number of stations it contains; zooming
  in or clicking the group breaks it down into individual markers.
  - **Bug fixed:** cluster icons rendered as bare numbers, no colored
    circle. `leaflet/dist/leaflet.css` (imported globally) only covers
    core Leaflet; the cluster plugin's own stylesheets
    (`MarkerCluster.css`, `MarkerCluster.Default.css`, bundled with
    `react-leaflet-cluster`) were never imported.

## Data

Follows the layered architecture from `core.md`:

- **DAO** (`control/backend/modules/stations/dao.py`): `SELECT` query
  on the `stations` table, with pagination (`LIMIT`/`OFFSET`) and the
  received filters, in plain SQL (`psycopg` v3, no ORM — same criteria
  as `ingest/`). Includes `daily_values_count`, computed with a
  `LEFT JOIN` against a `SELECT station_code, count(*) ... FROM
  climatological_values GROUP BY station_code` subquery (`LEFT`, not
  `INNER`, so a station with zero imported values still shows `0`
  instead of being dropped from the listing) — not a second query per
  row, one join covering the whole page.
- **Service** (`service.py`): validates the received filter/pagination
  parameters and delegates to the DAO; contains no additional business
  logic beyond that, since it's a read-only module.
- **Control** (`router.py`): exposes the API endpoints.

### Endpoints (REST API)

Following the contract set in `core.md`:

- `GET /api/stations/stations` — paginated, filtered listing
  (`page`, `page_size` parameters, and one per filterable field per
  the cross-cutting convention). Each item now also includes
  `daily_values_count` (see "Data" above) — **not** itself a
  filterable field (decided): it's a display convenience, not a column
  on `stations`, and filtering "stations with more than N values
  imported" isn't a need that's come up.
- **The map reuses the same endpoint, without pagination — decided.**
  With `page`/`page_size` omitted (or a value returning every row),
  the map requests the full set of stations at once: with ~921
  current rows it isn't a volume that justifies paginating the map's
  request. No dedicated endpoint is created for the map.

## Pending decisions

No open items in this module. The map **doesn't have its own search
box** (decided): clicking the marker is enough to check a station,
given the manageable data volume (~921 stations).
