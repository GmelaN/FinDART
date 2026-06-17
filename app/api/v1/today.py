from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk, ServingPage
from app.db.session import get_db
from app.schemas import TodayEvidenceRead, TodayPageRead, TodaySectionRead

router = APIRouter()

TODAY_PAGE_TYPE = "today"
DEFAULT_USER_ID = ""

SECTION_DEFAULTS: dict[str, Any] = {
    "daily_indicators": {},
    "headlines": [],
    "issues": [],
    "tracked_issues": [],
    "events": [],
}


def _get_today_page(db: Session, page_date: date, market: str, user_id: str = DEFAULT_USER_ID) -> ServingPage:
    page = db.execute(
        select(ServingPage)
        .where(
            ServingPage.page_type == TODAY_PAGE_TYPE,
            ServingPage.page_date == page_date,
            ServingPage.market == market,
            ServingPage.user_id == user_id,
        )
        .order_by(ServingPage.generated_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if page is None:
        raise HTTPException(status_code=404, detail="Today page not found.")
    return page


def _page_response(page: ServingPage) -> TodayPageRead:
    return TodayPageRead(
        page_id=page.page_id,
        page_type=page.page_type,
        page_date=page.page_date,
        market=page.market,
        title=page.title,
        status=page.status,
        payload=page.payload,
        generated_at=page.generated_at,
    )


def _section_response(page: ServingPage, section: str) -> TodaySectionRead:
    return TodaySectionRead(
        page_id=page.page_id,
        page_date=page.page_date,
        market=page.market,
        status=page.status,
        generated_at=page.generated_at,
        section=section,
        data=page.payload.get(section, SECTION_DEFAULTS[section]),
    )


@router.get("", response_model=TodayPageRead)
def get_today_page(
    market: str = Query(default="KR"),
    page_date: date = Query(default_factory=date.today, alias="date"),
    user_id: str = Query(default=DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> TodayPageRead:
    page = _get_today_page(db, page_date=page_date, market=market, user_id=user_id)
    return _page_response(page)


@router.get("/indicators", response_model=TodaySectionRead)
def get_today_indicators(
    market: str = Query(default="KR"),
    page_date: date = Query(default_factory=date.today, alias="date"),
    user_id: str = Query(default=DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> TodaySectionRead:
    page = _get_today_page(db, page_date=page_date, market=market, user_id=user_id)
    return _section_response(page, "daily_indicators")


@router.get("/headlines", response_model=TodaySectionRead)
def get_today_headlines(
    market: str = Query(default="KR"),
    page_date: date = Query(default_factory=date.today, alias="date"),
    user_id: str = Query(default=DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> TodaySectionRead:
    page = _get_today_page(db, page_date=page_date, market=market, user_id=user_id)
    return _section_response(page, "headlines")


@router.get("/issues", response_model=TodaySectionRead)
def get_today_issues(
    market: str = Query(default="KR"),
    page_date: date = Query(default_factory=date.today, alias="date"),
    user_id: str = Query(default=DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> TodaySectionRead:
    page = _get_today_page(db, page_date=page_date, market=market, user_id=user_id)
    return _section_response(page, "issues")


@router.get("/tracked-issues", response_model=TodaySectionRead)
def get_today_tracked_issues(
    market: str = Query(default="KR"),
    page_date: date = Query(default_factory=date.today, alias="date"),
    user_id: str = Query(default=DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> TodaySectionRead:
    page = _get_today_page(db, page_date=page_date, market=market, user_id=user_id)
    return _section_response(page, "tracked_issues")


@router.get("/events", response_model=TodaySectionRead)
def get_today_events(
    market: str = Query(default="KR"),
    page_date: date = Query(default_factory=date.today, alias="date"),
    user_id: str = Query(default=DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> TodaySectionRead:
    page = _get_today_page(db, page_date=page_date, market=market, user_id=user_id)
    return _section_response(page, "events")


@router.get("/evidence/{doc_id}", response_model=TodayEvidenceRead)
def get_today_evidence(
    doc_id: str,
    chunk_id: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    document = db.get(Document, doc_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Evidence document not found.")

    chunk = None
    if chunk_id:
        chunk = db.get(DocumentChunk, chunk_id)
        if chunk is None or chunk.doc_id != doc_id:
            raise HTTPException(status_code=404, detail="Evidence chunk not found.")

    return {
        "document": {
            "doc_id": document.doc_id,
            "title": document.title,
            "source_type": document.source_type,
            "source_name": document.source_name,
            "source_url": document.source_url,
            "summary_kr": document.summary_kr,
            "raw_text": document.raw_text,
            "published_at": document.published_at,
            "metadata": document.metadata_,
        },
        "chunk": None
        if chunk is None
        else {
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "text": chunk.text,
            "metadata": chunk.metadata_,
        },
    }
