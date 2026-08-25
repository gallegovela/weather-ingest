"""Pydantic response model for the climatological_values module.

See spec/control/module/climatological_values.md and spec/db/tables.md
(climatological_values table). name/province are joined from stations,
not native columns.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class ClimatologicalValueOut(BaseModel):
    station_code: str
    name: str
    province: str
    date: date
    mean_temperature: Decimal | None
    precipitation_mm: Decimal | None
    precipitation_raw: str | None
    min_temperature: Decimal | None
    min_temperature_time: str | None
    max_temperature: Decimal | None
    max_temperature_time: str | None
    wind_gust_direction: Decimal | None
    wind_mean_speed: Decimal | None
    wind_gust_speed: Decimal | None
    wind_gust_time: str | None
    sunshine_hours: Decimal | None
    pressure_max: Decimal | None
    pressure_max_time: str | None
    pressure_min: Decimal | None
    pressure_min_time: str | None
    humidity_mean: Decimal | None
    humidity_max: Decimal | None
    humidity_max_time: str | None
    humidity_min: Decimal | None
    humidity_min_time: str | None
    precipitation_intensity_max: Decimal | None
    precipitation_intensity_max_time: str | None
    created_at: datetime
    updated_at: datetime
