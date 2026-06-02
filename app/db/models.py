from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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


class DataCollectionJob(Base):
    __tablename__ = "data_collection_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    job_id: Mapped[str] = mapped_column(String(40), unique=True)
    job_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="QUEUED")
    requested_by: Mapped[str | None] = mapped_column(String(100))
    market: Mapped[str] = mapped_column(String(20), default="KOSPI")
    params: Mapped[dict] = mapped_column(JSONB, default=dict)
    progress: Mapped[dict] = mapped_column(JSONB, default=dict)
    error: Mapped[dict | None] = mapped_column(JSONB)
    parent_job_id: Mapped[int | None] = mapped_column(ForeignKey("data_collection_jobs.id"))
    enqueue_recalculation: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    parent: Mapped["DataCollectionJob | None"] = relationship(remote_side=[id])


class CollectionSchedule(Base):
    __tablename__ = "collection_schedules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    schedule_code: Mapped[str] = mapped_column(String(80), unique=True)
    job_type: Mapped[str] = mapped_column(String(50))
    market: Mapped[str] = mapped_column(String(20), default="KOSPI")
    recommended_interval: Mapped[str] = mapped_column(String(30))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    params: Mapped[dict] = mapped_column(JSONB, default=dict)
    last_success_job_id: Mapped[int | None] = mapped_column(ForeignKey("data_collection_jobs.id"))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_recommended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


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
