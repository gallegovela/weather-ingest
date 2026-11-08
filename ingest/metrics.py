"""Derivation of climatological metrics from the daily climatological
values already imported into climatological_values -- no AEMET
endpoint involved, no use of ingest/aemet_client.py.

See spec/ingest/METRICS.md for the full detail (formulas, the rainy
day definition, load strategy) and spec/db/tables.md for the
destination schema (climatological_metrics, ingest_jobs.result).

Always runs with parameters (station + date range) supplied by the job
that triggers it (spec/control/module/jobs.md) -- automatically after
a successful daily_values job (spec/ingest/general.md) or manually --
or, for manual debugging, CLI arguments:

    python -m ingest.metrics --station 3195 --from 2024-01-01 --to 2024-01-31
"""

import argparse
import logging
from dataclasses import dataclass
from datetime import date, timedelta

from ingest import db

SELECT_SQL = """
    SELECT date, max_temperature, min_temperature, precipitation_mm, precipitation_raw
    FROM climatological_values
    WHERE station_code = %(station_code)s AND date >= %(date_from)s AND date <= %(date_to)s
"""

UPSERT_SQL = """
    INSERT INTO climatological_metrics (
        station_code, date, temperature_range,
        max_temperature_diff_prev_day, min_temperature_diff_prev_day
    ) VALUES (
        %(station_code)s, %(date)s, %(temperature_range)s,
        %(max_temperature_diff_prev_day)s, %(min_temperature_diff_prev_day)s
    )
    ON CONFLICT (station_code, date) DO UPDATE SET
        temperature_range = EXCLUDED.temperature_range,
        max_temperature_diff_prev_day = EXCLUDED.max_temperature_diff_prev_day,
        min_temperature_diff_prev_day = EXCLUDED.min_temperature_diff_prev_day,
        updated_at = now()
    RETURNING (xmax = 0) AS inserted
"""

_SOURCE_COLUMNS = ("date", "max_temperature", "min_temperature", "precipitation_mm", "precipitation_raw")

log = logging.getLogger("ingest.metrics")


@dataclass
class ImportResult:
    received: int
    inserted: int
    updated: int
    errors: int
    result: dict


def is_rainy_day(precipitation_mm, precipitation_raw) -> bool | None:
    """Whether a day with a climatological_values row counts as rainy
    (spec/ingest/METRICS.md, "Rainy day definition"). Returns None for
    an `Acum` reading, meaning the day must be excluded from the rainy
    days count entirely (that day's actual figure is unknown, see
    spec/db/tables.md)."""

    if precipitation_raw == "Acum":
        return None
    if precipitation_raw == "Ip":
        return True
    return bool(precipitation_mm and precipitation_mm > 0)


def compute_day_metrics(station_code: str, target_date: date, today: dict, yesterday: dict | None) -> dict:
    """Computes one day's climatological_metrics row (spec/ingest/METRICS.md,
    "Formulas"). `today` is that day's source row (never missing --
    the caller only calls this for days that have one); `yesterday` is
    the immediately previous calendar day's source row, or None if
    there's no climatological_values row for it at all."""

    temperature_range = None
    if today["max_temperature"] is not None and today["min_temperature"] is not None:
        temperature_range = today["max_temperature"] - today["min_temperature"]

    max_temperature_diff_prev_day = None
    min_temperature_diff_prev_day = None
    if yesterday is not None:
        if today["max_temperature"] is not None and yesterday["max_temperature"] is not None:
            max_temperature_diff_prev_day = today["max_temperature"] - yesterday["max_temperature"]
        if today["min_temperature"] is not None and yesterday["min_temperature"] is not None:
            min_temperature_diff_prev_day = today["min_temperature"] - yesterday["min_temperature"]

    return {
        "station_code": station_code,
        "date": target_date,
        "temperature_range": temperature_range,
        "max_temperature_diff_prev_day": max_temperature_diff_prev_day,
        "min_temperature_diff_prev_day": min_temperature_diff_prev_day,
    }


def run_import(params: dict) -> ImportResult:
    """Runs the metrics derivation for params = {station_code, date_from,
    date_to} and returns its result."""

    station_code = params["station_code"]
    date_from = date.fromisoformat(params["date_from"])
    date_to = date.fromisoformat(params["date_to"])

    with db.connect() as conn, conn.cursor() as cur:
        cur.execute(SELECT_SQL, {
            "station_code": station_code,
            # Extra leading day covers date_from's own day-over-day
            # difference (spec/ingest/METRICS.md, "Job flow").
            "date_from": date_from - timedelta(days=1),
            "date_to": date_to,
        })
        rows_by_date = {row[0]: dict(zip(_SOURCE_COLUMNS, row)) for row in cur.fetchall()}

    target_dates = sorted(d for d in rows_by_date if date_from <= d <= date_to)
    log.info(
        "Computing metrics for %d days (station %s, %s to %s)",
        len(target_dates), station_code, date_from, date_to,
    )

    inserted = updated = errors = rainy_days = 0
    with db.connect() as conn, conn.cursor() as cur:
        for target_date in target_dates:
            today = rows_by_date[target_date]
            yesterday = rows_by_date.get(target_date - timedelta(days=1))

            try:
                record = compute_day_metrics(station_code, target_date, today, yesterday)
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
                log.exception("Error computing metrics for %s", target_date)

            if is_rainy_day(today["precipitation_mm"], today["precipitation_raw"]):
                rainy_days += 1

    log.info(
        "Summary: received=%d inserted=%d updated=%d errors=%d rainy_days=%d",
        len(target_dates), inserted, updated, errors, rainy_days,
    )
    return ImportResult(
        received=len(target_dates), inserted=inserted, updated=updated, errors=errors,
        result={"rainy_days": rainy_days},
    )


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
