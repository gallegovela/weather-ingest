"""Import of the AEMET climatological station inventory.

See spec/ingest/STATIONS.md for the detail of the process (API
two-step pattern, ISO-8859-15 encoding, transformations and upsert
strategy) and spec/db/tables.md for the destination schema.

Usage:
    python -m ingest.stations
"""

import logging

from ingest import aemet_client, db

ENDPOINT = (
    "https://opendata.aemet.es/opendata/api/valores/climatologicos/"
    "inventarioestaciones/todasestaciones"
)

UPSERT_SQL = """
    INSERT INTO stations (
        station_code, name, province, latitude, longitude,
        latitude_decimal, longitude_decimal, altitude, synoptic_code
    ) VALUES (
        %(station_code)s, %(name)s, %(province)s, %(latitude)s, %(longitude)s,
        %(latitude_decimal)s, %(longitude_decimal)s, %(altitude)s, %(synoptic_code)s
    )
    ON CONFLICT (station_code) DO UPDATE SET
        name = EXCLUDED.name,
        province = EXCLUDED.province,
        latitude = EXCLUDED.latitude,
        longitude = EXCLUDED.longitude,
        latitude_decimal = EXCLUDED.latitude_decimal,
        longitude_decimal = EXCLUDED.longitude_decimal,
        altitude = EXCLUDED.altitude,
        synoptic_code = EXCLUDED.synoptic_code,
        updated_at = now()
    RETURNING (xmax = 0) AS inserted
"""

SELECT_CURRENT_SQL = """
    SELECT name, province, latitude, longitude,
           latitude_decimal, longitude_decimal, altitude, synoptic_code,
           updated_at
    FROM stations
    WHERE station_code = %(station_code)s
    FOR UPDATE
"""

HISTORY_SQL = """
    INSERT INTO stations_history (
        station_code, name, province, latitude, longitude,
        latitude_decimal, longitude_decimal, altitude, synoptic_code, changed_at
    ) VALUES (
        %(station_code)s, %(name)s, %(province)s, %(latitude)s, %(longitude)s,
        %(latitude_decimal)s, %(longitude_decimal)s, %(altitude)s, %(synoptic_code)s, %(changed_at)s
    )
"""

# Source fields compared to detect changes (see spec/db/tables.md,
# stations_history table: latitude_decimal/longitude_decimal aren't
# compared separately since they're a deterministic function of
# latitude/longitude).
COMPARABLE_FIELDS = (
    "name", "province", "latitude", "longitude", "altitude", "synoptic_code",
)
# Same order as SELECT_CURRENT_SQL's columns.
_CURRENT_COLUMNS = (
    "name", "province", "latitude", "longitude",
    "latitude_decimal", "longitude_decimal", "altitude", "synoptic_code",
    "updated_at",
)

log = logging.getLogger("ingest.stations")


def parse_coordinate(raw: str) -> float:
    """Converts an AEMET coordinate (degrees/minutes/seconds +
    hemisphere, e.g. '394924N' or '025309E') to decimal degrees."""

    raw = raw.strip()
    hemisphere = raw[-1].upper()
    digits = raw[:-1]

    seconds = int(digits[-2:])
    minutes = int(digits[-4:-2])
    degrees = int(digits[:-4])

    decimal = degrees + minutes / 60 + seconds / 3600
    if hemisphere in ("S", "W"):
        decimal = -decimal
    return round(decimal, 6)


def transform(record: dict) -> dict:
    synoptic_code = record.get("indsinop", "").strip()
    return {
        "station_code": record["indicativo"].strip(),
        "name": record["nombre"].strip(),
        "province": record["provincia"].strip(),
        "latitude": record["latitud"].strip(),
        "longitude": record["longitud"].strip(),
        "latitude_decimal": parse_coordinate(record["latitud"]),
        "longitude_decimal": parse_coordinate(record["longitud"]),
        "altitude": int(record["altitud"]),
        "synoptic_code": synoptic_code or None,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    raw_records = aemet_client.fetch(ENDPOINT)
    log.info("Received %d stations from AEMET", len(raw_records))

    inserted = updated = errors = 0
    with db.connect() as conn, conn.cursor() as cur:
        for raw in raw_records:
            try:
                record = transform(raw)

                cur.execute(SELECT_CURRENT_SQL, record)
                current_row = cur.fetchone()
                if current_row:
                    current = dict(zip(_CURRENT_COLUMNS, current_row))
                    if any(current[field] != record[field] for field in COMPARABLE_FIELDS):
                        cur.execute(HISTORY_SQL, {
                            "station_code": record["station_code"],
                            "changed_at": current["updated_at"],
                            **{field: current[field] for field in COMPARABLE_FIELDS},
                            "latitude_decimal": current["latitude_decimal"],
                            "longitude_decimal": current["longitude_decimal"],
                        })

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
                log.exception("Error processing station %r", raw.get("indicativo"))

    log.info(
        "Summary: received=%d inserted=%d updated=%d errors=%d",
        len(raw_records),
        inserted,
        updated,
        errors,
    )


if __name__ == "__main__":
    main()
