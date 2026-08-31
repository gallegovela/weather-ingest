"""Pydantic request/response models for the jobs module.

See spec/control/module/jobs.md and spec/db/tables.md (ingest_jobs
table).
"""

from datetime import date, datetime

from pydantic import BaseModel


class JobOut(BaseModel):
    id: int
    job_type: str
    params: dict
    status: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    rows_inserted: int | None
    rows_updated: int | None
    error_message: str | None


class DailyValuesJobCreate(BaseModel):
    station_code: str
    date_from: date
    date_to: date


class DailyValuesAllStationsJobCreate(BaseModel):
    date_from: date
    date_to: date


class JobDeleteRequest(BaseModel):
    ids: list[int]
