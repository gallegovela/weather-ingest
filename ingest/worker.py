"""Job worker: drains the ingest_jobs queue one job at a time.

See spec/ingest/general.md for the full mechanism (why a DB-backed
queue instead of cron/a scheduling library, why exactly one job per
loop iteration, the poll interval coming from config_values). Run
with:

    python -m ingest.worker
"""

import logging
import time

from psycopg.types.json import Jsonb

from ingest import daily_values, db, metrics, stations

log = logging.getLogger("ingest.worker")

# job_type -> the function that executes a job of that type, taking
# its `params` (a dict, possibly empty) and returning a result with
# `.inserted`/`.updated` attributes. Adding a new ingestion script
# means adding an entry here (spec/ingest/general.md, "Job dispatch").
JOB_HANDLERS = {
    "stations": stations.run_import,
    "daily_values": daily_values.run_import,
    "metrics": metrics.run_import,
}

# job_type -> job_type: when a job of the key's type finishes with
# success, a new job of the value's type is queued (not executed
# inline, see "Exactly one job per loop iteration") with the same
# params (spec/ingest/general.md, "Automatic follow-up job").
AUTO_FOLLOWUP = {
    "daily_values": "metrics",
}

_CLAIM_SQL = """
    UPDATE ingest_jobs SET status = 'running', started_at = now()
    WHERE id = (
        SELECT id FROM ingest_jobs
        WHERE status = 'pending'
        ORDER BY created_at
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    )
    RETURNING id, job_type, params
"""

_SUCCESS_SQL = """
    UPDATE ingest_jobs
    SET status = 'success', finished_at = now(), rows_inserted = %(rows_inserted)s,
        rows_updated = %(rows_updated)s, result = %(result)s
    WHERE id = %(id)s
"""

_ERROR_SQL = """
    UPDATE ingest_jobs
    SET status = 'error', finished_at = now(), error_message = %(error_message)s
    WHERE id = %(id)s
"""

_QUEUE_SQL = """
    INSERT INTO ingest_jobs (job_type, params) VALUES (%(job_type)s, %(params)s)
"""


def _claim_job(conn) -> tuple | None:
    with conn.cursor() as cur:
        cur.execute(_CLAIM_SQL)
        job = cur.fetchone()
    conn.commit()
    return job


def _run_job(job_id: int, job_type: str, params: dict) -> None:
    handler = JOB_HANDLERS.get(job_type)
    if handler is None:
        _mark_error(job_id, f"No handler registered for job_type {job_type!r}.")
        return

    try:
        result = handler(params)
    except Exception as exc:
        log.exception("Job %d (%s) failed", job_id, job_type)
        _mark_error(job_id, str(exc))
        return

    job_result = getattr(result, "result", None)
    with db.connect() as conn, conn.cursor() as cur:
        cur.execute(_SUCCESS_SQL, {
            "id": job_id, "rows_inserted": result.inserted, "rows_updated": result.updated,
            "result": Jsonb(job_result) if job_result is not None else None,
        })

        followup_type = AUTO_FOLLOWUP.get(job_type)
        if followup_type is not None:
            cur.execute(_QUEUE_SQL, {"job_type": followup_type, "params": Jsonb(params)})

        conn.commit()
    log.info("Job %d (%s) succeeded: %s", job_id, job_type, result)


def _mark_error(job_id: int, error_message: str) -> None:
    with db.connect() as conn, conn.cursor() as cur:
        cur.execute(_ERROR_SQL, {"id": job_id, "error_message": error_message})
        conn.commit()


def run_once() -> bool:
    """Claims and runs a single pending job, if any. Returns whether a
    job was claimed (so the caller knows whether to skip its sleep)."""

    with db.connect() as conn:
        job = _claim_job(conn)

    if job is None:
        return False

    job_id, job_type, params = job
    log.info("Claimed job %d (%s)", job_id, job_type)
    _run_job(job_id, job_type, params)
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log.info("Job worker starting")

    while True:
        poll_interval_seconds = int(db.get_config_value("POLL_INTERVAL_SECONDS"))
        if not run_once():
            time.sleep(poll_interval_seconds)


if __name__ == "__main__":
    main()
