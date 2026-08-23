"""Capa de control (endpoints) del módulo seguridad.

Rutas bajo /api/seguridad, siguiendo el contrato REST transversal de
spec/control/core.md.
"""

from datetime import date

from fastapi import APIRouter, Cookie, Depends, Response, status
from psycopg import Connection

from core.auth import COOKIE_NAME, UsuarioActual, usuario_actual
from core.db import get_db
from core.esquemas import Listado
from modulos.seguridad import servicio
from modulos.seguridad.esquemas import LoginRequest, SesionOut, UsuarioCrear, UsuarioEditar, UsuarioOut

router = APIRouter(prefix="/api/seguridad", tags=["seguridad"])


def _a_usuario_out(fila: tuple) -> UsuarioOut:
    return UsuarioOut(id=fila[0], login=fila[1], fecha_alta=fila[2], fecha_actualizacion=fila[3])


@router.post("/login")
def iniciar_sesion(datos: LoginRequest, response: Response, conn: Connection = Depends(get_db)):
    token = servicio.login(conn, datos.login, datos.contrasena)
    response.set_cookie(COOKIE_NAME, token, httponly=True, secure=True, samesite="lax")
    return {"detail": "ok"}


@router.post("/logout")
def cerrar_sesion(
    response: Response,
    control_session: str | None = Cookie(default=None),
    usuario: UsuarioActual = Depends(usuario_actual),
    conn: Connection = Depends(get_db),
):
    if control_session:
        servicio.logout(conn, control_session)
    response.delete_cookie(COOKIE_NAME)
    return {"detail": "ok"}


@router.get("/sesion", response_model=SesionOut)
def obtener_sesion(usuario: UsuarioActual = Depends(usuario_actual)):
    # Usado por control/frontend/ como guard de sesión (¿hay sesión válida?)
    # y para conocer el id del usuario logado (ocultar "eliminar" sobre uno
    # mismo, ver spec/control/module/seguridad.md).
    return SesionOut(id=usuario.id, login=usuario.login)


@router.get("/usuarios", response_model=Listado[UsuarioOut])
def listar_usuarios(
    pagina: int = 1,
    tamano_pagina: int = 20,
    login: str | None = None,
    fecha_alta_desde: date | None = None,
    fecha_alta_hasta: date | None = None,
    usuario: UsuarioActual = Depends(usuario_actual),
    conn: Connection = Depends(get_db),
):
    filas, total = servicio.listar_usuarios(
        conn, pagina, tamano_pagina, login, fecha_alta_desde, fecha_alta_hasta
    )
    return Listado(
        items=[_a_usuario_out(f) for f in filas], total=total, pagina=pagina, tamano_pagina=tamano_pagina
    )


@router.post("/usuarios", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    datos: UsuarioCrear,
    usuario: UsuarioActual = Depends(usuario_actual),
    conn: Connection = Depends(get_db),
):
    return _a_usuario_out(servicio.crear_usuario(conn, datos.login, datos.contrasena))


@router.put("/usuarios/{usuario_id}", response_model=UsuarioOut)
def editar_usuario(
    usuario_id: int,
    datos: UsuarioEditar,
    usuario: UsuarioActual = Depends(usuario_actual),
    conn: Connection = Depends(get_db),
):
    return _a_usuario_out(
        servicio.editar_usuario(conn, usuario_id, login=datos.login, contrasena=datos.contrasena)
    )


@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    usuario_id: int,
    usuario: UsuarioActual = Depends(usuario_actual),
    conn: Connection = Depends(get_db),
):
    servicio.eliminar_usuario(conn, usuario_id, usuario.id)
