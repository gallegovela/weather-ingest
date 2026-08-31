"""Control (endpoints) layer of the climatological_values module.

A single read-only, filtered, paginated endpoint
(spec/control/module/climatological_values.md).
"""

from datetime import date

from fastapi import APIRouter, Depends
from psycopg import Connection

from core.auth import CurrentUser, get_current_user
from core.db import get_db
from core.schemas import Page
from modules.climatological_values import service
from modules.climatological_values.schemas import ClimatologicalValueOut

router = APIRouter(prefix="/api/climatological-values", tags=["climatological-values"])


def _to_value_out(row: tuple) -> ClimatologicalValueOut:
    (
        station_code, name, province, value_date,
        mean_temperature, precipitation_mm, precipitation_raw,
        min_temperature, min_temperature_time,
        max_temperature, max_temperature_time,
        wind_gust_direction, wind_mean_speed, wind_gust_speed, wind_gust_time,
        sunshine_hours,
        pressure_max, pressure_max_time, pressure_min, pressure_min_time,
        humidity_mean, humidity_max, humidity_max_time,
        humidity_min, humidity_min_time,
        precipitation_intensity_max, precipitation_intensity_max_time,
        created_at, updated_at,
    ) = row
    return ClimatologicalValueOut(
        station_code=station_code, name=name, province=province, date=value_date,
        mean_temperature=mean_temperature, precipitation_mm=precipitation_mm,
        precipitation_raw=precipitation_raw,
        min_temperature=min_temperature, min_temperature_time=min_temperature_time,
        max_temperature=max_temperature, max_temperature_time=max_temperature_time,
        wind_gust_direction=wind_gust_direction, wind_mean_speed=wind_mean_speed,
        wind_gust_speed=wind_gust_speed, wind_gust_time=wind_gust_time,
        sunshine_hours=sunshine_hours,
        pressure_max=pressure_max, pressure_max_time=pressure_max_time,
        pressure_min=pressure_min, pressure_min_time=pressure_min_time,
        humidity_mean=humidity_mean, humidity_max=humidity_max, humidity_max_time=humidity_max_time,
        humidity_min=humidity_min, humidity_min_time=humidity_min_time,
        precipitation_intensity_max=precipitation_intensity_max,
        precipitation_intensity_max_time=precipitation_intensity_max_time,
        created_at=created_at, updated_at=updated_at,
    )


@router.get("/values", response_model=Page[ClimatologicalValueOut])
def list_values(
    page: int = 1,
    page_size: int = 20,
    station_code: str | None = None,
    precipitation_raw: str | None = None,
    min_temperature_time: str | None = None,
    max_temperature_time: str | None = None,
    wind_gust_time: str | None = None,
    pressure_max_time: str | None = None,
    pressure_min_time: str | None = None,
    humidity_max_time: str | None = None,
    humidity_min_time: str | None = None,
    precipitation_intensity_max_time: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    mean_temperature_from: float | None = None,
    mean_temperature_to: float | None = None,
    precipitation_mm_from: float | None = None,
    precipitation_mm_to: float | None = None,
    min_temperature_from: float | None = None,
    min_temperature_to: float | None = None,
    max_temperature_from: float | None = None,
    max_temperature_to: float | None = None,
    wind_gust_direction_from: float | None = None,
    wind_gust_direction_to: float | None = None,
    wind_mean_speed_from: float | None = None,
    wind_mean_speed_to: float | None = None,
    wind_gust_speed_from: float | None = None,
    wind_gust_speed_to: float | None = None,
    sunshine_hours_from: float | None = None,
    sunshine_hours_to: float | None = None,
    pressure_max_from: float | None = None,
    pressure_max_to: float | None = None,
    pressure_min_from: float | None = None,
    pressure_min_to: float | None = None,
    humidity_mean_from: float | None = None,
    humidity_mean_to: float | None = None,
    humidity_max_from: float | None = None,
    humidity_max_to: float | None = None,
    humidity_min_from: float | None = None,
    humidity_min_to: float | None = None,
    precipitation_intensity_max_from: float | None = None,
    precipitation_intensity_max_to: float | None = None,
    created_at_from: date | None = None,
    created_at_to: date | None = None,
    updated_at_from: date | None = None,
    updated_at_to: date | None = None,
    user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    filters = {
        "station_code": station_code,
        "precipitation_raw": precipitation_raw,
        "min_temperature_time": min_temperature_time,
        "max_temperature_time": max_temperature_time,
        "wind_gust_time": wind_gust_time,
        "pressure_max_time": pressure_max_time,
        "pressure_min_time": pressure_min_time,
        "humidity_max_time": humidity_max_time,
        "humidity_min_time": humidity_min_time,
        "precipitation_intensity_max_time": precipitation_intensity_max_time,
        "date_from": date_from,
        "date_to": date_to,
        "mean_temperature_from": mean_temperature_from,
        "mean_temperature_to": mean_temperature_to,
        "precipitation_mm_from": precipitation_mm_from,
        "precipitation_mm_to": precipitation_mm_to,
        "min_temperature_from": min_temperature_from,
        "min_temperature_to": min_temperature_to,
        "max_temperature_from": max_temperature_from,
        "max_temperature_to": max_temperature_to,
        "wind_gust_direction_from": wind_gust_direction_from,
        "wind_gust_direction_to": wind_gust_direction_to,
        "wind_mean_speed_from": wind_mean_speed_from,
        "wind_mean_speed_to": wind_mean_speed_to,
        "wind_gust_speed_from": wind_gust_speed_from,
        "wind_gust_speed_to": wind_gust_speed_to,
        "sunshine_hours_from": sunshine_hours_from,
        "sunshine_hours_to": sunshine_hours_to,
        "pressure_max_from": pressure_max_from,
        "pressure_max_to": pressure_max_to,
        "pressure_min_from": pressure_min_from,
        "pressure_min_to": pressure_min_to,
        "humidity_mean_from": humidity_mean_from,
        "humidity_mean_to": humidity_mean_to,
        "humidity_max_from": humidity_max_from,
        "humidity_max_to": humidity_max_to,
        "humidity_min_from": humidity_min_from,
        "humidity_min_to": humidity_min_to,
        "precipitation_intensity_max_from": precipitation_intensity_max_from,
        "precipitation_intensity_max_to": precipitation_intensity_max_to,
        "created_at_from": created_at_from,
        "created_at_to": created_at_to,
        "updated_at_from": updated_at_from,
        "updated_at_to": updated_at_to,
    }
    rows, total = service.list_values(conn, page, page_size, filters)
    return Page(
        items=[_to_value_out(r) for r in rows], total=total, page=page, page_size=page_size
    )


@router.get("/years", response_model=list[int])
def list_years(
    station_code: str,
    user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    return service.list_years(conn, station_code)


@router.get("/monthly-counts", response_model=list[int])
def monthly_counts(
    station_code: str,
    year: int,
    user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    return service.monthly_counts(conn, station_code, year)
