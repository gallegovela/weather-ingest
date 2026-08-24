# Module: Config

## Objective

Let an authenticated user view and edit the project's operational
key-value configuration (e.g. the future ingest job worker's polling
interval) from the control panel, without needing direct database
access. It's an **edit-only** module: the set of valid keys is defined
by whichever code reads them (see
[`spec/db/tables.md`](../../db/tables.md), table `config_values`), so
the panel only allows changing the `value` of existing keys — it
doesn't allow creating or deleting keys.

## Menu

One top-level "Config" entry in the side menu (see "Application
structure" in `core.md`), with a single subitem:

1. **Values** — list of config keys with their current value.

## Screens

### 1. Config values list

- Table listing every row in `config_values`: `key`, `description`,
  `value`, `updated_at`.
- **No filters, no pagination — decided.** The expected number of keys
  is small (a handful), so the shared "paginated listings with
  filters" convention (`core.md`, "REST API contract") doesn't apply
  here: the endpoint returns the full list in one call.
- **Edit only:** each row has an **Edit** action that opens a form
  with just the `value` field (`key` and `description` are read-only).
  There's no **add** or **delete** action — decided in "Objective"
  above.

## Data

Follows the layered architecture in `core.md`:

- **DAO** (`control/backend/modules/config/dao.py`): plain SQL
  (`psycopg` v3, no ORM) against `config_values`.
- **Service** (`service.py`): validates that the key being edited
  exists (`404` otherwise), then validates the new value against that
  row's `value_type` (see `spec/db/tables.md`, table `config_values`:
  `string` = non-empty, `positive_integer` = parses as an int `> 0`),
  rejecting with `400` if it doesn't match.
- **Control** (`router.py`): exposes the endpoints.

### Endpoints (REST API)

Following the contract fixed in `core.md`, with the exception noted
above (no pagination):

- `GET /api/config/values` — full list of config values, unpaginated.
- `PUT /api/config/values/{key}` — update the `value` of an existing
  key. `404` if the key doesn't exist.

## Pending decisions

None.
