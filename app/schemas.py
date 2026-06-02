from datetime import date, datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    version: str
    time: datetime


class ListResponse(BaseModel):
    items: list[Any]
    next_cursor: str | None = None
    total: int | None = None


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    corp_code: str
    stock_code: str
    corp_name: str
    corp_name_eng: str | None = None
    market: str
    sector: str | None = None
    industry: str | None = None
    fiscal_month: int | None = None
    listed_at: date | None = None
    delisted_at: date | None = None
    is_active: bool
    updated_at: datetime | None = None


class CollectionJobCreateBase(BaseModel):
    market: str = "KOSPI"
    company_ids: list[int] | None = None
    enqueue_recalculation: bool = True
    force: bool = False


class CollectCompaniesRequest(BaseModel):
    market: str = "KOSPI"
    source: str = "FDR"
    enqueue_recalculation: bool = False
    force: bool = False


class CollectFilingsRequest(CollectionJobCreateBase):
    from_date: date
    to_date: date
    report_codes: list[str] = Field(default_factory=lambda: ["11011", "11013", "11012", "11014"])


class CollectFinancialsRequest(CollectionJobCreateBase):
    year: int
    periods: list[str] = Field(default_factory=lambda: ["FY"])
    basis: str = "CONSOLIDATED"


class CollectPricesRequest(CollectionJobCreateBase):
    from_date: date
    to_date: date


class CollectEventsRequest(CollectionJobCreateBase):
    from_date: date
    to_date: date
    event_types: list[str] = Field(
        default_factory=lambda: ["MANAGEMENT_ISSUE", "AUDIT_OPINION", "TRADING_SUSPENSION"]
    )


class JobQueuedResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    job_type: str
    status: str
    requested_by: str | None = None
    market: str
    params: dict[str, Any]
    progress: dict[str, Any]
    error: dict[str, Any] | None = None
    parent_job_id: int | None = None
    enqueue_recalculation: bool
    created_at: datetime
    queued_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class SchedulePatch(BaseModel):
    recommended_interval: str | None = None
    is_active: bool | None = None
    params: dict[str, Any] | None = None
    next_recommended_at: datetime | None = None


class ScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    schedule_code: str
    job_type: str
    market: str
    recommended_interval: str
    is_active: bool
    params: dict[str, Any]
    last_success_job_id: int | None = None
    last_success_at: datetime | None = None
    next_recommended_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    is_stale: bool = False


def is_stale(next_recommended_at: datetime | None) -> bool:
    if next_recommended_at is None:
        return False
    now = datetime.now(timezone.utc)
    target = next_recommended_at
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    return target < now
