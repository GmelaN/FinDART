from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


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


class CompanyIngest(BaseModel):
    corp_code: str
    stock_code: str
    corp_name: str
    corp_name_eng: str | None = None
    market: str = "KOSPI"
    sector: str | None = None
    industry: str | None = None
    fiscal_month: int | None = None
    listed_at: date | None = None
    delisted_at: date | None = None
    is_active: bool = True


class CompanyListingIngest(BaseModel):
    corp_code: str
    stock_code: str
    stock_name: str
    market: str
    listed_at: date | None = None
    ended_at: date | None = None
    listing_status: str = "LISTED"
    source: str = "KRX"


class DartFilingIngest(BaseModel):
    corp_code: str
    stock_code: str | None = None
    rcept_no: str
    report_code: str
    report_name: str
    report_year: int
    report_period: str
    receipt_date: date | None = None
    filing_date: date | None = None
    is_consolidated: bool | None = None
    source_url: str | None = None
    raw_payload: dict[str, Any] | None = None


class FinancialStatementItemIngest(BaseModel):
    corp_code: str
    stock_code: str | None = None
    rcept_no: str | None = None
    report_code: str
    report_year: int
    report_period: str
    statement_type: str
    statement_name: str | None = None
    is_consolidated: bool = True
    currency: str = "KRW"
    unit: int = 1
    dart_account_id: str | None = None
    account_name: str
    account_detail: str | None = None
    amount: float | None = None
    amount_previous: float | None = None
    amount_before_previous: float | None = None
    ordinal: int | None = None
    period_start: date | None = None
    period_end: date | None = None
    raw_payload: dict[str, Any] | None = None


class IngestResult(BaseModel):
    received: int
    inserted_or_updated: int


class TodayPageRead(BaseModel):
    page_id: str
    page_type: str
    page_date: date
    market: str
    title: str | None = None
    status: str
    payload: dict[str, Any]
    generated_at: datetime


class TodaySectionRead(BaseModel):
    page_id: str
    page_date: date
    market: str
    status: str
    generated_at: datetime
    section: str
    data: Any


class TodayEvidenceDocumentRead(BaseModel):
    doc_id: str
    title: str
    source_type: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    summary_kr: str | None = None
    raw_text: str | None = None
    published_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class TodayEvidenceChunkRead(BaseModel):
    chunk_id: str
    doc_id: str
    text: str
    metadata: dict[str, Any] | None = None


class TodayEvidenceRead(BaseModel):
    document: TodayEvidenceDocumentRead
    chunk: TodayEvidenceChunkRead | None = None

