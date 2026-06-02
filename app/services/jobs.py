from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import DataCollectionJob


def create_collection_job(
    db: Session,
    *,
    job_type: str,
    market: str,
    params: dict,
    enqueue_recalculation: bool,
    requested_by: str | None = None,
) -> DataCollectionJob:
    job = DataCollectionJob(
        job_id=f"job_{uuid4().hex[:26]}",
        job_type=job_type,
        status="QUEUED",
        requested_by=requested_by,
        market=market,
        params=params,
        progress={"total": None, "processed": 0, "succeeded": 0, "failed": 0},
        enqueue_recalculation=enqueue_recalculation,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

