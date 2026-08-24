# Database tables

This document covers the design of the project's tables. It will be
expanded as new elements are added (daily climatological values,
etc.).

Database engine: PostgreSQL (see `spec/db/general.md`).

## Table `stations`

Stores the inventory of AEMET climatological stations, fed by the
ingestion process described in
[`spec/ingest/STATIONS.md`](../ingest/STATIONS.md).

Natural key: `station_code` (station code assigned by AEMET).

| Column               | Type           | Null | Description                                                                 |
|----------------------|----------------|------|------------------------------------------------------------------------------|
| `station_code`       | `varchar`      | No   | Climatological code of the station (primary key). E.g. `B013X`.       |
| `name`               | `varchar`      | No   | Station name/location. E.g. `ESCORCA, LLUC`.                         |
| `province`           | `varchar`      | No   | Province where the station is located.                                          |
| `latitude`           | `varchar`      | No   | Original latitude as sent by AEMET, `DDMMSSH` format. E.g. `394924N`.  |
| `longitude`          | `varchar`      | No   | Original longitude as sent by AEMET, `DDDMMSSH` format. E.g. `025309E`.|
| `latitude_decimal`   | `decimal`      | No   | Latitude converted to decimal degrees (derived from `latitude`).              |
| `longitude_decimal`  | `decimal`      | No   | Longitude converted to decimal degrees (derived from `longitude`).            |
| `altitude`           | `integer`      | No   | Station altitude in meters.                                           |
| `synoptic_code`      | `varchar`      | Yes  | Synoptic code of the station (not all stations have one).                    |
| `created_at`         | `timestamp`    | No   | Date/time the station was first seen in the inventory.       |
| `updated_at`         | `timestamp`    | No   | Date/time its data was last updated.                   |

### Design notes

- **Primary key**: `station_code`. It's the stable identifier AEMET
  uses to reference the station in the rest of its endpoints (e.g.
  when requesting daily climatological values for a specific
  station), so future tables will reference this column as a foreign
  key.
- **Duplicated coordinates (text + decimal)**: the original AEMET
  value is kept (`latitude`/`longitude` in `DDMMSSH` format) for
  traceability and debugging, alongside the version already
  converted to decimal degrees (`latitude_decimal`/`longitude_decimal`),
  which is the one used in calculations, maps and geographic filters.
- **`synoptic_code` optional**: the empty value (`""`) returned by the
  API is normalized to `NULL`.
- **No physical deletion**: the ingestion process doesn't remove rows
  when a station stops appearing in the AEMET inventory; it only
  inserts or updates (upsert). If marking stations as inactive is
  ever needed, a status column will be added (e.g. `active boolean`)
  instead of deleting the record.
- **Auditing**: `created_at` is set once, on first insert;
  `updated_at` is refreshed on every upsert, even if the data hasn't
  changed, to know when the last sync with the API happened.

### Implementation

Migration: `db/migrations/versions/20260822_2051_f54155bc39b7_create_stations.py`.
`latitude_decimal`/`longitude_decimal` implemented as `NUMERIC(9,6)`
(precision of ~0.11 m, more than enough for station coordinates).

### Pending decisions

- Whether to add an auto-numbered technical identifier (`id`) besides
  the `station_code` natural key, depending on how tables that
  reference `stations` end up needing it.
- Additional indexes (e.g. on `province` if it's filtered on often).

## Table `stations_history`

Keeps the previous state of a station every time
`ingest/stations.py` detects, during the upsert, that some of its
data has changed relative to what's already stored (see
[`spec/ingest/STATIONS.md`](../ingest/STATIONS.md)). A station's data
isn't expected to change often, but if it does (a location change, an
altitude change, etc.) there's a record of how it was before the
change.

| Column                | Type        | Null | Description                                                                 |
|-----------------------|-------------|------|--------------------------------------------------------------------------------|
| `id`                   | `bigint`    | No   | Auto-numbered technical identifier (primary key). No natural key: each row is a change event, not an entity. |
| `station_code`         | `varchar`   | No   | Foreign key to `stations.station_code`: the station this history entry belongs to. |
| `name`                 | `varchar`   | No   | Value of `name` **before** the change.                                       |
| `province`             | `varchar`   | No   | Value of `province` before the change.                                        |
| `latitude`             | `varchar`   | No   | Value of `latitude` (`DDMMSSH` format) before the change.                      |
| `longitude`            | `varchar`   | No   | Value of `longitude` (`DDDMMSSH` format) before the change.                    |
| `latitude_decimal`     | `decimal`   | No   | Value of `latitude_decimal` before the change.                                  |
| `longitude_decimal`    | `decimal`   | No   | Value of `longitude_decimal` before the change.                                 |
| `altitude`             | `integer`   | No   | Value of `altitude` before the change.                                          |
| `synoptic_code`        | `varchar`   | Yes  | Value of `synoptic_code` before the change.                                         |
| `changed_at`           | `timestamp` | No   | Date/time the change was detected (the `updated_at` the row in `stations` had right before it was overwritten). |

### Design notes

- **Full snapshot, not a per-field diff**: each row represents the
  full state of the station right before the update that replaced it,
  not just the field that changed. It's simpler to generate (a copy
  of the existing row) and to query (the full state at any point in
  the history), at the cost of storing columns that didn't change
  alongside the ones that did.
- **Only recorded on updates, not on inserts**: a new station has no
  "previous state" to save.
- **Change detection based on source fields**: only `name`,
  `province`, `latitude`, `longitude`, `altitude` and `synoptic_code`
  (the fields coming from the API) are compared. `latitude_decimal`
  and `longitude_decimal` aren't compared separately: they're a
  deterministic function of `latitude`/`longitude`, so if those
  haven't changed, neither have their decimal versions.
- **No natural key**: unlike `stations`, each row is an event (a
  previous version), not an entity with its own identity, so it uses
  an auto-numbered `id` per the criteria in `spec/db/general.md`.

## Table `climatological_values`

Stores AEMET's daily climatological values (temperature, precipitation,
wind, pressure, humidity, sunshine) per station and day, fed by the
ingestion process described in
[`spec/ingest/DAILY_VALUES.md`](../ingest/DAILY_VALUES.md).

Natural key: `station_code` + `date`.

| Column                              | Type        | Null | Description                                                                 |
|--------------------------------------|-------------|------|--------------------------------------------------------------------------------|
| `station_code`                       | `varchar`   | No   | Foreign key to `stations.station_code`.                                       |
| `date`                                | `date`      | No   | Day this row's values are for.                                                |
| `mean_temperature`                    | `decimal`   | Yes  | Daily mean temperature (°C).                                                  |
| `precipitation_mm`                    | `decimal`   | Yes  | Daily precipitation (mm). `NULL` when `precipitation_raw` is a non-numeric sentinel (`Ip`, `Acum`). |
| `precipitation_raw`                   | `varchar`   | Yes  | Precipitation exactly as received from AEMET: a plain number, `Ip` (trace, <0.1mm) or `Acum` (accumulated over several days). |
| `min_temperature`                     | `decimal`   | Yes  | Daily minimum temperature (°C).                                               |
| `min_temperature_time`                | `varchar`   | Yes  | Time of the minimum temperature (UTC; may be non-time text like `Varias`).    |
| `max_temperature`                     | `decimal`   | Yes  | Daily maximum temperature (°C).                                               |
| `max_temperature_time`                | `varchar`   | Yes  | Time of the maximum temperature (UTC; may be non-time text).                  |
| `wind_gust_direction`                 | `decimal`   | Yes  | Direction of the maximum wind gust (tens of degrees; `88` = no data, `99` = variable direction). |
| `wind_mean_speed`                     | `decimal`   | Yes  | Daily mean wind speed (m/s).                                                  |
| `wind_gust_speed`                     | `decimal`   | Yes  | Maximum wind gust speed (m/s).                                                |
| `wind_gust_time`                      | `varchar`   | Yes  | Time of the maximum wind gust (UTC; may be non-time text).                    |
| `sunshine_hours`                      | `decimal`   | Yes  | Daily sunshine duration (hours).                                              |
| `pressure_max`                        | `decimal`   | Yes  | Maximum pressure at the station's reference level (hPa).                      |
| `pressure_max_time`                   | `varchar`   | Yes  | Time of the maximum pressure (UTC, rounded to the nearest hour).              |
| `pressure_min`                        | `decimal`   | Yes  | Minimum pressure at the station's reference level (hPa).                      |
| `pressure_min_time`                   | `varchar`   | Yes  | Time of the minimum pressure (UTC, rounded to the nearest hour).              |
| `humidity_mean`                       | `decimal`   | Yes  | Daily mean relative humidity (%).                                             |
| `humidity_max`                        | `decimal`   | Yes  | Daily maximum relative humidity (%).                                          |
| `humidity_max_time`                   | `varchar`   | Yes  | Time of the maximum relative humidity (UTC; may be non-time text).            |
| `humidity_min`                        | `decimal`   | Yes  | Daily minimum relative humidity (%).                                          |
| `humidity_min_time`                   | `varchar`   | Yes  | Time of the minimum relative humidity (UTC; may be non-time text).            |
| `precipitation_intensity_max`         | `decimal`   | Yes  | Maximum precipitation intensity (mm/h; `-0.3` = inappreciable, <0.1mm/h).      |
| `precipitation_intensity_max_time`    | `varchar`   | Yes  | Time of the maximum precipitation intensity (UTC; may be non-time text).      |
| `created_at`                          | `timestamp` | No   | Date/time this row was first inserted.                                        |
| `updated_at`                          | `timestamp` | No   | Date/time this row was last updated.                                          |

### Design notes

- **Composite natural key (`station_code`, `date`)**: AEMET's source
  data is already uniquely identified by station and day — one row per
  station per day — so there's no need for a technical `id`, same
  criterion as `stations`.
- **`station`/`province`/`altitude` not duplicated here**: the source
  API repeats the station's `indicativo`/`nombre`/`provincia`/`altitud`
  on every daily record, but that data already lives in `stations` and
  is reachable via the `station_code` foreign key — storing it again
  per row would duplicate data that can drift out of sync (see
  `stations_history`) for no benefit.
- **Decimal comma in the source, not a DB concern**: AEMET returns
  numeric values as text with a comma decimal separator (e.g. `"6,6"`).
  This is purely an ingestion-time parsing detail (see
  `spec/ingest/DAILY_VALUES.md`); the columns here store proper
  `decimal` values.
- **`precipitation_raw` alongside `precipitation_mm` — decided:**
  unlike the other numeric fields, `prec` can carry two non-numeric
  sentinel values with real meaning (`Ip` = trace rain fell but
  couldn't be measured, vs. `NULL`/absent = no data at all; `Acum` =
  this day's figure is folded into a later accumulated reading). Losing
  that distinction by coercing straight to `NULL` would conflate
  "trace rain" with "no measurement". The other sentinel-bearing fields
  (`wind_gust_direction`'s `88`/`99`, `precipitation_intensity_max`'s
  `-0.3`) are still syntactically valid numbers, so they're stored as
  plain `decimal` — their special meaning is documented above, not
  represented structurally.
- **`*_time` columns are `varchar`, not `time`**: most contain an
  `HH:MM` value, but AEMET can return non-time text instead (observed
  in real data: `"Varias"`, meaning the extreme value was reached more
  than once that day). A `time` column can't hold that.
- **No change-history table (unlike `stations_history`) — decided:**
  re-running a `daily_values` job for a date range that overlaps
  existing rows is an expected, routine way to use this table (e.g.
  re-importing a period to pick up an AEMET correction), not a rare
  event worth a full audit trail; and at this table's expected volume
  (potentially millions of rows across all stations/years), snapshotting
  every upsert would be costly for little benefit. Revisit if a real
  need for point-in-time history shows up.
- **Upsert by (`station_code`, `date`)**: same load strategy as
  `stations` — insert if new, overwrite if the row already exists.

### Pending decisions

- None beyond the ones already covered in
  `spec/ingest/DAILY_VALUES.md`.

## Table `config_values`

Generic key-value store for operational configuration used across the
project's processes (e.g. the ingest job worker's polling interval,
see `spec/ingest/`). Editable from the control panel's config module
(see [`spec/control/module/config.md`](../control/module/config.md)),
but **not** a panel-specific table (no `control_` prefix): it's also
read directly by processes outside `control/`, such as the future
ingest job worker, so it's treated as a business table like `stations`,
per the naming criteria in `spec/control/core.md`.

Natural key: `key`.

| Column        | Type        | Null | Description                                                        |
|---------------|-------------|------|----------------------------------------------------------------------|
| `key`         | `varchar`   | No   | Config key (primary key), `UPPER_SNAKE_CASE`. E.g. `POLL_INTERVAL_SECONDS`. |
| `value`       | `varchar`   | No   | Config value, stored as raw text; each consumer parses it to the type it expects. |
| `value_type`  | `varchar`   | No   | One of `string`, `secret`, `positive_integer` (see "Design notes") — governs how the panel validates an edit to `value`, and whether it's masked on read. |
| `description` | `varchar`   | No   | Human-readable explanation of what the key controls, shown in the panel. |
| `updated_at`  | `timestamp` | No   | Date/time of the last edit.                                          |

### Design notes

- **No `created_at`**: unlike tables fed by an ingestion process, rows
  here aren't created through normal app usage — they only exist
  because a migration seeded them (see "Seed data" below), and the
  panel only allows editing their `value` (see
  `spec/control/module/config.md`: no add/delete from the UI). A
  creation timestamp wouldn't carry meaningful information beyond "when
  this migration ran", so it's left out.
- **`value` always `varchar`**: keeping the column type generic avoids
  a schema change every time a new config key with a different
  underlying type is added; type conversion is the responsibility of
  whichever code reads a given key.
- **`value_type` drives per-key validation on edit — decided:**
  resolves the earlier open question of whether/how to validate a
  key's new value before saving it (see `spec/control/module/config.md`).
  Covers the types actually in use today:
  - **`string`**: non-empty after trimming.
  - **`secret`**: same validation as `string`, but the control panel's
    `GET /api/config/values` masks the value instead of returning it in
    plain text (a fixed placeholder, not derived from the real value's
    length) — see `spec/control/module/config.md`. Added after
    `AEMET_API_KEY` was returned in plain text by the config endpoint
    during development and got exposed in a terminal session; `string`
    alone didn't distinguish "safe to display" from "a credential".
    Used by `AEMET_API_KEY`.
  - **`positive_integer`**: parses as an integer, and is `> 0`. Used by
    `POLL_INTERVAL_SECONDS` and `SCHEDULER_MAX_DATE_RANGE`.
  Like `job_type`/`status` on `ingest_jobs`, `value_type` isn't
  DB-enforced (no `CHECK`): the service layer looks up the validator
  for a row's `value_type` and rejects an unrecognized one the same
  way it'd reject a bad value, so there's no gap in practice. New
  types are added here, and their validator implemented in the config
  module's service layer, as new kinds of keys need them — same
  incremental approach as seeding keys themselves (see "Seed data").
- **Keys are code-defined, not free-form**: the set of valid keys is
  implicitly defined by whichever part of the codebase reads them (e.g.
  the ingest worker reading `POLL_INTERVAL_SECONDS`). The panel doesn't
  allow creating or deleting keys — only migrations do — to avoid
  orphaned keys nothing reads, or missing keys some process expects.
- **Keys are `UPPER_SNAKE_CASE` — decided:** unlike every other
  identifier in the project (`snake_case`, see `spec/db/general.md`),
  config keys are uppercase, mirroring environment variable naming.
  Several keys started life as actual `.env` variables (e.g.
  `AEMET_API_KEY`), and the ones that didn't (e.g.
  `SCHEDULER_MAX_DATE_RANGE`) still read like one — keeping a single
  visual style for "a name you'd look up in config" regardless of
  where it happens to be stored.

### Seed data

- Each config key is inserted by its own migration at the point some
  part of the codebase starts needing it (same pattern as the
  `control_users` admin seed in `spec/db/tables.md`), rather than all
  being seeded up front.
- **`AEMET_API_KEY`** (`value_type: secret`) — the first key seeded
  (migrations `create_config_values` and
  `seed_config_value_aemet_api_key`; `value_type` started as `string`
  and was changed to `secret` by a later migration,
  `mark_aemet_api_key_as_secret`, once the masking behavior existed):
  AEMET OpenData's `api_key`, previously an `AEMET_API_KEY` variable in
  `.env`, now read here by `ingest/` (see `ingest/db.py`'s
  `get_config_value`, used by `ingest/aemet_client.py`) instead. The
  seed migration inserts a placeholder value (`CHANGE_ME`), not the
  real key — the real value is set with a direct `UPDATE` against the
  running database, never committed. `.env`'s `AEMET_API_KEY` isn't
  read by any code anymore, but hasn't been removed from `.env` yet.
- **`POLL_INTERVAL_SECONDS`** (`value_type: positive_integer`) — `300`
  (5 minutes). Seconds the job worker sleeps between poll iterations
  when there's nothing pending (see `spec/ingest/general.md`).
- **`SCHEDULER_MAX_DATE_RANGE`** (`value_type: positive_integer`) —
  `180` (days). Maximum date range a single `daily_values` job may
  cover — both the threshold the Jobs module enforces when queuing one
  (see `spec/control/module/jobs.md`) and the window the ingestion
  script itself uses against the AEMET endpoint (see
  `spec/ingest/DAILY_VALUES.md`), the same number reused for both.
- `value_type` was added to the table (and backfilled for these three
  keys) by a later migration, `add_value_type_to_config_values` — the
  table was created without it initially, before per-key validation
  was decided.

### Pending decisions

None.

## Table `ingest_jobs`

Queue of ingestion runs, one row per run requested from the control
panel's Jobs module (see
[`spec/control/module/jobs.md`](../control/module/jobs.md)) and
processed by the ingest job worker (see
[`spec/ingest/general.md`](../ingest/general.md)). Like `config_values`,
it's **not** a panel-specific table (no `control_` prefix): it's
written by `control/backend/` but read and updated by the worker
process in `ingest/`, so it's treated as a business/shared table, per
the naming criteria in `spec/control/core.md`.

No natural key: each row is a job execution request, not an entity.

| Column          | Type        | Null | Description                                                                 |
|-----------------|-------------|------|--------------------------------------------------------------------------------|
| `id`            | `bigint`    | No   | Auto-numbered technical identifier (primary key).                            |
| `job_type`      | `varchar`   | No   | Which ingestion script this job is for (e.g. `stations`, `daily_values`).      |
| `params`        | `jsonb`     | No   | Job-type-specific parameters (e.g. `{}` for `stations`; `{"station_code", "date_from", "date_to"}` for `daily_values`). |
| `status`        | `varchar`   | No   | One of `pending`, `running`, `success`, `error`, `cancelled`. Defaults to `pending`. |
| `created_at`    | `timestamp` | No   | Date/time the job was queued.                                                 |
| `started_at`    | `timestamp` | Yes  | Date/time the worker claimed the job.                                         |
| `finished_at`   | `timestamp` | Yes  | Date/time the job finished (success or error).                                |
| `rows_inserted` | `integer`   | Yes  | Rows inserted by the run, filled in by the worker when it finishes.           |
| `rows_updated`  | `integer`   | Yes  | Rows updated by the run, filled in by the worker when it finishes.            |
| `error_message` | `varchar`   | Yes  | Error detail, filled in by the worker if the run fails.                       |

### Design notes

- **Technical primary key**: same criteria as `stations_history` — each
  row is an event (a requested run), not an entity with its own
  natural identity.
- **`params` as `jsonb` instead of typed columns**: different job
  types need different parameters (`stations` needs none;
  `daily_values` needs a station and a date range; future job types
  will need whatever they need). A single flexible column lets the
  worker poll one table regardless of job type, and lets new
  ingestion scripts be added without a schema migration — only a new
  `job_type` value and its own dispatch logic in the worker (see
  `spec/ingest/general.md`).
- **`job_type` and `status` aren't DB-enforced (no `CHECK`/enum)**:
  same criteria as `control_users.login`'s email format — validated in
  the application layer (the jobs module's service when creating a
  job; the worker when transitioning status), not with a database
  constraint.
- **Claiming pattern**: the worker claims the oldest `pending` job with
  `SELECT ... WHERE status = 'pending' ORDER BY created_at LIMIT 1 FOR
  UPDATE SKIP LOCKED`, then updates it to `running` in the same
  transaction. This keeps things correct even if more than one worker
  process is ever run, though today there's only one (see
  `spec/ingest/general.md`).
- **No edit, but cancellable while `pending`**: a job's `params` can
  never be changed after creation (queue a new job instead). The one
  state change a user can trigger directly (as opposed to the worker)
  is cancelling a `pending` job (see `spec/control/module/jobs.md`);
  once a job is `running` it can no longer be cancelled, it runs to
  completion (`success`/`error`).
- **Deletable from the panel, any status — decided:** unlike cancelling
  (`pending` only), deleting a row has no status restriction — see
  "Pending decisions" below and `spec/control/module/jobs.md`,
  "Deleting jobs". Deleting a `running` job's row doesn't stop the
  worker (it isn't notified); the worker's later `UPDATE` when it
  finishes that job just affects zero rows, silently. This is an
  accepted, low-consequence edge case (the ingestion side effects
  already happened or are already in progress regardless of the
  `ingest_jobs` row) rather than something worth adding a status guard
  for.
- **Cancelling is a conditional update, not a check-then-update**:
  `UPDATE ingest_jobs SET status = 'cancelled' WHERE id = %(id)s AND
  status = 'pending'`, checking whether a row was actually affected.
  This avoids a race against the worker's own claim (`SELECT ... FOR
  UPDATE SKIP LOCKED` immediately followed by setting `running` in the
  same transaction, see above): if the worker claimed the job first,
  this `UPDATE` simply matches zero rows (the status is no longer
  `pending` by the time it runs) instead of cancelling a job that's
  already executing.
- **No `control_` prefix**: see the note at the top of this section.

### Pending decisions

None. **Retention — decided: no automatic policy.** Instead of a
background cleanup job or row cap, the Jobs module's history list
lets a user delete rows directly — single or multiple at once, see
`spec/control/module/jobs.md`, "Deleting jobs". Manual and on-demand,
same spirit as the jobs themselves (`spec/control/module/jobs.md`,
"Objective": nothing in this module runs on a schedule).

## Table `control_users`

Access accounts for the control panel, with the `control_` prefix
agreed in [`spec/control/core.md`](../control/core.md) (the only
exception to this document's "no technical prefixes" convention).
Managed from the control panel's security section (see
[`spec/control/module/security.md`](../control/module/security.md)),
not by an ingestion process.

| Column                | Type        | Null | Description                                                                 |
|-----------------------|-------------|------|--------------------------------------------------------------------------------|
| `id`                   | `bigint`    | No   | Auto-numbered technical identifier (primary key).                          |
| `login`                | `varchar`   | No   | Access identifier, email format. Unique.                                |
| `password_hash`        | `varchar`   | No   | Argon2id hash of the password. Never stored in plain text.                   |
| `created_at`           | `timestamp` | No   | Date/time the user was created.                                               |
| `updated_at`           | `timestamp` | No   | Date/time of the last modification (e.g. password change).             |

### Design notes

- **Technical primary key, not `login`**: although `login` is unique
  and stable in practice, the user edit screen
  (`spec/control/module/security.md`) allows modifying user data
  without explicitly excluding `login` itself; using an auto-numbered
  `id` as the primary key avoids a future `login` edit having to
  propagate the change to `control_sessions` or other tables
  referencing it.
- **`login` unique, email format**: the only format validation
  required (decided in `spec/control/module/security.md`); the format
  is validated in the backend's service layer (Pydantic), not with a
  database `CHECK`.
- **`password_hash`**: Argon2id algorithm, decided in
  `spec/control/core.md`. There's no complexity or password-history
  column: no additional rules are enforced.
- **Physical deletion**: deleting a user is a real `DELETE` (decided
  in `spec/control/module/security.md`), with no `active`-style
  status column.
- **Auditing**: `created_at` is set on creation; `updated_at` is
  refreshed on every edit (including a password change), same
  criteria as the rest of the project's tables (`spec/db/general.md`).
  It also powers the "by creation date" filter planned in the user
  listing (`spec/control/module/security.md`).

### Seed data

- **Default admin user**: migration
  `db/migrations/versions/20260824_1200_cbdb178fe390_seed_control_admin_user.py`
  inserts a default user (login `info@gallegovela.es` / password
  `admin`, stored as an Argon2id hash like any other user) so there's
  always a way to log into the control panel after rebuilding the
  database from scratch — there's no self-service signup, and creating
  a user through the API requires already being logged in (see
  `spec/control/module/security.md`). Change this password after first
  login in a real environment.
  - **Login corrected by a later migration**,
    `update_admin_user_login`: the original seed used
    `admin@weather.local`, which `pydantic`'s `EmailStr` rejects
    outright (`.local` is a reserved TLD by RFC — a syntax rule the
    login form's own validation enforces, not a network/deliverability
    check) — the seeded admin could never actually authenticate
    through the real API, only exist as a row in the database. Found
    by actually logging in through the API while testing the jobs
    module, not just checking the database.

### Pending decisions

- None beyond the ones already covered in
  `spec/control/module/security.md`.

## Table `control_sessions`

Server-side sessions for the control panel (opaque token, not JWT —
decided in [`spec/control/core.md`](../control/core.md)). One row per
active or historical session.

| Column                | Type        | Null | Description                                                                 |
|-----------------------|-------------|------|--------------------------------------------------------------------------------|
| `token`                | `varchar`   | No   | Opaque session identifier, generated at login (primary key).        |
| `user_id`              | `bigint`    | No   | Foreign key to `control_users.id`: the user owning the session.           |
| `started_at`           | `timestamp` | No   | Date/time of the login that created the session.                                     |

### Design notes

- **Natural primary key**: the `token` itself is the stable
  identifier the application receives on every request (`httpOnly`/
  `secure` cookie) to validate the session, so it's used directly as
  the primary key instead of adding a technical `id`.
- **No expiration column**: the session expires
  `CONTROL_SESSION_TTL_MINUTES` (environment variable, defaulting to
  15, see `spec/control/core.md`) after `started_at`, computed on
  every request by the security service layer; no expiration date is
  stored because the TTL is configurable and changing it shouldn't
  require rewriting already-created sessions.
- **No renewal**: `started_at` isn't updated with use (decided in
  `spec/control/core.md`); a session's validity is always counted
  from login.
- **Cascading delete**: deleting a user (`control_users`, physical
  deletion) also deletes their sessions (`ON DELETE CASCADE`), so a
  deleted user immediately loses access even if they had a still
  valid session.

### Pending decisions

- None beyond the ones already covered in `spec/control/core.md`.
