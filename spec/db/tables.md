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
  inserts a default user (`admin@weather.local` / password `admin`,
  stored as an Argon2id hash like any other user) so there's always a
  way to log into the control panel after rebuilding the database
  from scratch — there's no self-service signup, and creating a user
  through the API requires already being logged in (see
  `spec/control/module/security.md`). Change this password after
  first login in a real environment.

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
