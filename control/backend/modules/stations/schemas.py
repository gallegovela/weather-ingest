"""Pydantic response models for the stations module.

See spec/control/module/stations.md and spec/db/tables.md (stations
table).
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class StationOut(BaseModel):
    station_code: str
    name: str
    province: str
    latitude: str
    longitude: str
    latitude_decimal: Decimal
    longitude_decimal: Decimal
    altitude: int
    synoptic_code: str | None
    created_at: datetime
    updated_at: datetime
    daily_values_count: int
