"""Pydantic response model for the metrics module.

See spec/control/module/metrics.md and spec/db/tables.md
(climatological_metrics table). name/province are joined from
stations, not native columns.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class ClimatologicalMetricOut(BaseModel):
    station_code: str
    name: str
    province: str
    date: date
    temperature_range: Decimal | None
    max_temperature_diff_prev_day: Decimal | None
    min_temperature_diff_prev_day: Decimal | None
    created_at: datetime
    updated_at: datetime
