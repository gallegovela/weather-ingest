"""Control (endpoints) layer of the stations module.

A single endpoint reused by both the listing and the map (without
pagination, omitting page_size — decided in
spec/control/module/stations.md).
"""

from datetime import date

from fastapi import APIRouter, Depends
from psycopg import Connection

from core.auth import CurrentUser, get_current_user
from core.db import get_db
from core.schemas import Page
from modules.stations import service
from modules.stations.schemas import StationOut

router = APIRouter(prefix="/api/stations", tags=["stations"])


def _to_station_out(row: tuple) -> StationOut:
    (
        station_code, name, province, latitude, longitude,
        latitude_decimal, longitude_decimal, altitude, synoptic_code,
        created_at, updated_at,
    ) = row
    return StationOut(
        station_code=station_code, name=name, province=province,
        latitude=latitude, longitude=longitude,
        latitude_decimal=latitude_decimal, longitude_decimal=longitude_decimal,
        altitude=altitude, synoptic_code=synoptic_code,
        created_at=created_at, updated_at=updated_at,
    )


@router.get("/stations", response_model=Page[StationOut])
def list_stations(
    page: int = 1,
    page_size: int | None = 20,
    station_code: str | None = None,
    name: str | None = None,
    province: str | None = None,
    synoptic_code: str | None = None,
    latitude: str | None = None,
    longitude: str | None = None,
    altitude_from: int | None = None,
    altitude_to: int | None = None,
    latitude_decimal_from: float | None = None,
    latitude_decimal_to: float | None = None,
    longitude_decimal_from: float | None = None,
    longitude_decimal_to: float | None = None,
    created_at_from: date | None = None,
    created_at_to: date | None = None,
    updated_at_from: date | None = None,
    updated_at_to: date | None = None,
    user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    filters = {
        "station_code": station_code,
        "name": name,
        "province": province,
        "synoptic_code": synoptic_code,
        "latitude": latitude,
        "longitude": longitude,
        "altitude_from": altitude_from,
        "altitude_to": altitude_to,
        "latitude_decimal_from": latitude_decimal_from,
        "latitude_decimal_to": latitude_decimal_to,
        "longitude_decimal_from": longitude_decimal_from,
        "longitude_decimal_to": longitude_decimal_to,
        "created_at_from": created_at_from,
        "created_at_to": created_at_to,
        "updated_at_from": updated_at_from,
        "updated_at_to": updated_at_to,
    }
    rows, total = service.list_stations(conn, page, page_size, filters)
    return Page(
        items=[_to_station_out(r) for r in rows], total=total, page=page, page_size=page_size
    )
