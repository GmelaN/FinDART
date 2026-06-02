from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import Company, CompanyListing


def parse_listing_date(value: Any) -> date | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        pass
    if len(text) == 8 and text.isdigit():
        return date(int(text[:4]), int(text[4:6]), int(text[6:8]))
    return None


def value_or_none(value: Any) -> Any:
    if value is None:
        return None
    text = str(value)
    if text.lower() == "nan":
        return None
    return value


def upsert_company(
    db: Session,
    *,
    stock_code: str,
    corp_name: str,
    market: str,
    sector: str | None,
    industry: str | None,
    listed_at: date | None,
) -> int:
    corp_code = f"9{stock_code}0"
    stmt = (
        insert(Company)
        .values(
            corp_code=corp_code,
            stock_code=stock_code,
            corp_name=corp_name,
            market=market,
            sector=sector,
            industry=industry,
            listed_at=listed_at,
            is_active=True,
        )
        .on_conflict_do_update(
            index_elements=[Company.stock_code],
            set_={
                "corp_name": corp_name,
                "market": market,
                "sector": sector,
                "industry": industry,
                "listed_at": listed_at,
                "is_active": True,
            },
        )
        .returning(Company.id)
    )
    return db.execute(stmt).scalar_one()


def upsert_company_listing(
    db: Session,
    *,
    company_id: int,
    stock_code: str,
    stock_name: str,
    market: str,
    listed_at: date | None,
    source: str,
) -> None:
    existing = db.execute(
        select(CompanyListing).where(
            CompanyListing.company_id == company_id,
            CompanyListing.stock_code == stock_code,
            CompanyListing.market == market,
            CompanyListing.listed_at.is_(None) if listed_at is None else CompanyListing.listed_at == listed_at,
        )
    ).scalar_one_or_none()
    if existing:
        existing.stock_name = stock_name
        existing.listing_status = "LISTED"
        existing.source = source
        existing.ended_at = None
        return
    db.add(
        CompanyListing(
            company_id=company_id,
            stock_code=stock_code,
            stock_name=stock_name,
            market=market,
            listed_at=listed_at,
            listing_status="LISTED",
            source=source,
        )
    )
