# Module: Security

Special control panel module (see
[`spec/control/core.md`](../core.md)) that the rest of the
application depends on: it implements access to the app itself
(login) and the management of the accounts that can access it.

## Objective

- Authenticate users via **username and password** to access the
  panel (cross-cutting requirement defined in `core.md`).
- Allow managing (creating, editing, deleting) the user accounts that
  can authenticate in the panel, from a dedicated section within the
  already-logged-in application.

## No roles

This module **doesn't implement roles or differentiated
permissions**: every user who can authenticate has full access to
every section and module of the panel, including this security
section itself. There's therefore no "administrator" user distinct
from a "regular" user.

## Screens

### 1. Login

- Access screen described in `core.md` (blank page, centered form, no
  menu layout).
- Fields: **username** (email format) and **password**.
- On successful authentication, a session starts and the panel is
  accessed (layout with side menu); an authentication failure (user
  doesn't exist or wrong password) is always shown with the same
  generic message — **decided: "Error en los datos de entrada"** —
  without indicating which of the two fields failed.
- On authentication, `control/backend/` creates a server-side session
  with an opaque token (stored in `control_sessions`, expires 15
  minutes after login, no renewal) and the password is validated with
  an Argon2id hash — mechanism decided in `core.md`.

### 2. User list

Main screen of the security section once inside the panel (subitem of
the "Security" module in the side menu, see `core.md`).

- **Listing** of all existing users.
- **Search filters** on the listing (at least by username; more
  filters — e.g. by creation date — can be added once the user's final
  fields are defined).
- From this screen the three management operations are accessed:
  **add**, **edit** and **delete** users.

### 3. Add user

- Creation form with, at minimum, **username** (email format) and
  **password**.
- The newly created user can immediately authenticate at login with
  those credentials.

### 4. Edit user

- Edit form for an existing user.
- Allows modifying their data, including the **password** — it's the
  only way to change it (see "Password recovery"), whether the user
  themself changes it or another logged-in user resets it.

### 5. Delete user

- Deletion action on an existing user, with confirmation required
  before executing it (irreversible action: the deleted user can no
  longer authenticate).
- **Physical deletion — decided:** the deletion is permanent (a real
  `DELETE` on `control_users`, not an `active`-style status column).
  Being a low-activity internal panel, keeping a history of deleted
  users isn't justified.
- **A user can't delete themself — decided.** The delete action is
  disabled/hidden for the currently logged-in user; only other users
  can be deleted. This avoids ending up without a valid session
  mid-operation and, since there are no roles, also avoids the edge
  case of the last user deleting themself and nobody being able to
  get back into the panel.

### Password recovery

- **Decided: there's no self-service "recover password" option** (no
  recovery email, no security question, nothing similar). If a user
  forgets their password, another already logged-in user changes it
  from **User list → Edit user** (screen 4).

## Data

The panel's users are persisted in the PostgreSQL database shared with
the rest of the project, in a table with the `control_` prefix agreed
in `core.md` (`control_users`).

The formal column schema (types, primary key, whether deletion is
physical or logical, audit columns, etc.) is documented in
[`spec/db/tables.md`](../../db/tables.md) following the usual
`spec/db/general.md` workflow when this module's implementation is
tackled — this file only establishes the minimum functional content
that table must support:

- A unique user identifier (login), **in email format** (decided —
  it's the only format validation required; no additional password
  complexity rules).
- A password, always stored with an **Argon2id** hash (never in plain
  text — decided in `core.md`).

## Pending decisions

No open items in this module.
