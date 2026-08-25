"""Integration test for climatological_values upsert idempotency.

See spec/testing.md, "Known exceptions": this needs a real Postgres to
mean anything -- the guarantee under test is the composite primary key
(station_code, date) plus daily_values.UPSERT_SQL's
`ON CONFLICT ... DO UPDATE`, not something a mock could stand in for.
Requires DATABASE_URL pointing at a migrated database (see
spec/ingest/general.md and spec/testing.md, "Continuous integration").
"""

import pytest

from ingest import daily_values, db

STATION_CODE = "TEST01"


@pytest.fixture
def conn():
    connection = db.connect()
    yield connection
    # Never committed: the test station and its climatological_values
    # rows are rolled back, not left behind for the next run.
    connection.rollback()
    connection.close()


def _insert_test_station(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO stations (
                station_code, name, province, latitude, longitude,
                latitude_decimal, longitude_decimal, altitude
            ) VALUES (%(station_code)s, 'TEST STATION', 'TEST', '000000N', '000000E', 0, 0, 0)
            """,
            {"station_code": STATION_CODE},
        )


def test_overlapping_import_updates_not_duplicates(conn):
    _insert_test_station(conn)

    raw = {"fecha": "2024-01-01", "indicativo": STATION_CODE, "tmed": "10,0"}
    with conn.cursor() as cur:
        cur.execute(daily_values.UPSERT_SQL, daily_values.transform(raw))
        (inserted,) = cur.fetchone()
    assert inserted is True

    # Same (station_code, date), different value -- simulates
    # re-importing an overlapping range.
    raw["tmed"] = "20,0"
    with conn.cursor() as cur:
        cur.execute(daily_values.UPSERT_SQL, daily_values.transform(raw))
        (inserted,) = cur.fetchone()
    assert inserted is False

    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*), max(mean_temperature) FROM climatological_values WHERE station_code = %(station_code)s",
            {"station_code": STATION_CODE},
        )
        count, mean_temperature = cur.fetchone()

    assert count == 1
    assert float(mean_temperature) == 20.0
