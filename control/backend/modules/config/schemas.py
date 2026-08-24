"""Pydantic request/response models for the config module.

See spec/control/module/config.md and spec/db/tables.md (config_values
table).
"""

from datetime import datetime

from pydantic import BaseModel


class ConfigValueOut(BaseModel):
    key: str
    value: str
    value_type: str
    description: str
    updated_at: datetime


class ConfigValueUpdate(BaseModel):
    value: str
