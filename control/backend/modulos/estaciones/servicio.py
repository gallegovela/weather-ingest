"""Capa de servicio del módulo estaciones: valida parámetros de
filtro/paginación y delega en el DAO; sin lógica de negocio adicional,
al ser un módulo de solo consulta (spec/control/module/estaciones.md).
"""

from fastapi import HTTPException, status
from psycopg import Connection

from modulos.estaciones import dao


def listar_estaciones(
    conn: Connection, pagina: int, tamano_pagina: int | None, filtros: dict
) -> tuple[list[tuple], int]:
    if pagina < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "pagina debe ser >= 1")
    if tamano_pagina is not None and tamano_pagina < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "tamano_pagina debe ser >= 1")

    return dao.listar_estaciones(conn, pagina, tamano_pagina, filtros)
