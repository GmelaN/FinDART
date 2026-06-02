from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import Company
from app.db.session import get_db
from app.schemas import CompanyRead

router = APIRouter()


@router.get("", response_model=dict)
def list_companies(
    market: str = "KOSPI",
    q: str | None = None,
    sector: str | None = None,
    is_active: bool = True,
    limit: int = Query(default=50, ge=1, le=200),
    cursor: int | None = None,
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(Company).where(Company.market == market, Company.is_active == is_active)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Company.corp_name.ilike(like), Company.stock_code == q))
    if sector:
        stmt = stmt.where(Company.sector == sector)
    if cursor:
        stmt = stmt.where(Company.id > cursor)
    rows = db.execute(stmt.order_by(Company.id).limit(limit + 1)).scalars().all()
    items = rows[:limit]
    next_cursor = str(items[-1].id) if len(rows) > limit and items else None
    return {
        "items": [CompanyRead.model_validate(item).model_dump(mode="json") for item in items],
        "next_cursor": next_cursor,
        "total": None,
    }


@router.get("/by-stock/{stock_code}", response_model=CompanyRead)
def get_company_by_stock(stock_code: str, db: Session = Depends(get_db)) -> Company:
    company = db.execute(select(Company).where(Company.stock_code == stock_code)).scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found.")
    return company


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db)) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found.")
    return company
