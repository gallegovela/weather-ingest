"""Cross-cutting Pydantic schemas, reused by every module.

See spec/control/core.md, "Paginated listings with filters": the
shared paginated-listing convention first set by the stations module
and reused by the following ones.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int | None
