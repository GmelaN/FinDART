from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk, ServingPage, TrackedIssue
from app.db.session import get_db
from app.schemas import (
    TodayEvidenceRead,
    TodayIndicatorValues,
    TodayPageRead,
    TodaySectionRead,
    TrackedIssueCreate,
    TrackedIssueRead,
)

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

INDICATOR_CATEGORY_ALIASES: dict[str, tuple[str, ...]] = {
    "interest_rate": ("interest_rate", "interest_rates", "rate", "rates"),
    "fx": ("fx", "foreign_exchange", "exchange_rate", "exchange_rates", "currency"),
    "inflation": ("inflation", "prices", "price", "cpi"),
    "growth": ("growth", "economic_growth", "gdp", "growth_index"),
}

VALUE_ALIASES = ("today", "today_value", "current", "current_value", "value", "actual", "latest")
PREVIOUS_VALUE_ALIASES = (
    "previous",
    "previous_value",
    "prev",
    "prev_value",
    "yesterday",
    "yesterday_value",
    "prior",
    "prior_value",
)
DATE_ALIASES = ("date", "as_of", "base_date", "today_date")
PREVIOUS_DATE_ALIASES = ("previous_date", "prev_date", "yesterday_date", "prior_date")


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


def _first_present(source: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in source:
            return source[key]
    return None


def _looks_like_indicator_value(value: Any) -> bool:
    return isinstance(value, dict) and (
        _first_present(value, VALUE_ALIASES) is not None
        or _first_present(value, PREVIOUS_VALUE_ALIASES) is not None
        or "change" in value
        or "change_rate" in value
    )


def _find_indicator_source(payload: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    daily_indicators = payload.get("daily_indicators", {})
    candidates = [daily_indicators, payload.get("indicator_values", {}), payload.get("indicators", {})]
    normalized_aliases = {alias.lower() for alias in aliases}

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        for alias in aliases:
            value = candidate.get(alias)
            if value is not None:
                return value
        items = candidate.get("items")
        if isinstance(items, list):
            matches = [
                item
                for item in items
                if isinstance(item, dict)
                and str(
                    item.get("category")
                    or item.get("type")
                    or item.get("key")
                    or item.get("name")
                    or ""
                ).lower()
                in normalized_aliases
            ]
            if matches:
                return matches
    return None


def _normalize_indicator_item(item: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "name": item.get("name") or item.get("label") or item.get("title"),
        "today_value": _first_present(item, VALUE_ALIASES),
        "previous_value": _first_present(item, PREVIOUS_VALUE_ALIASES),
        "date": _first_present(item, DATE_ALIASES),
        "previous_date": _first_present(item, PREVIOUS_DATE_ALIASES),
        "unit": item.get("unit"),
        "change": item.get("change"),
        "change_rate": item.get("change_rate"),
    }
    return {key: value for key, value in normalized.items() if value is not None}


def _normalize_indicator_source(source: Any) -> Any:
    if isinstance(source, list):
        return [_normalize_indicator_item(item) for item in source if isinstance(item, dict)]
    if isinstance(source, dict):
        if _looks_like_indicator_value(source):
            return _normalize_indicator_item(source)
        normalized: dict[str, Any] = {}
        for key, value in source.items():
            if isinstance(value, dict):
                normalized[key] = _normalize_indicator_item(value) if _looks_like_indicator_value(value) else value
            else:
                normalized[key] = value
        return normalized
    return source


def _indicator_values(payload: dict[str, Any]) -> TodayIndicatorValues:
    values = {
        name: _normalize_indicator_source(_find_indicator_source(payload, aliases))
        for name, aliases in INDICATOR_CATEGORY_ALIASES.items()
    }
    return TodayIndicatorValues(**values)


def _page_response(page: ServingPage) -> TodayPageRead:
    return TodayPageRead(
        page_id=page.page_id,
        page_type=page.page_type,
        page_date=page.page_date,
        market=page.market,
        title=page.title,
        status=page.status,
        indicator_values=_indicator_values(page.payload),
        payload=page.payload,
        generated_at=page.generated_at,
    )


def _section_response(page: ServingPage, section: str) -> TodaySectionRead:
    data = page.payload.get(section, SECTION_DEFAULTS[section])
    if section == "daily_indicators":
        data = {"indicator_values": _indicator_values(page.payload).model_dump(), "daily_indicators": data}
    return TodaySectionRead(
        page_id=page.page_id,
        page_date=page.page_date,
        market=page.market,
        status=page.status,
        generated_at=page.generated_at,
        section=section,
        data=data,
    )


def _tracked_issue_response(issue: TrackedIssue) -> TrackedIssueRead:
    return TrackedIssueRead(
        subscription_key=issue.subscription_key,
        issue=issue.issue,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
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


@router.get("/tracked-issues", response_model=list[TrackedIssueRead])
def get_today_tracked_issues(
    market: str = Query(default="KR"),
    user_id: str = Query(default=DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> list[TrackedIssueRead]:
    rows = db.execute(
        select(TrackedIssue)
        .where(TrackedIssue.market == market, TrackedIssue.user_id == user_id)
        .order_by(TrackedIssue.created_at.desc(), TrackedIssue.id.desc())
    ).scalars()
    return [_tracked_issue_response(row) for row in rows]


@router.post("/tracked-issues", response_model=TrackedIssueRead, status_code=status.HTTP_201_CREATED)
def add_today_tracked_issue(
    request: TrackedIssueCreate,
    market: str = Query(default="KR"),
    user_id: str = Query(default=DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> TrackedIssueRead:
    issue = db.execute(
        select(TrackedIssue).where(
            TrackedIssue.market == market,
            TrackedIssue.user_id == user_id,
            TrackedIssue.subscription_key == request.subscription_key,
        )
    ).scalar_one_or_none()
    if issue is None:
        issue = TrackedIssue(
            market=market,
            user_id=user_id,
            subscription_key=request.subscription_key,
            issue=request.issue,
        )
        db.add(issue)
    else:
        issue.issue = request.issue
        issue.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(issue)
    return _tracked_issue_response(issue)


@router.delete("/tracked-issues/{subscription_key}", status_code=status.HTTP_204_NO_CONTENT)
def remove_today_tracked_issue(
    subscription_key: str,
    market: str = Query(default="KR"),
    user_id: str = Query(default=DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> Response:
    issue = db.execute(
        select(TrackedIssue).where(
            TrackedIssue.market == market,
            TrackedIssue.user_id == user_id,
            TrackedIssue.subscription_key == subscription_key,
        )
    ).scalar_one_or_none()
    if issue is None:
        raise HTTPException(status_code=404, detail="Tracked issue not found.")
    db.delete(issue)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
