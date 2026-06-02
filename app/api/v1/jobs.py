from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CollectionSchedule, DataCollectionJob
from app.db.session import get_db
from app.schemas import (
    CollectCompaniesRequest,
    CollectEventsRequest,
    CollectFilingsRequest,
    CollectFinancialsRequest,
    CollectPricesRequest,
    JobQueuedResponse,
    JobRead,
    SchedulePatch,
    ScheduleRead,
    is_stale,
)
from app.services.jobs import create_collection_job

router = APIRouter()


def _queued_response(job: DataCollectionJob) -> JobQueuedResponse:
    return JobQueuedResponse(job_id=job.job_id, status=job.status, message="Collection job queued.")


@router.post("/collect/companies", response_model=JobQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
def collect_companies(payload: CollectCompaniesRequest, db: Session = Depends(get_db)) -> JobQueuedResponse:
    job = create_collection_job(
        db,
        job_type="COLLECT_COMPANIES",
        market=payload.market,
        params=payload.model_dump(mode="json"),
        enqueue_recalculation=payload.enqueue_recalculation,
    )
    return _queued_response(job)


@router.post("/collect/filings", response_model=JobQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
def collect_filings(payload: CollectFilingsRequest, db: Session = Depends(get_db)) -> JobQueuedResponse:
    job = create_collection_job(
        db,
        job_type="COLLECT_FILINGS",
        market=payload.market,
        params=payload.model_dump(mode="json"),
        enqueue_recalculation=payload.enqueue_recalculation,
    )
    return _queued_response(job)


@router.post("/collect/financials", response_model=JobQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
def collect_financials(payload: CollectFinancialsRequest, db: Session = Depends(get_db)) -> JobQueuedResponse:
    job = create_collection_job(
        db,
        job_type="COLLECT_FINANCIALS",
        market=payload.market,
        params=payload.model_dump(mode="json"),
        enqueue_recalculation=payload.enqueue_recalculation,
    )
    return _queued_response(job)


@router.post("/collect/prices", response_model=JobQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
def collect_prices(payload: CollectPricesRequest, db: Session = Depends(get_db)) -> JobQueuedResponse:
    job = create_collection_job(
        db,
        job_type="COLLECT_PRICES",
        market=payload.market,
        params=payload.model_dump(mode="json"),
        enqueue_recalculation=payload.enqueue_recalculation,
    )
    return _queued_response(job)


@router.post("/collect/events", response_model=JobQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
def collect_events(payload: CollectEventsRequest, db: Session = Depends(get_db)) -> JobQueuedResponse:
    job = create_collection_job(
        db,
        job_type="COLLECT_EVENTS",
        market=payload.market,
        params=payload.model_dump(mode="json"),
        enqueue_recalculation=payload.enqueue_recalculation,
    )
    return _queued_response(job)


@router.get("/schedules", response_model=dict)
def list_schedules(db: Session = Depends(get_db)) -> dict:
    rows = db.execute(select(CollectionSchedule).order_by(CollectionSchedule.id)).scalars().all()
    items = []
    for row in rows:
        item = ScheduleRead.model_validate(row).model_dump(mode="json")
        item["is_stale"] = is_stale(row.next_recommended_at)
        items.append(item)
    return {"items": items, "next_cursor": None, "total": len(items)}


@router.patch("/schedules/{schedule_id}", response_model=ScheduleRead)
def patch_schedule(schedule_id: int, payload: SchedulePatch, db: Session = Depends(get_db)) -> dict:
    schedule = db.get(CollectionSchedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found.")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(schedule, key, value)
    schedule.updated_at = datetime.now(tz=schedule.updated_at.tzinfo) if schedule.updated_at else datetime.now()
    db.commit()
    db.refresh(schedule)
    item = ScheduleRead.model_validate(schedule).model_dump(mode="json")
    item["is_stale"] = is_stale(schedule.next_recommended_at)
    return item


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: str, db: Session = Depends(get_db)) -> DataCollectionJob:
    job = db.execute(select(DataCollectionJob).where(DataCollectionJob.job_id == job_id)).scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@router.get("", response_model=dict)
def list_jobs(
    type: str | None = None,
    job_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    cursor: int | None = None,
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(DataCollectionJob)
    if type:
        stmt = stmt.where(DataCollectionJob.job_type == type)
    if job_status:
        stmt = stmt.where(DataCollectionJob.status == job_status)
    if cursor:
        stmt = stmt.where(DataCollectionJob.id > cursor)
    rows = db.execute(stmt.order_by(DataCollectionJob.id.desc()).limit(limit + 1)).scalars().all()
    items = rows[:limit]
    next_cursor = str(items[-1].id) if len(rows) > limit and items else None
    return {
        "items": [JobRead.model_validate(item).model_dump(mode="json") for item in items],
        "next_cursor": next_cursor,
        "total": None,
    }
