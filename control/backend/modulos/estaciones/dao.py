"""Capa DAO del módulo estaciones: único punto de acceso a la tabla
estaciones (ver spec/control/core.md, "Arquitectura en capas"). SQL
puro con psycopg v3, sin ORM, mismo criterio que importa/.

Es un módulo de solo consulta (spec/control/module/estaciones.md): no
hay insert/update/delete aquí, eso lo gestiona importa/estaciones.py.
"""

from psycopg import Connection
from psycopg.rows import tuple_row

# Filtro "contiene" (ILIKE), convención transversal fijada en
# spec/control/core.md ("Listados paginados con filtros").
_CAMPOS_TEXTO_CONTIENE = ("indicativo", "nombre", "provincia", "indsinop", "latitud", "longitud")

# Filtro por rango (sufijos _desde/_hasta), misma convención.
_CAMPOS_RANGO = ("altitud", "latitud_decimal", "longitud_decimal", "fecha_alta", "fecha_actualizacion")

_COLUMNAS = """
    indicativo, nombre, provincia, latitud, longitud,
    latitud_decimal, longitud_decimal, altitud, indsinop,
    fecha_alta, fecha_actualizacion
"""


def _construir_where(filtros: dict) -> tuple[str, dict]:
    condiciones = []
    params: dict = {}

    for campo in _CAMPOS_TEXTO_CONTIENE:
        valor = filtros.get(campo)
        if valor:
            condiciones.append(f"{campo} ILIKE %({campo})s")
            params[campo] = f"%{valor}%"

    for campo in _CAMPOS_RANGO:
        desde = filtros.get(f"{campo}_desde")
        if desde is not None:
            condiciones.append(f"{campo} >= %({campo}_desde)s")
            params[f"{campo}_desde"] = desde
        hasta = filtros.get(f"{campo}_hasta")
        if hasta is not None:
            condiciones.append(f"{campo} <= %({campo}_hasta)s")
            params[f"{campo}_hasta"] = hasta

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    return where, params


def listar_estaciones(
    conn: Connection, pagina: int, tamano_pagina: int | None, filtros: dict
) -> tuple[list[tuple], int]:
    where, params = _construir_where(filtros)

    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(f"SELECT count(*) FROM estaciones {where}", params)
        (total,) = cur.fetchone()

        sql = f"SELECT {_COLUMNAS} FROM estaciones {where} ORDER BY indicativo"
        params_consulta = dict(params)
        # Sin tamano_pagina: el mapa pide el conjunto completo sin paginar
        # (decidido en spec/control/module/estaciones.md).
        if tamano_pagina is not None:
            sql += " LIMIT %(limite)s OFFSET %(offset)s"
            params_consulta["limite"] = tamano_pagina
            params_consulta["offset"] = (pagina - 1) * tamano_pagina

        cur.execute(sql, params_consulta)
        filas = cur.fetchall()

    return filas, total
