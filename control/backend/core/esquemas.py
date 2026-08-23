"""Esquemas Pydantic transversales, reutilizados por todos los módulos.

Ver spec/control/core.md, "Listados paginados con filtros": convención
común de listado paginado que fija por primera vez el módulo
estaciones y reutilizan los siguientes.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Listado(BaseModel, Generic[T]):
    items: list[T]
    total: int
    pagina: int
    tamano_pagina: int | None
