from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CollectionSchedule, DataCollectionJob
from app.services.companies import parse_listing_date, upsert_company, upsert_company_listing, value_or_none
from app.services.fdr_client import fetch_stock_listing


def collect_companies(db: Session, job: DataCollectionJob) -> dict[str, Any]:
    market = job.market or job.params.get("market", "KOSPI")
    source = job.params.get("source", "FDR")
    rows = fetch_stock_listing(market)
    progress: dict[str, Any] = {
        "total": len(rows),
        "processed": 0,
        "succeeded": 0,
        "failed": 0,
        "failed_items": [],
    }
    max_failed_items = 50

    for row in rows:
        stock_code = str(row.get("Code") or row.get("Symbol") or "").zfill(6)
        try:
            with db.begin_nested():
                corp_name = str(row.get("Name") or "").strip()
                if not stock_code or not corp_name:
                    raise ValueError("Missing stock code or company name.")
                sector = value_or_none(row.get("Sector"))
                industry = value_or_none(row.get("Industry"))
                listed_at = parse_listing_date(row.get("ListingDate"))
                company_id = upsert_company(
                    db,
                    stock_code=stock_code,
                    corp_name=corp_name,
                    market=market,
                    sector=sector,
                    industry=industry,
                    listed_at=listed_at,
                )
                upsert_company_listing(
                    db,
                    company_id=company_id,
                    stock_code=stock_code,
                    stock_name=corp_name,
                    market=market,
                    listed_at=listed_at,
                    source=source,
                )
            progress["succeeded"] += 1
        except Exception as exc:
            progress["failed"] += 1
            if len(progress["failed_items"]) < max_failed_items:
                progress["failed_items"].append(
                    {
                        "stock_code": stock_code or None,
                        "name": row.get("Name"),
                        "error_code": exc.__class__.__name__,
                        "message": str(exc),
                    }
                )
        finally:
            progress["processed"] += 1

    if progress["succeeded"] > 0:
        update_collection_schedule(db, job, "kospi_companies_monthly", timedelta(days=30))
    return progress


def update_collection_schedule(
    db: Session,
    job: DataCollectionJob,
    schedule_code: str,
    interval: timedelta,
) -> None:
    schedule = db.execute(
        select(CollectionSchedule).where(CollectionSchedule.schedule_code == schedule_code)
    ).scalar_one_or_none()
    if schedule is None:
        return
    now = datetime.now(timezone.utc)
    schedule.last_success_job_id = job.id
    schedule.last_success_at = now
    schedule.next_recommended_at = now + interval
    schedule.updated_at = now
