# Control panel (core)

This document describes the **core** of the control panel
application: what it is, how it's organized into modules, and what's
implemented transversally (authentication, security). The detail of
each specific piece of panel functionality is documented in its own
file inside `spec/control/module/` (see below), not in this document.

## Objective

Web application (SPA) in **React** that serves as a control panel for
this project's backend (database and weather data ingestion,
described in `spec/db/` and `spec/ingest/`). Lets an authenticated
user supervise and operate the system without having to use the
command line or access the database directly.

- **App type:** SPA in **React.js**, consumed via a browser.
- **Data source:** the panel consumes data from the **same PostgreSQL
  database** used by the rest of the project (the one started by
  `docker-compose.yml`, see `spec/db/general.md`), not a separate
  database. For now the panel is only about **controlling the
  importer**; access is direct to the database. A **second phase** is
  planned in which the project will have its own data-consumption
  API, which will at that point replace this direct access — see the
  DAO layer in "Layered architecture" below, designed precisely to
  absorb that change without affecting the rest of the app.
- **Panel-specific tables:** any table the control panel needs for its
  own operation (e.g. access users) is created in that same database
  with the **`control_`** prefix (e.g. `control_users`), to
  distinguish them at a glance from business tables (`stations`,
  future `climatological_values`, etc.). They're managed the same way
  through `db/` migrations, with the same workflow as the rest of the
  tables (see [`spec/db/general.md`](../db/general.md)); it's the only
  exception to that document's "no technical prefixes" convention, and
  an underscore (`control_`) is used instead of a hyphen (`control-`)
  because PostgreSQL doesn't allow hyphens in unquoted identifiers,
  and the rest of the project follows `snake_case`.
- **Relationship to the rest of the project:** it's just another
  client of the backend/database; it doesn't replace the `ingest/`
  scripts or `db/`'s schema management, which remain independent (see
  `spec/db/general.md`).
- **Scope:** for now the core (modular architecture, layers,
  authentication, stack, deployment) and two modules are specified —
  `security` (login and user management) and `stations` (listing and
  map, the reference module). The rest of the panel's functionality
  (e.g. launching imports, viewing climatological value history) will
  be added as new, independent modules.

## Modular architecture

The application is organized into **modules**: independent functional
units of the panel (e.g. "stations", "imports", "security"). Each
module is specified in its own file inside:

```
spec/control/
├── core.md              # This document: cross-cutting core of the app
└── module/
    ├── security.md      # Login, user management (see Security section)
    ├── stations.md      # Station listing + map (first functional module)
    └── ...
```

- **`stations` is the reference module:** it's the first functional
  module built (beyond `security`, which is special), and it sets the
  implementation pattern — layers, paginated listings with filters,
  consuming the API from React — that's replicated in the following
  modules. Any new convention that comes up while building it (see
  "Paginated listings with filters" in "REST API contract") is
  documented here in the core so it's cross-cutting from the start.

- **A module = a folder/functional section of the panel of its own**,
  with its own `spec/control/module/<module>.md` file.
- Each module file documents its objective, the screens/views it's
  made of, the data it consumes or modifies, and any business rule of
  its own, following the same level of detail already used in
  `spec/db/` and `spec/ingest/`.
- The core (this document) covers only what's **cross-cutting to all
  modules**: general navigation, authentication, permissions, and the
  security section itself as the special module the rest depends on.
- As with the rest of the project (see CLAUDE.md), before working on
  any panel module you must review `core.md` in full in addition to
  the specific module's file, not just the latter.

## Layered architecture

**Cross-cutting concept for the whole application** (applies equally
to all modules, it's not a decision specific to any one of them): data
access and manipulation are always organized in three layers, with a
single dependency direction and no jumps between non-adjacent layers:

```
Control / View  →  Service  →  DAO  →  data source
```

- **Control/view layer:** the panel's screens (the React views
  described in each `spec/control/module/<module>.md`) together with
  the logic managing the user's interaction with them (which business
  action fires when a button is clicked, how the result is shown). It
  contains no business logic and doesn't know how or from where the
  data is obtained: it only invokes the service layer and renders its
  result. Implemented in **React.js**, running in the browser.
- **Service layer:** implements each module's business logic
  (validations, rules, orchestration of several operations if
  needed). It doesn't know **how** data is accessed nor where it comes
  from (database, API...), only which operation it needs from the DAO
  (e.g. "user with this login", "create station"). It's the only
  layer allowed to invoke the DAO.
- **DAO (Data Access Object) layer:** the single real point of access
  to the data. It's the **only** layer that knows how to obtain it. In
  this first phase, the DAO accesses **PostgreSQL directly** (plain
  SQL, same criteria already followed by `ingest/`, see
  `spec/db/general.md`: no ORM). Once the future data-consumption API
  exists (second phase, see Objective), the DAO is the only layer that
  will change — it'll switch to consuming that API instead of the
  database directly — without needing to touch the service or
  control/view layers.
- **Service and DAO technology — decided: Python + FastAPI.** Both
  layers live in a panel-specific backend, written in Python, exposed
  to the control/view layer (React) as a **REST API** (JSON over HTTP)
  consumed from the browser. Python is chosen instead of a unified
  JavaScript/Node stack to keep **a single language across the whole
  project's backend**, sharing conventions already established with
  `ingest/` and `db/` (plain SQL with `psycopg` v3, no ORM — see
  `spec/db/general.md`) instead of duplicating data access in a second
  ecosystem. Like `db/` and `ingest/`, this backend is its own module,
  independent in dependencies/virtual environment from the rest (see
  Project structure in `CLAUDE.md`).

**Code location — decided:** a new `control/` folder at the project
root, sibling to `db/`, `ingest/` and `spec/` (which remains
documentation-only, no code, per `CLAUDE.md`), and inside it
`frontend/` and `backend/`:

```
control/
├── frontend/          # React SPA (control/view layer)
└── backend/           # FastAPI API (service and DAO layers)
```

- `control/frontend/` — the React SPA.
- `control/backend/` — the FastAPI API, with its own internal service
  and DAO layers (see "Internal organization of `control/backend/`
  and `control/frontend/`" below).
- Both are documented under `spec/control/` (this `core.md` and
  `spec/control/module/`), but **their code lives outside `spec/`**,
  in `control/`, same as `ingest/`'s code lives outside
  `spec/ingest/`'s documentation.
- **Dependency rule:** each layer only knows and invokes the layer
  immediately below it. Control/view never accesses data by skipping
  the service, and the service never runs SQL (nor calls a future data
  API) by skipping the DAO.
- This separation is the whole reason the DAO layer exists: to
  isolate the data access point so that a change of source (from
  direct database access to the future data-consumption API) is a
  change **localized to that layer**, without redoing the rest of the
  application.
- Each module implements its own control/view, service and DAO
  following this same split; the detail of which operations each
  layer exposes for a given module is documented in its
  `spec/control/module/<module>.md` file.

## Internal organization of `control/backend/` and `control/frontend/`

**Cross-cutting concept**: inside each of the two `control/` projects,
the code is organized **module-first, layer within each module** —
not the other way around. Each module occupies a single self-contained
folder, with the same 1:1 correspondence that already exists between a
module and its `spec/control/module/<module>.md` file.

```
control/backend/
├── main.py                  # FastAPI startup, mounts each module's router
├── core/                     # cross-cutting: config (.env), opaque token/session, Postgres connection
│   ├── config.py
│   ├── db.py
│   └── auth.py                # FastAPI dependency that validates the session on each request
└── modules/
    ├── security/
    │   ├── router.py            # control layer (endpoints)
    │   ├── service.py           # service layer
    │   ├── dao.py                 # DAO layer
    │   └── schemas.py            # Pydantic request/response models
    └── stations/                # (future) same structure

control/frontend/src/
├── app/                      # cross-cutting: layout with side menu, router, session guard, Login
└── modules/
    ├── security/
    │   ├── UsersList.jsx
    │   ├── UserForm.jsx
    │   └── securityApi.js       # calls to control/backend (frontend's control/view layer)
    └── stations/                # (future)
```

- **A module = a folder** in `modules/`, both in `backend/` and in
  `frontend/`, containing its own layers (control/router, service, DAO
  in the backend; views and API calls in the frontend). Adding or
  removing a module doesn't touch other modules' folders.
- **`core/`/`app/` are the only cross-cutting folders**: what's common
  to all modules (configuration, database connection, session
  validation, layout, login) lives there, outside `modules/`.
- **Lazy loading per module (frontend):** this organization leaves the
  natural boundary to lazy-load each module on demand (e.g.
  `React.lazy(() => import('./modules/security'))` when entering that
  section of the menu), so the browser only downloads the code for the
  visited module instead of the whole panel at once. It isn't
  mandatory to implement it from the start, but the module-first
  structure leaves it available without reorganizing anything.

## Application structure

Basic web layout, common to every panel screen once logged in:

- **Left column:** navigation menu, fixed, organized by **modules**.
  Each module appears as a top-level menu group/entry, with its own
  subitems (the different screens/views that module defines in its
  `spec/control/module/<module>.md` file). The correspondence is
  direct: one spec module = one menu entry with its subitems.
- **Rest of the screen (right):** main content area, where the
  selected subitem's screen is rendered.

**Login page:** a blank screen (without the menu/column layout above,
since there's no session yet) with the login form centered: username
and password fields.

- Additional login security policies (e.g. captcha) will be added
  later — out of scope for now, see "Other cross-cutting decisions".

## Authentication

- **Cross-cutting concept for the whole application:** to access any
  section of the panel, the user must be **logged in**. No screen or
  module is accessible anonymously.
- The application requires **login via username and password**
  (login screen described above); there's no other session-creation
  mechanism (SSO, guests, etc.) for now.
- Without an active session, any panel route redirects to the login
  screen.

**Session mechanism — decided: server-side session with an opaque
token** (not JWT). On login, `control/backend/` generates a random
session identifier (opaque token, with no encoded information inside)
and persists it in a `control_sessions` database table, along with the
user and the start date. That token is delivered to `control/frontend/`
in an `httpOnly` and `secure` cookie, which the browser automatically
resends with every API request. On each request, the security service
layer validates the token against `control_sessions`.

- **Why an opaque token and not JWT:** by keeping session state on the
  server itself (Postgres), logging out or revoking a deleted user's
  access is as simple as deleting the `control_sessions` row — no
  extra infrastructure is needed (revocation lists, refresh tokens)
  that a JWT-based scheme would require.
- `control_sessions` is, like `control_users`, a panel-specific table
  (`control_` prefix), formally documented in `spec/db/tables.md`.
- **Expiration — decided: 15 minutes by default, configurable.** 15
  minutes after login, the session stops being valid and the user is
  sent back to the login screen. The value isn't hardcoded: it's read
  from a new `.env` environment variable (`CONTROL_SESSION_TTL_MINUTES`,
  default value `15`), alongside the rest of the project's
  configuration (`AEMET_API_KEY`, `DATABASE_URL`).
- **No renewal — decided:** the session is **not renewed** with use;
  the 15 minutes are always counted from login, not from the last
  activity. On expiry, the user simply logs back in; there's no task
  in the panel that needs to be resumed after expiry, so the
  complexity of automatic renewal isn't justified.

**Password hashing — decided: Argon2id** (algorithm currently
recommended by OWASP), used to store `control_users` passwords; the
password is never stored or transmitted in plain text beyond the
login request over HTTPS.

## Security section

The panel includes a **security** section, accessible only to already
authenticated users, from which the application's own access accounts
are managed:

- **User creation:** creating new users (username and password) who
  will be able to authenticate in the panel.
- **User deletion:** removing existing users, who immediately lose the
  ability to access the panel.

The detail of this section (screens, creation form fields,
validations, who can manage users, whether there are differentiated
roles/permissions, whether deletion is physical or logical, etc.) is
documented in `spec/control/module/security.md` when its
implementation is tackled; this document only establishes that the
functionality exists and that it's cross-cutting (it affects
authentication for the whole app).

## Frontend technical stack

- **Decided:** `control/frontend/` is built with **Vite** (build and
  dev server), **react-router-dom** for routing between
  screens/modules, **TanStack Query** for API calls (caching,
  loading/error states, instead of a global state manager like Redux)
  and **Mantine** as the UI styling/component library (forms with
  `@mantine/form`, tables, confirmation modals for destructive actions
  like deleting a user, and the left-menu-column + content layout
  described in "Application structure").

## REST API contract

**Cross-cutting concept:** every module exposes its API following the
same conventions, so `control/frontend/` consumes them uniformly.

- **Routes:** `/api/<module>/<resource>` pattern (e.g.
  `/api/security/users`, `/api/security/users/{id}`).
- **HTTP verbs:** standard — `GET` to list/read, `POST` to create,
  `PUT`/`PATCH` to edit, `DELETE` to delete.
- **Errors:** FastAPI's default format — HTTP status code (`400`,
  `401`, `404`, etc.) plus a `{"detail": "message"}` body.
- Each module documents in its `spec/control/module/<module>.md` file
  the specific routes it exposes, always following this contract.
- **Paginated listings with filters:** shared convention for any
  listing screen in the panel (first set by the `stations` module, see
  `spec/control/module/stations.md`, and reused by the following
  modules): `page` and `page_size` query parameters for pagination; a
  query parameter per filterable field, with the same name as the
  column; for text (`varchar`) the filter is "contains" (not exact);
  for numeric and date fields it filters by range with `_from`/`_to`
  suffixes (e.g. `altitude_from`, `altitude_to`, `created_at_from`).

## Other cross-cutting decisions

- **Roles and permissions:** confirmed that **there will be no
  roles** (see `spec/control/module/security.md`); every logged-in
  user has the same access to all panel sections.
- **Login security policies:** captcha and similar, explicitly
  postponed (see Application structure).

## Deployment

- **Decided: containerized with Docker**, same as is already done
  today with PostgreSQL (`docker-compose.yml`, project root — see
  `spec/db/general.md`). `control/backend/` and `control/frontend/`
  will each have their own `Dockerfile`, and will be added as new
  services to the existing `docker-compose.yml`, alongside the
  already-defined `postgres` service.
- **Production server — decided:** an **nginx** is already set up on
  the target server, managed **outside this project**. The
  adjustments needed on that nginx (domain, TLS, etc.) are external
  configuration to this app and aren't documented here. Within this
  project's scope is only bringing up the containers; the external
  routing towards them is a separate responsibility.
- **The `control-frontend` container itself already proxies `/api`**
  to `control-backend` (see `control/frontend/nginx.conf`), resolving
  the service name through the docker-compose network. This makes the
  stack work autonomously with `docker compose up` locally (without
  depending on the target server's external nginx) and also serves
  production: the external nginx can keep routing `/api` directly to
  `control-backend`, or simply forward all traffic to
  `control-frontend` and let this internal proxy resolve `/api`.
