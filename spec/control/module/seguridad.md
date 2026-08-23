# Módulo: Seguridad

Módulo especial del panel de control (ver
[`spec/control/core.md`](../core.md)) del que depende el resto de la
aplicación: implementa el acceso a la propia app (login) y la gestión
de las cuentas que pueden acceder a ella.

## Objetivo

- Autenticar usuarios mediante **usuario y contraseña** para poder
  acceder al panel (requisito transversal definido en `core.md`).
- Permitir gestionar (alta, edición, baja) las cuentas de usuario que
  pueden autenticarse en el panel, desde una sección propia dentro de
  la aplicación ya logada.

## Sin roles

Este módulo **no implementa roles ni permisos diferenciados**: todo
usuario que pueda autenticarse tiene acceso completo a todas las
secciones y módulos del panel, incluida esta misma sección de
seguridad. No existe por tanto un usuario "administrador" distinto de
un usuario "normal".

## Pantallas

### 1. Login

- Pantalla de acceso descrita en `core.md` (página en blanco,
  formulario centrado, sin el layout de menú).
- Campos: **usuario** (formato email) y **contraseña**.
- Al autenticar correctamente, se inicia sesión y se accede al panel
  (layout con menú lateral); un fallo de autenticación (usuario no
  existe o contraseña incorrecta) se muestra siempre con el mismo
  mensaje genérico — **decidido: "Error en los datos de entrada"**
  —, sin indicar cuál de los dos campos ha fallado.
- Al autenticar, `control/backend/` crea una sesión de servidor con
  token opaco (guardada en `control_sesiones`, expira a los 15
  minutos desde el login, sin renovación) y la contraseña se valida
  con hash Argon2id — mecanismo decidido en `core.md`.

### 2. Listado de usuarios

Pantalla principal de la sección de seguridad una vez dentro del
panel (subitem del módulo "Seguridad" en el menú lateral, ver
`core.md`).

- **Listado** de todos los usuarios existentes.
- **Filtros de búsqueda** sobre el listado (al menos por nombre de
  usuario; se podrán añadir más filtros — ej. por fecha de alta —
  cuando se definan los campos finales del usuario).
- Desde esta pantalla se accede a las tres operaciones de gestión:
  **añadir**, **editar** y **eliminar** usuarios.

### 3. Añadir usuario

- Formulario de alta con, como mínimo, **usuario** (formato email) y
  **contraseña**.
- El usuario recién creado puede autenticarse de inmediato en el
  login con esas credenciales.

### 4. Editar usuario

- Formulario de edición sobre un usuario existente.
- Permite modificar sus datos, incluida la **contraseña** — es la
  única vía para cambiarla (ver "Recuperación de contraseña"), tanto
  si la cambia el propio usuario como si se la resetea otro usuario
  logado.

### 5. Eliminar usuario

- Acción de baja sobre un usuario existente, con confirmación previa
  antes de ejecutarla (acción irreversible: el usuario eliminado deja
  de poder autenticarse).
- **Baja física — decidido:** el borrado es definitivo (`DELETE` real
  sobre `control_usuarios`, no una columna de estado tipo `activo`).
  Al ser un panel interno de baja actividad, no se justifica guardar
  histórico de usuarios eliminados.
- **Un usuario no puede eliminarse a sí mismo — decidido.** La acción
  de eliminar se deshabilita/oculta sobre el propio usuario logado;
  solo se puede eliminar a otros usuarios. Evita el caso de quedarse
  sin sesión válida a media operación y, al no haber roles, evita
  también el caso límite de que el último usuario se elimine a sí
  mismo y nadie pueda volver a entrar al panel.

### Recuperación de contraseña

- **Decidido: no existe una opción de "recuperar contraseña"**
  autoservicio (no hay email de recuperación, ni pregunta de
  seguridad, ni nada similar). Si un usuario olvida su contraseña,
  otro usuario ya logado se la cambia desde el **listado de
  usuarios → Editar usuario** (pantalla 4).

## Datos

Los usuarios del panel se persisten en la base de datos PostgreSQL
compartida con el resto del proyecto, en una tabla con el prefijo
`control_` acordado en `core.md` (`control_usuarios`).

El esquema formal de columnas (tipos, clave primaria, si la baja es
física o lógica, columnas de auditoría, etc.) se documentará en
[`spec/db/tables.md`](../../db/tables.md) siguiendo el flujo habitual
de `spec/db/general.md` cuando se aborde la implementación de este
módulo — este fichero fija el contenido funcional mínimo que esa
tabla debe soportar:

- Un identificador de usuario (login) único, **con formato email**
  (decidido — es la única validación de formato que se exige; sin
  reglas adicionales de complejidad de contraseña).
- Una contraseña, almacenada siempre con hash **Argon2id** (nunca en
  claro — decidido en `core.md`).

## Pendiente de definir

Sin pendientes abiertos en este módulo.
