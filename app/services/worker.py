from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DataCollectionJob
from app.services.collectors import collect_companies


SUPPORTED_JOB_TYPES = {"COLLECT_COMPANIES"}


def claim_next_job(db: Session) -> DataCollectionJob | None:
    job = db.execute(
        select(DataCollectionJob)
        .where(DataCollectionJob.status == "QUEUED")
        .order_by(DataCollectionJob.created_at, DataCollectionJob.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    ).scalar_one_or_none()
    if job is None:
        return None
    job.status = "RUNNING"
    job.started_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job


def process_job(db: Session, job: DataCollectionJob) -> DataCollectionJob:
    try:
        if job.job_type == "COLLECT_COMPANIES":
            progress = collect_companies(db, job)
        else:
            raise NotImplementedError(f"Unsupported job type: {job.job_type}")

        job.progress = progress
        if progress.get("failed", 0) == 0:
            job.status = "SUCCESS"
            job.error = None
        elif progress.get("succeeded", 0) == 0:
            job.status = "FAILED"
            job.error = {"message": "All items failed."}
        else:
            job.status = "PARTIAL_SUCCESS"
            job.error = {"message": "Some items failed."}
    except Exception as exc:
        db.rollback()
        job.status = "FAILED"
        job.error = {"error_code": exc.__class__.__name__, "message": str(exc)}
    finally:
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
    return job


def run_once(db: Session) -> DataCollectionJob | None:
    job = claim_next_job(db)
    if job is None:
        return None
    return process_job(db, job)
