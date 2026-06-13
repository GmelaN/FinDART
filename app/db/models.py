from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Numeric, String, func
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
