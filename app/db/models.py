from datetime import date, datetime

from typing import Any

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    corp_code: Mapped[str] = mapped_column(String(8), unique=True)
    stock_code: Mapped[str] = mapped_column(String(6), unique=True)
    corp_name: Mapped[str] = mapped_column(String(200))
    corp_name_eng: Mapped[str | None] = mapped_column(String(200))
    market: Mapped[str] = mapped_column(String(20), default="KOSPI")
    sector: Mapped[str | None] = mapped_column(String(100))
    industry: Mapped[str | None] = mapped_column(String(100))
    fiscal_month: Mapped[int | None]
    listed_at: Mapped[date | None] = mapped_column(Date)
    delisted_at: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CompanyListing(Base):
    __tablename__ = "company_listings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    stock_code: Mapped[str] = mapped_column(String(6))
    stock_name: Mapped[str] = mapped_column(String(200))
    market: Mapped[str] = mapped_column(String(20))
    listed_at: Mapped[date | None] = mapped_column(Date)
    ended_at: Mapped[date | None] = mapped_column(Date)
    listing_status: Mapped[str] = mapped_column(String(30))
    source: Mapped[str] = mapped_column(String(50))


class DailyPrice(Base):
    __tablename__ = "daily_prices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    trade_date: Mapped[date] = mapped_column(Date)
    open: Mapped[float | None] = mapped_column(Numeric(18, 4))
    high: Mapped[float | None] = mapped_column(Numeric(18, 4))
    low: Mapped[float | None] = mapped_column(Numeric(18, 4))
    close: Mapped[float] = mapped_column(Numeric(18, 4))
    adjusted_close: Mapped[float | None] = mapped_column(Numeric(18, 4))
    volume: Mapped[int | None] = mapped_column(BigInteger)
    change_rate: Mapped[float | None] = mapped_column(Numeric(12, 8))
    market_cap: Mapped[float | None] = mapped_column(Numeric(24, 4))
    shares_outstanding: Mapped[float | None] = mapped_column(Numeric(24, 4))
    source: Mapped[str] = mapped_column(String(50))


class ServingPage(Base):
    __tablename__ = "serving_pages"

    page_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    page_type: Mapped[str] = mapped_column(String(50))
    page_date: Mapped[date] = mapped_column(Date)
    market: Mapped[str] = mapped_column(String(20))
    user_id: Mapped[str] = mapped_column(String(100), default="")
    title: Mapped[str | None] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(30), default="ready")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TrackedIssue(Base):
    __tablename__ = "tracked_issues"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "market",
            "subscription_key",
            name="uq_tracked_issues_user_market_key",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), default="")
    market: Mapped[str] = mapped_column(String(20), default="KR")
    subscription_key: Mapped[str] = mapped_column(String(200))
    issue: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Document(Base):
    __tablename__ = "documents"

    doc_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    source_type: Mapped[str | None] = mapped_column(String(50))
    source_name: Mapped[str | None] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(Text)
    summary_kr: Mapped[str | None] = mapped_column(Text)
    raw_text: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    chunk_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    doc_id: Mapped[str] = mapped_column(ForeignKey("documents.doc_id", ondelete="CASCADE"))
    chunk_index: Mapped[int | None] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvidenceLink(Base):
    __tablename__ = "evidence_links"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    target_type: Mapped[str] = mapped_column(String(50))
    target_id: Mapped[str] = mapped_column(String(120))
    section_key: Mapped[str | None] = mapped_column(String(80))
    doc_id: Mapped[str | None] = mapped_column(ForeignKey("documents.doc_id", ondelete="SET NULL"))
    chunk_id: Mapped[str | None] = mapped_column(ForeignKey("document_chunks.chunk_id", ondelete="SET NULL"))
    final_rank: Mapped[int | None] = mapped_column(Integer)
    score: Mapped[float | None] = mapped_column(Numeric(12, 8))
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
