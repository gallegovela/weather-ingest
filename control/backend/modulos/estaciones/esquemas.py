"""Modelos Pydantic de respuesta del módulo estaciones.

Ver spec/control/module/estaciones.md y spec/db/tables.md (tabla
estaciones).
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class EstacionOut(BaseModel):
    indicativo: str
    nombre: str
    provincia: str
    latitud: str
    longitud: str
    latitud_decimal: Decimal
    longitud_decimal: Decimal
    altitud: int
    indsinop: str | None
    fecha_alta: datetime
    fecha_actualizacion: datetime
