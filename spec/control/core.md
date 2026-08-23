# Panel de control (core)

Este documento describe el **núcleo** de la aplicación de panel de
control: qué es, cómo se organiza en módulos y qué hay implementado
de forma transversal (autenticación, seguridad). El detalle de cada
funcionalidad concreta del panel se documenta en un fichero propio
dentro de `spec/control/module/` (ver más abajo), no en este
documento.

## Objetivo

Aplicación web (SPA) en **React** que sirve de panel de control para
el backend de este proyecto (base de datos e ingesta de datos
meteorológicos descritos en `spec/db/` y `spec/importa/`). Permite a
un usuario autenticado supervisar y operar el sistema sin tener que
usar la línea de comandos o acceder directamente a la base de datos.

- **Tipo de app:** SPA en **React.js**, consumida vía navegador.
- **Origen de los datos:** el panel consume datos de la **misma base
  de datos PostgreSQL** que usa el resto del proyecto (la que levanta
  `docker-compose.yml`, ver `spec/db/general.md`), no una base de
  datos aparte. Por ahora el panel es únicamente de **control del
  importador**; el acceso es directo a la base de datos. Está
  previsto que en una **segunda fase** exista una API de consumo de
  datos propia del proyecto, que en su momento sustituirá este acceso
  directo — ver la capa de DAO en "Arquitectura en capas" más abajo,
  pensada precisamente para absorber ese cambio sin afectar al resto
  de la app.
- **Tablas propias del panel:** cualquier tabla que necesite el panel
  de control para su propio funcionamiento (ej. usuarios de acceso)
  se crea en esa misma base de datos con el prefijo **`control_`**
  (ej. `control_usuarios`), para distinguirlas a simple vista de las
  tablas de negocio (`estaciones`, futuras `valores_climatologicos`,
  etc.). Se gestionan igualmente mediante migraciones de `db/`, con el
  mismo flujo que el resto de tablas (ver
  [`spec/db/general.md`](../db/general.md)); es la única excepción a
  la convención de "sin prefijos técnicos" de ese documento, y se usa
  guión bajo (`control_`) en vez de guión (`control-`) porque
  PostgreSQL no admite guiones en identificadores sin comillas, y el
  resto del proyecto sigue `snake_case`.
- **Relación con el resto del proyecto:** es un cliente más del
  backend/base de datos; no sustituye a los scripts de `importa/` ni
  a la gestión de esquema de `db/`, que siguen siendo independientes
  (ver `spec/db/general.md`).
- **Alcance:** especificados por ahora el core (arquitectura modular,
  capas, autenticación, stack, despliegue) y dos módulos —
  `seguridad` (login y gestión de usuarios) y `estaciones` (listado y
  mapa, módulo de referencia). El resto de funcionalidades del panel
  (ej. lanzar importaciones, ver histórico de valores climatológicos)
  se irán añadiendo como nuevos módulos independientes.

## Arquitectura modular

La aplicación se organiza en **módulos**: unidades funcionales
independientes del panel (ej. "estaciones", "importaciones",
"seguridad"). Cada módulo se especifica en su propio fichero dentro
de:

```
spec/control/
├── core.md              # Este documento: núcleo transversal de la app
└── module/
    ├── seguridad.md      # Login, gestión de usuarios (ver sección Seguridad)
    ├── estaciones.md      # Listado + mapa de estaciones (primer módulo funcional)
    └── ...
```

- **`estaciones` es el módulo de referencia:** es el primer módulo
  funcional que se construye (más allá de `seguridad`, que es
  especial), y sienta el patrón de implementación — capas, listados
  paginados con filtros, consumo de la API desde React — que se
  replica en los módulos siguientes. Cualquier convención nueva que
  aparezca al construirlo (ver "Listados paginados con filtros" en
  "Contrato de la API REST") se documenta aquí en el core para que
  sea transversal desde el principio.

- **Un módulo = una carpeta/sección funcional propia del panel**,
  con su propio fichero `spec/control/module/<modulo>.md`.
- Cada fichero de módulo documenta su objetivo, las pantallas/vistas
  que lo componen, los datos que consume o modifica y cualquier
  regla de negocio propia, siguiendo el mismo criterio de detalle
  que ya se usa en `spec/db/` y `spec/importa/`.
- El core (este documento) recoge únicamente lo que es **transversal
  a todos los módulos**: navegación general, autenticación, permisos
  y la propia sección de seguridad como módulo especial del que
  depende el resto.
- Como en el resto del proyecto (ver CLAUDE.md), antes de trabajar en
  cualquier módulo del panel hay que revisar `core.md` completo además
  del fichero del módulo concreto, no solo este último.

## Arquitectura en capas

Concepto **transversal a toda la aplicación** (aplica a todos los
módulos por igual, no es una decisión particular de ninguno de
ellos): el acceso y la manipulación de datos se organizan siempre en
tres capas, con una única dirección de dependencia y sin saltos entre
capas no adyacentes:

```
Control / Visualización  →  Servicio  →  DAO  →  origen de datos
```

- **Capa de control/visualización:** las pantallas del panel (las
  vistas React descritas en cada `spec/control/module/<modulo>.md`)
  junto con la lógica que gestiona la interacción del usuario con
  ellas (qué acción de negocio se dispara al pulsar un botón, cómo se
  muestra el resultado). No contiene lógica de negocio ni sabe cómo
  ni de dónde se obtienen los datos: solo invoca a la capa de
  servicio y renderiza su resultado. Se implementa en **React.js**,
  ejecutada en el navegador.
- **Capa de servicio:** implementa la lógica de negocio de cada
  módulo (validaciones, reglas, orquestación de varias operaciones si
  hiciera falta). No sabe **cómo** se accede a los datos ni de dónde
  vienen (base de datos, API...), solo qué operación necesita del DAO
  (ej. "usuario con este login", "crear estación"). Es la única capa
  que puede invocar al DAO.
- **Capa de DAO (Data Access Object):** único punto de acceso real a
  los datos. Es la **única** capa que sabe cómo obtenerlos. En esta
  primera fase, el DAO accede **directamente a PostgreSQL** (SQL puro,
  mismo criterio que ya sigue `importa/`, ver `spec/db/general.md`:
  sin ORM). Cuando exista la futura API de consumo de datos (segunda
  fase, ver Objetivo), el DAO es la única capa que cambiará —
  pasará a consumir esa API en vez de la base de datos directamente
  — sin necesidad de tocar la capa de servicio ni la de
  control/visualización.
- **Tecnología de servicio y DAO — decidido: Python + FastAPI.**
  Ambas capas viven en un backend propio del panel, escrito en
  Python, expuesto a la capa de control/visualización (React) como
  una **API REST** (JSON sobre HTTP) consumida desde el navegador. Se
  elige Python en vez de un stack unificado en JavaScript/Node para
  mantener **un único lenguaje en todo el backend del proyecto**,
  compartiendo convenciones ya establecidas con `importa/` y `db/`
  (SQL puro con `psycopg` v3, sin ORM — ver `spec/db/general.md`) en
  vez de duplicar el acceso a datos en un segundo ecosistema. Igual
  que `db/` e `importa/`, este backend es un módulo propio,
  independiente en dependencias/entorno virtual del resto (ver
  Estructura del proyecto en `CLAUDE.md`).

**Ubicación del código — decidido:** una carpeta nueva `control/` en
la raíz del proyecto, hermana de `db/`, `importa/` y `spec/` (que
sigue siendo solo documentación, sin código, según `CLAUDE.md`), y
dentro de ella `frontend/` y `backend/`:

```
control/
├── frontend/          # SPA React (capa de control/visualización)
└── backend/           # API FastAPI (capas de servicio y DAO)
```

- `control/frontend/` — la SPA React.
- `control/backend/` — la API FastAPI, con sus propias capas
  internas de servicio y DAO (ver "Organización interna de
  `control/backend/` y `control/frontend/`" más abajo).
- Ambas se documentan bajo `spec/control/` (este `core.md` y
  `spec/control/module/`), pero **su código vive fuera de `spec/`**,
  en `control/`, igual que el código de `importa/` vive fuera de la
  documentación de `spec/importa/`.
- **Regla de dependencia:** cada capa solo conoce e invoca a la capa
  inmediatamente inferior. Control/visualización nunca accede a datos
  saltándose el servicio, y el servicio nunca ejecuta SQL (ni llama a
  una futura API de datos) saltándose el DAO.
- Esta separación es la razón de ser de la capa de DAO: aislar el
  punto de acceso a los datos para que un cambio de origen (de base
  de datos directa a la futura API de consumo) sea un cambio
  **localizado en esa capa**, sin rehacer el resto de la aplicación.
- Cada módulo implementa sus propias control/visualización, servicio
  y DAO siguiendo esta misma división; el detalle de qué operaciones
  expone cada capa para un módulo concreto se documenta en su fichero
  `spec/control/module/<modulo>.md`.

## Organización interna de `control/backend/` y `control/frontend/`

Concepto **transversal**: dentro de cada uno de los dos proyectos de
`control/`, el código se organiza **por módulo primero, por capa
dentro de cada módulo** — no al revés. Cada módulo ocupa una única
carpeta autocontenida, con la misma correspondencia 1:1 que ya existe
entre un módulo y su fichero `spec/control/module/<modulo>.md`.

```
control/backend/
├── main.py                  # arranque FastAPI, monta el router de cada módulo
├── core/                     # transversal: config (.env), sesión/token opaco, conexión a Postgres
│   ├── config.py
│   ├── db.py
│   └── auth.py                # dependencia FastAPI que valida la sesión en cada request
└── modulos/
    ├── seguridad/
    │   ├── router.py            # capa control (endpoints)
    │   ├── servicio.py           # capa servicio
    │   ├── dao.py                 # capa DAO
    │   └── esquemas.py            # modelos Pydantic de petición/respuesta
    └── estaciones/                # (futuro) misma estructura

control/frontend/src/
├── app/                      # transversal: layout con menú lateral, router, guard de sesión, Login
└── modulos/
    ├── seguridad/
    │   ├── ListadoUsuarios.jsx
    │   ├── FormularioUsuario.jsx
    │   └── seguridadApi.js       # llamadas a control/backend (capa control/visualización del front)
    └── estaciones/                # (futuro)
```

- **Un módulo = una carpeta** en `modulos/`, tanto en `backend/` como
  en `frontend/`, que contiene sus propias capas (control/router,
  servicio, DAO en el backend; vistas y llamadas a la API en el
  frontend). Añadir o quitar un módulo no toca carpetas de otros
  módulos.
- **`core/`/`app/` son las únicas carpetas transversales**: lo común
  a todos los módulos (configuración, conexión a base de datos,
  validación de sesión, layout, login) vive ahí, fuera de
  `modulos/`.
- **Carga diferida por módulo (frontend):** esta organización deja el
  límite natural para cargar cada módulo bajo demanda (ej.
  `React.lazy(() => import('./modulos/seguridad'))` al entrar en esa
  sección del menú), de modo que el navegador solo descarga el código
  del módulo visitado en vez de todo el panel de una vez. No es
  obligatorio implementarlo desde el primer momento, pero la
  estructura módulo-primero lo deja disponible sin reorganizar nada.

## Estructura de la aplicación

Layout web básico, común a todas las pantallas del panel una vez
logado:

- **Columna izquierda:** menú de navegación, fijo, organizado por
  **módulos**. Cada módulo aparece como un grupo/entrada de primer
  nivel del menú, con sus propios subitems (las distintas
  pantallas/vistas que define ese módulo en su fichero
  `spec/control/module/<modulo>.md`). La correspondencia es directa:
  un módulo de la spec = una entrada de menú con sus subitems.
- **Resto de la pantalla (derecha):** área de contenido principal,
  donde se renderiza la pantalla del subitem seleccionado.

**Página de login:** pantalla en blanco (sin el layout de
menú/columna anterior, ya que todavía no hay sesión) con el
formulario de login centrado: campos de usuario y contraseña.

- Más adelante se añadirán políticas de seguridad adicionales sobre
  esta pantalla (ej. captcha) — por ahora queda fuera de alcance, ver
  "Otras decisiones transversales".

## Autenticación

- **Concepto transversal a toda la aplicación:** para acceder a
  cualquier sección del panel, el usuario debe estar **logado**. No
  existe ninguna pantalla ni módulo accesible de forma anónima.
- La aplicación requiere **login mediante usuario y contraseña**
  (pantalla de login descrita arriba); no hay otro mecanismo de alta
  de sesión (SSO, invitados, etc.) por ahora.
- Sin sesión iniciada, cualquier ruta del panel redirige a la
  pantalla de login.

**Mecanismo de sesión — decidido: sesión de servidor con token
opaco** (no JWT). Al hacer login, `control/backend/` genera un
identificador de sesión aleatorio (token opaco, sin información
codificada dentro) y lo persiste en una tabla `control_sesiones` de
la base de datos, junto con el usuario y la fecha de inicio. Ese
token se entrega al `control/frontend/` en una cookie `httpOnly` y
`secure`,
que el navegador reenvía automáticamente en cada petición a la API.
En cada petición, la capa de servicio de seguridad valida el token
contra `control_sesiones`.

- **Por qué token opaco y no JWT:** al mantener el estado de la
  sesión en el propio servidor (Postgres), cerrar sesión o revocar el
  acceso de un usuario eliminado es tan simple como borrar la fila de
  `control_sesiones` — no hace falta infraestructura adicional
  (listas de revocación, tokens de refresco) que sí necesitaría un
  esquema con JWT.
- `control_sesiones` es, igual que `control_usuarios`, una tabla
  propia del panel (prefijo `control_`), documentada formalmente en
  `spec/db/tables.md` cuando se implemente.
- **Expiración — decidido: 15 minutos por defecto, configurable.**
  Pasados 15 minutos desde el login, la sesión deja de ser válida y
  el usuario vuelve a la pantalla de login. El valor no se fija en
  código: se lee de una variable de entorno nueva en `.env` (ej.
  `CONTROL_SESSION_TTL_MINUTOS`, valor por defecto `15`), junto al
  resto de configuración del proyecto (`AEMET_API_KEY`,
  `DATABASE_URL`).
- **Sin renovación — decidido:** la sesión **no se renueva** con el
  uso; los 15 minutos se cuentan siempre desde el login, no desde la
  última actividad. Al caducar, el usuario simplemente vuelve a
  iniciar sesión; no hay ninguna tarea en el panel que necesite
  retomarse tras la caducidad, así que no se justifica la complejidad
  de una renovación automática.

**Hashing de contraseñas — decidido: Argon2id** (algoritmo
recomendado actualmente por OWASP), usado para almacenar las
contraseñas de `control_usuarios`; nunca se guarda ni se transmite la
contraseña en claro más allá de la petición de login sobre HTTPS.

## Sección de seguridad

El panel incluye una sección de **seguridad**, accesible solo a
usuarios ya autenticados, desde la que se gestionan las cuentas de
acceso a la propia aplicación:

- **Alta de usuarios:** creación de nuevos usuarios (usuario y
  contraseña) que podrán autenticarse en el panel.
- **Baja de usuarios:** eliminación de usuarios existentes, que
  pierden inmediatamente la posibilidad de acceder al panel.

El detalle de esta sección (pantallas, campos del formulario de alta,
validaciones, quién puede gestionar usuarios, si hay roles/permisos
diferenciados, si la baja es física o lógica, etc.) se documentará en
`spec/control/module/seguridad.md` cuando se aborde su
implementación; este documento solo fija que la funcionalidad existe
y que es transversal (afecta a la autenticación de toda la app).

## Stack técnico del frontend

- **Decidido:** `control/frontend/` se construye con **Vite** (build
  y servidor de desarrollo), **react-router-dom** para el enrutado
  entre pantallas/módulos, **TanStack Query** para las llamadas a la
  API (caché, estados de carga/error, en vez de un gestor de estado
  global tipo Redux) y **Mantine** como librería de estilos/
  componentes UI (formularios con `@mantine/form`, tablas, modales de
  confirmación para acciones destructivas como eliminar un usuario, y
  el layout de columna izquierda de menú + contenido descrito en
  "Estructura de la aplicación").

## Contrato de la API REST

Concepto **transversal**: todos los módulos exponen su API con las
mismas convenciones, para que `control/frontend/` los consuma de
forma uniforme.

- **Rutas:** patrón `/api/<modulo>/<recurso>` (ej.
  `/api/seguridad/usuarios`, `/api/seguridad/usuarios/{id}`).
- **Verbos HTTP:** estándar — `GET` para listar/leer, `POST` para
  crear, `PUT`/`PATCH` para editar, `DELETE` para eliminar.
- **Errores:** formato por defecto de FastAPI — código de estado HTTP
  (`400`, `401`, `404`, etc.) más un cuerpo `{"detail": "mensaje"}`.
- Cada módulo documenta en su fichero `spec/control/module/<modulo>.md`
  las rutas concretas que expone, siguiendo siempre este contrato.
- **Listados paginados con filtros:** convención común para cualquier
  pantalla de listado del panel (la fija por primera vez el módulo
  `estaciones`, ver `spec/control/module/estaciones.md`, y la
  reutilizan los módulos siguientes): parámetros de query `pagina` y
  `tamano_pagina` para la paginación; un parámetro de query por cada
  campo filtrable, con el mismo nombre que la columna; en texto
  (`varchar`) el filtro es "contiene" (no exacto); en numéricos y
  fechas se filtra por rango con sufijos `_desde`/`_hasta` (ej.
  `altitud_desde`, `altitud_hasta`, `fecha_alta_desde`).

## Otras decisiones transversales

- **Roles y permisos:** confirmado que **no habrá roles** (ver
  `spec/control/module/seguridad.md`); todo usuario logado tiene el
  mismo acceso a todas las secciones del panel.
- **Políticas de seguridad del login:** captcha y similares,
  explícitamente pospuesto (ver Estructura de la aplicación).

## Despliegue

- **Decidido: contenedorizado con Docker**, igual que ya se hace hoy
  con PostgreSQL (`docker-compose.yml`, raíz del proyecto — ver
  `spec/db/general.md`). `control/backend/` y `control/frontend/`
  tendrán cada uno su propio `Dockerfile`, y se añadirán como
  servicios nuevos al `docker-compose.yml` existente, junto al
  servicio `postgres` ya definido.
- **Servidor de producción — decidido:** ya existe un **nginx**
  montado en el servidor de destino, gestionado **fuera de este
  proyecto**. Los ajustes necesarios en ese nginx (proxy hacia los
  contenedores `control/backend/` y `control/frontend/`, dominio,
  TLS, etc.) son configuración externa a esta app y no se documentan
  aquí. Dentro del alcance de este proyecto solo entra levantar los
  contenedores; el enrutado externo hacia ellos es responsabilidad
  aparte.
