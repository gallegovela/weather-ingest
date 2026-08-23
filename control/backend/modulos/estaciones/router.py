"""Capa de control (endpoints) del módulo estaciones.

Un único endpoint reutilizado por el listado y el mapa (sin paginar,
omitiendo tamano_pagina — decidido en
spec/control/module/estaciones.md).
"""

from datetime import date

from fastapi import APIRouter, Depends
from psycopg import Connection

from core.auth import UsuarioActual, usuario_actual
from core.db import get_db
from core.esquemas import Listado
from modulos.estaciones import servicio
from modulos.estaciones.esquemas import EstacionOut

router = APIRouter(prefix="/api/estaciones", tags=["estaciones"])


def _a_estacion_out(fila: tuple) -> EstacionOut:
    (
        indicativo, nombre, provincia, latitud, longitud,
        latitud_decimal, longitud_decimal, altitud, indsinop,
        fecha_alta, fecha_actualizacion,
    ) = fila
    return EstacionOut(
        indicativo=indicativo, nombre=nombre, provincia=provincia,
        latitud=latitud, longitud=longitud,
        latitud_decimal=latitud_decimal, longitud_decimal=longitud_decimal,
        altitud=altitud, indsinop=indsinop,
        fecha_alta=fecha_alta, fecha_actualizacion=fecha_actualizacion,
    )


@router.get("/estaciones", response_model=Listado[EstacionOut])
def listar_estaciones(
    pagina: int = 1,
    tamano_pagina: int | None = 20,
    indicativo: str | None = None,
    nombre: str | None = None,
    provincia: str | None = None,
    indsinop: str | None = None,
    latitud: str | None = None,
    longitud: str | None = None,
    altitud_desde: int | None = None,
    altitud_hasta: int | None = None,
    latitud_decimal_desde: float | None = None,
    latitud_decimal_hasta: float | None = None,
    longitud_decimal_desde: float | None = None,
    longitud_decimal_hasta: float | None = None,
    fecha_alta_desde: date | None = None,
    fecha_alta_hasta: date | None = None,
    fecha_actualizacion_desde: date | None = None,
    fecha_actualizacion_hasta: date | None = None,
    usuario: UsuarioActual = Depends(usuario_actual),
    conn: Connection = Depends(get_db),
):
    filtros = {
        "indicativo": indicativo,
        "nombre": nombre,
        "provincia": provincia,
        "indsinop": indsinop,
        "latitud": latitud,
        "longitud": longitud,
        "altitud_desde": altitud_desde,
        "altitud_hasta": altitud_hasta,
        "latitud_decimal_desde": latitud_decimal_desde,
        "latitud_decimal_hasta": latitud_decimal_hasta,
        "longitud_decimal_desde": longitud_decimal_desde,
        "longitud_decimal_hasta": longitud_decimal_hasta,
        "fecha_alta_desde": fecha_alta_desde,
        "fecha_alta_hasta": fecha_alta_hasta,
        "fecha_actualizacion_desde": fecha_actualizacion_desde,
        "fecha_actualizacion_hasta": fecha_actualizacion_hasta,
    }
    filas, total = servicio.listar_estaciones(conn, pagina, tamano_pagina, filtros)
    return Listado(
        items=[_a_estacion_out(f) for f in filas], total=total, pagina=pagina, tamano_pagina=tamano_pagina
    )
