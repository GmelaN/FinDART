from __future__ import annotations

import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import (
    CompanyIngest,
    CompanyListingIngest,
    DartFilingIngest,
    FinancialStatementItemIngest,
    IngestResult,
)

router = APIRouter()


def _db_error(status_code: int, endpoint: str, row_index: int, row_key: str | None, error: SQLAlchemyError) -> HTTPException:
    original = getattr(error, "orig", error)
    detail = {
        "endpoint": endpoint,
        "row_index": row_index,
        "row_key": row_key,
        "error_type": type(original).__name__,
        "message": str(original),
    }
    return HTTPException(status_code=status_code, detail=detail)


def _company_id(db: Session, corp_code: str) -> int:
    company_id = db.execute(text("select id from companies where corp_code = :corp_code"), {"corp_code": corp_code}).scalar()
    if company_id is None:
        raise HTTPException(status_code=400, detail=f"Unknown corp_code: {corp_code}")
    return int(company_id)


def _filing_id(db: Session, rcept_no: str | None) -> int | None:
    if not rcept_no:
        return None
    return db.execute(text("select id from dart_filings where rcept_no = :rcept_no"), {"rcept_no": rcept_no}).scalar()


def _period_dates(row: FinancialStatementItemIngest) -> tuple[date, date]:
    if row.period_end:
        return row.period_start or date(row.report_year, 1, 1), row.period_end
    if row.report_period == "Q1":
        return date(row.report_year, 1, 1), date(row.report_year, 3, 31)
    if row.report_period == "H1":
        return date(row.report_year, 1, 1), date(row.report_year, 6, 30)
    if row.report_period == "Q3":
        return date(row.report_year, 1, 1), date(row.report_year, 9, 30)
    return date(row.report_year, 1, 1), date(row.report_year, 12, 31)


@router.post("/companies", response_model=IngestResult)
def ingest_companies(rows: list[CompanyIngest], db: Session = Depends(get_db)) -> IngestResult:
    for index, row in enumerate(rows):
        try:
            existing_id = db.execute(
                text("select id from companies where corp_code = :corp_code or stock_code = :stock_code limit 1"),
                {"corp_code": row.corp_code, "stock_code": row.stock_code},
            ).scalar()
            payload = row.model_dump()
            if existing_id is None:
                db.execute(
                    text(
                        """
                        insert into companies (
                            corp_code, stock_code, corp_name, corp_name_eng, market, sector, industry,
                            fiscal_month, listed_at, delisted_at, is_active
                        )
                        values (
                            :corp_code, :stock_code, :corp_name, :corp_name_eng, :market, :sector, :industry,
                            :fiscal_month, :listed_at, :delisted_at, :is_active
                        )
                        """
                    ),
                    payload,
                )
            else:
                payload["id"] = existing_id
                db.execute(
                    text(
                        """
                        update companies set
                            corp_code = :corp_code,
                            stock_code = :stock_code,
                            corp_name = :corp_name,
                            corp_name_eng = :corp_name_eng,
                            market = :market,
                            sector = :sector,
                            industry = :industry,
                            fiscal_month = :fiscal_month,
                            listed_at = :listed_at,
                            delisted_at = :delisted_at,
                            is_active = :is_active,
                            updated_at = now()
                        where id = :id
                        """
                    ),
                    payload,
                )
        except IntegrityError as error:
            db.rollback()
            raise _db_error(409, "companies", index, row.corp_code, error) from error
        except SQLAlchemyError as error:
            db.rollback()
            raise _db_error(500, "companies", index, row.corp_code, error) from error
    db.commit()
    return IngestResult(received=len(rows), inserted_or_updated=len(rows))


@router.post("/company-listings", response_model=IngestResult)
def ingest_company_listings(rows: list[CompanyListingIngest], db: Session = Depends(get_db)) -> IngestResult:
    for row in rows:
        payload = row.model_dump()
        payload["company_id"] = _company_id(db, row.corp_code)
        db.execute(
            text(
                """
                insert into company_listings (
                    company_id, stock_code, stock_name, market, listed_at, ended_at, listing_status, source
                )
                values (
                    :company_id, :stock_code, :stock_name, :market, :listed_at, :ended_at, :listing_status, :source
                )
                on conflict (company_id, stock_code, market, listed_at) do update set
                    stock_name = excluded.stock_name,
                    ended_at = excluded.ended_at,
                    listing_status = excluded.listing_status,
                    source = excluded.source
                """
            ),
            payload,
        )
    db.commit()
    return IngestResult(received=len(rows), inserted_or_updated=len(rows))


@router.post("/dart-filings", response_model=IngestResult)
def ingest_dart_filings(rows: list[DartFilingIngest], db: Session = Depends(get_db)) -> IngestResult:
    for row in rows:
        payload = row.model_dump()
        payload["company_id"] = _company_id(db, row.corp_code)
        payload["receipt_date"] = row.receipt_date or row.filing_date or date(row.report_year, 12, 31)
        payload["raw_payload"] = json.dumps(row.raw_payload, ensure_ascii=False) if row.raw_payload else None
        db.execute(
            text(
                """
                insert into dart_filings (
                    company_id, rcept_no, report_code, report_name, report_year, report_period,
                    receipt_date, filing_date, is_consolidated, source_url, raw_payload
                )
                values (
                    :company_id, :rcept_no, :report_code, :report_name, :report_year, :report_period,
                    :receipt_date, :filing_date, :is_consolidated, :source_url, cast(:raw_payload as jsonb)
                )
                on conflict (rcept_no) do update set
                    report_code = excluded.report_code,
                    report_name = excluded.report_name,
                    report_year = excluded.report_year,
                    report_period = excluded.report_period,
                    receipt_date = excluded.receipt_date,
                    filing_date = excluded.filing_date,
                    is_consolidated = excluded.is_consolidated,
                    source_url = excluded.source_url,
                    raw_payload = excluded.raw_payload
                """
            ),
            payload,
        )
    db.commit()
    return IngestResult(received=len(rows), inserted_or_updated=len(rows))


@router.post("/financial-statement-items", response_model=IngestResult)
def ingest_financial_statement_items(
    rows: list[FinancialStatementItemIngest], db: Session = Depends(get_db)
) -> IngestResult:
    for row in rows:
        company_id = _company_id(db, row.corp_code)
        filing_id = _filing_id(db, row.rcept_no)
        period_start, period_end = _period_dates(row)
        statement_payload = {
            "company_id": company_id,
            "filing_id": filing_id,
            "report_year": row.report_year,
            "report_period": row.report_period,
            "statement_type": row.statement_type,
            "currency": row.currency,
            "unit": row.unit,
            "is_consolidated": row.is_consolidated,
            "accounting_standard": None,
            "period_start": period_start,
            "period_end": period_end,
        }
        statement_id = db.execute(
            text(
                """
                insert into financial_statements (
                    company_id, filing_id, report_year, report_period, statement_type, currency, unit,
                    is_consolidated, accounting_standard, period_start, period_end
                )
                values (
                    :company_id, :filing_id, :report_year, :report_period, :statement_type, :currency, :unit,
                    :is_consolidated, :accounting_standard, :period_start, :period_end
                )
                on conflict (company_id, report_year, report_period, statement_type, is_consolidated)
                do update set
                    filing_id = coalesce(excluded.filing_id, financial_statements.filing_id),
                    currency = excluded.currency,
                    unit = excluded.unit,
                    accounting_standard = excluded.accounting_standard,
                    period_start = excluded.period_start,
                    period_end = excluded.period_end
                returning id
                """
            ),
            statement_payload,
        ).scalar_one()
        item_payload = row.model_dump()
        item_payload["statement_id"] = statement_id
        item_payload["raw_payload"] = json.dumps(row.raw_payload, ensure_ascii=False) if row.raw_payload else None
        db.execute(
            text(
                """
                delete from financial_statement_items
                where statement_id = :statement_id
                  and dart_account_id is not distinct from :dart_account_id
                  and account_name = :account_name
                  and ordinal is not distinct from :ordinal
                """
            ),
            item_payload,
        )
        db.execute(
            text(
                """
                insert into financial_statement_items (
                    statement_id, dart_account_id, account_name, account_detail, amount,
                    amount_previous, amount_before_previous, ordinal, raw_payload
                )
                values (
                    :statement_id, :dart_account_id, :account_name, :account_detail, :amount,
                    :amount_previous, :amount_before_previous, :ordinal, cast(:raw_payload as jsonb)
                )
                """
            ),
            item_payload,
        )
    db.commit()
    return IngestResult(received=len(rows), inserted_or_updated=len(rows))
