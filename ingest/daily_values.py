"""Import of AEMET daily climatological values, either for a station and
date range or for every station at once (same date range).

See spec/ingest/DAILY_VALUES.md for the detail of the process (AEMET
endpoint, decimal-comma parsing, precipitation sentinels, dropped
redundant fields) and spec/db/tables.md for the destination schema.

Always runs with parameters supplied by the job that triggers it
(spec/control/module/jobs.md) or, for manual debugging, CLI arguments:

    python -m ingest.daily_values --station 3195 --from 2024-01-01 --to 2024-01-31
"""

import argparse
import logging
from dataclasses import dataclass
from datetime import date

from ingest import aemet_client, db

ENDPOINT_TEMPLATE = (
    "https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/"
    "fechaini/{date_from}T00:00:00UTC/fechafin/{date_to}T00:00:00UTC/estacion/{station_code}"
)

# "All stations" import mode (spec/ingest/DAILY_VALUES.md, "Import mode:
# all stations at once"): same resource, aggregated across every station
# AEMET has data for instead of filtered to one -- station_code comes from
# each record's own indicativo (see transform()), not from params.
ALL_STATIONS_ENDPOINT_TEMPLATE = (
    "https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/"
    "fechaini/{date_from}T00:00:00UTC/fechafin/{date_to}T00:00:00UTC/todasestaciones"
)

UPSERT_SQL = """
    INSERT INTO climatological_values (
        station_code, date, mean_temperature, precipitation_mm, precipitation_raw,
        min_temperature, min_temperature_time, max_temperature, max_temperature_time,
        wind_gust_direction, wind_mean_speed, wind_gust_speed, wind_gust_time,
        sunshine_hours, pressure_max, pressure_max_time, pressure_min, pressure_min_time,
        humidity_mean, humidity_max, humidity_max_time, humidity_min, humidity_min_time,
        precipitation_intensity_max, precipitation_intensity_max_time
    ) VALUES (
        %(station_code)s, %(date)s, %(mean_temperature)s, %(precipitation_mm)s, %(precipitation_raw)s,
        %(min_temperature)s, %(min_temperature_time)s, %(max_temperature)s, %(max_temperature_time)s,
        %(wind_gust_direction)s, %(wind_mean_speed)s, %(wind_gust_speed)s, %(wind_gust_time)s,
        %(sunshine_hours)s, %(pressure_max)s, %(pressure_max_time)s, %(pressure_min)s, %(pressure_min_time)s,
        %(humidity_mean)s, %(humidity_max)s, %(humidity_max_time)s, %(humidity_min)s, %(humidity_min_time)s,
        %(precipitation_intensity_max)s, %(precipitation_intensity_max_time)s
    )
    ON CONFLICT (station_code, date) DO UPDATE SET
        mean_temperature = EXCLUDED.mean_temperature,
        precipitation_mm = EXCLUDED.precipitation_mm,
        precipitation_raw = EXCLUDED.precipitation_raw,
        min_temperature = EXCLUDED.min_temperature,
        min_temperature_time = EXCLUDED.min_temperature_time,
        max_temperature = EXCLUDED.max_temperature,
        max_temperature_time = EXCLUDED.max_temperature_time,
        wind_gust_direction = EXCLUDED.wind_gust_direction,
        wind_mean_speed = EXCLUDED.wind_mean_speed,
        wind_gust_speed = EXCLUDED.wind_gust_speed,
        wind_gust_time = EXCLUDED.wind_gust_time,
        sunshine_hours = EXCLUDED.sunshine_hours,
        pressure_max = EXCLUDED.pressure_max,
        pressure_max_time = EXCLUDED.pressure_max_time,
        pressure_min = EXCLUDED.pressure_min,
        pressure_min_time = EXCLUDED.pressure_min_time,
        humidity_mean = EXCLUDED.humidity_mean,
        humidity_max = EXCLUDED.humidity_max,
        humidity_max_time = EXCLUDED.humidity_max_time,
        humidity_min = EXCLUDED.humidity_min,
        humidity_min_time = EXCLUDED.humidity_min_time,
        precipitation_intensity_max = EXCLUDED.precipitation_intensity_max,
        precipitation_intensity_max_time = EXCLUDED.precipitation_intensity_max_time,
        updated_at = now()
    RETURNING (xmax = 0) AS inserted
"""

# Source fields that are plain numbers (comma decimal separator) once
# any non-numeric sentinel has been ruled out. `prec` is handled on its
# own (see transform()) since its sentinels aren't numeric at all.
_NUMERIC_FIELDS = {
    "tmed": "mean_temperature",
    "tmin": "min_temperature",
    "tmax": "max_temperature",
    "dir": "wind_gust_direction",
    "velmedia": "wind_mean_speed",
    "racha": "wind_gust_speed",
    "sol": "sunshine_hours",
    "presMax": "pressure_max",
    "presMin": "pressure_min",
    "hrMedia": "humidity_mean",
    "hrMax": "humidity_max",
    "hrMin": "humidity_min",
    "pintMax": "precipitation_intensity_max",
}

# hora* fields: stored as-is, no parsing (spec/ingest/DAILY_VALUES.md:
# can contain non-time text like "Varias").
_TIME_FIELDS = {
    "horatmin": "min_temperature_time",
    "horatmax": "max_temperature_time",
    "horaracha": "wind_gust_time",
    "horaPresMax": "pressure_max_time",
    "horaPresMin": "pressure_min_time",
    "horaHrMax": "humidity_max_time",
    "horaHrMin": "humidity_min_time",
    "horaPintMax": "precipitation_intensity_max_time",
}

log = logging.getLogger("ingest.daily_values")


@dataclass
class ImportResult:
    received: int
    inserted: int
    updated: int
    errors: int


def _parse_decimal(raw: str) -> float:
    return float(raw.replace(",", "."))


def transform(record: dict) -> dict:
    result = {
        "station_code": record["indicativo"].strip(),
        "date": date.fromisoformat(record["fecha"]),
    }

    for source_field, column in _NUMERIC_FIELDS.items():
        raw = record.get(source_field)
        result[column] = _parse_decimal(raw) if raw else None

    for source_field, column in _TIME_FIELDS.items():
        result[column] = record.get(source_field)

    prec_raw = record.get("prec")
    result["precipitation_raw"] = prec_raw
    try:
        result["precipitation_mm"] = _parse_decimal(prec_raw) if prec_raw else None
    except ValueError:
        # Non-numeric sentinel (Ip, Acum, ...) -- kept verbatim in
        # precipitation_raw, but there's no numeric value to store here.
        result["precipitation_mm"] = None

    return result


def _upsert_records(raw_records: list) -> ImportResult:
    """Transforms and upserts each raw record, one row/transaction at a
    time so a single record's failure (e.g. an indicativo with no
    matching stations row) is counted in errors without aborting the
    rest of the batch -- see spec/ingest/DAILY_VALUES.md, "Row-level
    error handling"."""

    inserted = updated = errors = 0
    with db.connect() as conn, conn.cursor() as cur:
        for raw in raw_records:
            try:
                record = transform(raw)
                cur.execute(UPSERT_SQL, record)
                (was_inserted,) = cur.fetchone()
                conn.commit()
                if was_inserted:
                    inserted += 1
                else:
                    updated += 1
            except Exception:
                conn.rollback()
                errors += 1
                log.exception("Error processing record %r", raw.get("fecha"))

    log.info(
        "Summary: received=%d inserted=%d updated=%d errors=%d",
        len(raw_records),
        inserted,
        updated,
        errors,
    )
    return ImportResult(received=len(raw_records), inserted=inserted, updated=updated, errors=errors)


def run_import(params: dict) -> ImportResult:
    """Runs the import for params = {station_code, date_from, date_to}
    (a date range already guaranteed by the caller to fit AEMET's
    per-request limit -- see spec/ingest/DAILY_VALUES.md, "Date range
    limit") and returns its result."""

    station_code = params["station_code"]
    endpoint = ENDPOINT_TEMPLATE.format(
        station_code=station_code,
        date_from=params["date_from"],
        date_to=params["date_to"],
    )

    raw_records = aemet_client.fetch(endpoint)
    log.info(
        "Received %d daily values for station %s", len(raw_records), station_code
    )
    return _upsert_records(raw_records)


def run_import_all_stations(params: dict) -> ImportResult:
    """Runs the "all stations" import for params = {date_from, date_to}
    (no station_code -- see spec/ingest/DAILY_VALUES.md, "Import mode:
    all stations at once"): one call covers every station AEMET has
    data for, over the same date range. Reuses transform()/UPSERT_SQL
    unchanged, since station_code already comes from each record's own
    indicativo."""

    endpoint = ALL_STATIONS_ENDPOINT_TEMPLATE.format(
        date_from=params["date_from"],
        date_to=params["date_to"],
    )

    raw_records = aemet_client.fetch(endpoint)
    log.info("Received %d daily values for all stations", len(raw_records))
    return _upsert_records(raw_records)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--station", required=True, dest="station_code")
    parser.add_argument("--from", required=True, dest="date_from")
    parser.add_argument("--to", required=True, dest="date_to")
    args = parser.parse_args()

    run_import({
        "station_code": args.station_code,
        "date_from": args.date_from,
        "date_to": args.date_to,
    })


if __name__ == "__main__":
    main()
