# finDART API spec

## Scope

This FastAPI service exposes:

- read APIs for data already stored in PostgreSQL
- ingest APIs for the external `FinDART-data` pipeline to insert or update collected rows

The API server still does not call OpenDART, KRX, FinanceDataReader, or other external providers directly. External collection remains the responsibility of the separate data pipeline.

## Base URL

All endpoints are mounted under:

```text
/api/v1
```

Example:

```text
https://findart.example.com/api/v1/health
```

## Implemented Endpoints

```text
GET  /api/v1/health
GET  /api/v1/health/dependencies
GET  /api/v1/companies
GET  /api/v1/companies/by-stock/{stock_code}
GET  /api/v1/companies/{company_id}
GET  /api/v1/today
GET  /api/v1/today/indicators
GET  /api/v1/today/headlines
GET  /api/v1/today/issues
GET  /api/v1/today/tracked-issues
GET  /api/v1/today/events
GET  /api/v1/today/evidence/{doc_id}

POST /api/v1/ingest/companies
POST /api/v1/ingest/company-listings
POST /api/v1/ingest/dart-filings
POST /api/v1/ingest/financial-statement-items
```

## Rules

- API versioning is part of the URL.
- Date values use `YYYY-MM-DD`.
- List endpoints use cursor pagination where implemented.
- Read handlers read from PostgreSQL only.
- Ingest handlers receive JSON arrays and write to PostgreSQL.
- Ingest clients should send `companies` before dependent rows.

## Health

### GET `/health`

Returns service status.

### GET `/health/dependencies`

Checks database connectivity.

Response:

```json
{
  "status": "ok",
  "dependencies": {
    "database": "ok"
  }
}
```

## Companies

### GET `/companies`

Returns companies stored in the database.

Query:

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `market` | string | `KOSPI` | Market filter |
| `q` | string nullable |  | Company name search or exact stock code |
| `sector` | string nullable |  | Sector filter |
| `is_active` | boolean | `true` | Active company filter |
| `limit` | integer | `50` | Minimum `1`, maximum `200` |
| `cursor` | integer nullable |  | Last seen company id |

### GET `/companies/by-stock/{stock_code}`

Returns one company by exact stock code.

### GET `/companies/{company_id}`

Returns one company by internal database id.

## Today

Today endpoints read from `serving_pages.payload` first. Supporting tables such as
`documents`, `document_chunks`, and `evidence_links` are for evidence drill-down,
payload regeneration, and operations/debugging.

Common query:

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `market` | string | `KR` | Market code |
| `date` | date | server today | Page date in `YYYY-MM-DD` |
| `user_id` | string | empty string | User-specific page key. The shared Today page uses `""`. |

### GET `/today`

Returns the latest Today serving page for the requested market/date/user.

Read query:

```sql
select page_id, page_type, page_date, market, title, status, payload, generated_at
from serving_pages
where page_type = 'today'
  and page_date = :date
  and market = :market
  and user_id = :user_id
order by generated_at desc
limit 1;
```

Response:

```json
{
  "page_id": "today-KR-2026-06-17",
  "page_type": "today",
  "page_date": "2026-06-17",
  "market": "KR",
  "title": "Today",
  "status": "ready",
  "generated_at": "2026-06-17T09:00:00+09:00",
  "payload": {
    "page_type": "today",
    "daily_indicators": {},
    "market_regimes": {},
    "headlines": [],
    "issues": [],
    "tracked_issues": [],
    "events": []
  }
}
```

### GET `/today/indicators`

Returns `payload.daily_indicators`, including interest rates, FX pairs,
inflation, and growth indicators.

### GET `/today/headlines`

Returns `payload.headlines`. Items are expected to include title, one-sentence
headline text, summary, news URL, source, published time, and evidence.

### GET `/today/issues`

Returns `payload.issues`. Items are expected to include `subscription_key` so the
frontend can add the issue to Issue Tracking.

### GET `/today/tracked-issues`

Returns `payload.tracked_issues`. Items are expected to include
`subscription_key`, `is_subscribed`, and `unsubscribe_action`.

### GET `/today/events`

Returns `payload.events`, covering policy briefings, news, disclosures, macro
indicator events, and market movement events.

### GET `/today/evidence/{doc_id}`

Returns source document detail from `documents`. Pass optional `chunk_id` to
also return one chunk from `document_chunks`.

Example:

```text
GET /api/v1/today/evidence/news-123?chunk_id=news-123-0
```

## Ingest

All ingest endpoints accept a JSON array and return:

```json
{
  "received": 1,
  "inserted_or_updated": 1
}
```

### POST `/ingest/companies`

Upserts company master rows by `corp_code`.

Request:

```json
[
  {
    "corp_code": "00126380",
    "stock_code": "005930",
    "corp_name": "삼성전자",
    "corp_name_eng": null,
    "market": "KOSPI",
    "sector": "전기전자",
    "industry": "전자제품",
    "fiscal_month": 12,
    "listed_at": "1975-06-11",
    "delisted_at": null,
    "is_active": true
  }
]
```

### POST `/ingest/company-listings`

Upserts listing rows. `corp_code` must already exist in `companies`.

Request:

```json
[
  {
    "corp_code": "00126380",
    "stock_code": "005930",
    "stock_name": "삼성전자",
    "market": "KOSPI",
    "listed_at": "1975-06-11",
    "ended_at": null,
    "listing_status": "LISTED",
    "source": "KRX"
  }
]
```

### POST `/ingest/dart-filings`

Upserts DART filing metadata by `rcept_no`. `corp_code` must already exist in `companies`.

Request:

```json
[
  {
    "corp_code": "00126380",
    "stock_code": "005930",
    "rcept_no": "20260312001234",
    "report_code": "11011",
    "report_name": "사업보고서 (2025.12)",
    "report_year": 2025,
    "report_period": "FY",
    "receipt_date": "2026-03-12",
    "filing_date": "2026-03-12",
    "is_consolidated": true,
    "source_url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260312001234",
    "raw_payload": {}
  }
]
```

### POST `/ingest/financial-statement-items`

Upserts a `financial_statements` header and then replaces a matching item row by:

```text
statement_id, dart_account_id, account_name, ordinal
```

`corp_code` must already exist in `companies`. If `rcept_no` exists in `dart_filings`, it is linked as `filing_id`.

Request:

```json
[
  {
    "corp_code": "00126380",
    "stock_code": "005930",
    "rcept_no": "20260312001234",
    "report_code": "11011",
    "report_year": 2025,
    "report_period": "FY",
    "statement_type": "BS",
    "statement_name": "재무상태표",
    "is_consolidated": true,
    "currency": "KRW",
    "unit": 1,
    "dart_account_id": "ifrs-full_Assets",
    "account_name": "자산총계",
    "account_detail": null,
    "amount": 1000000000,
    "amount_previous": 900000000,
    "amount_before_previous": 800000000,
    "ordinal": 1,
    "period_start": "2025-01-01",
    "period_end": "2025-12-31",
    "raw_payload": {}
  }
]
```

## FinDART-data Mapping

`FinDART-data/collect_findart_data.py` sends batches in this order:

```text
GET  {server}{base}/health/dependencies
POST {server}{base}/ingest/companies
POST {server}{base}/ingest/company-listings
POST {server}{base}/ingest/dart-filings
POST {server}{base}/ingest/financial-statement-items
```

With:

```env
FINDART_SERVER_URL=https://findart.example.com
FINDART_API_BASE=/api/v1
```

the first ingest URL is:

```text
https://findart.example.com/api/v1/ingest/companies
```
