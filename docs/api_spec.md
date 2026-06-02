# finDART API spec draft

## 개요

FastAPI 기반 REST API 초안이다. 초기 목표는 KOSPI 기업의 재무/주가/이벤트 원천 데이터와 신용도 분석 지표를 조회하고, 수집/재계산 작업을 비동기로 실행하는 것이다.

기본 원칙:

- API 버전은 URL에 포함한다. 예: `/api/v1`
- 날짜는 `YYYY-MM-DD` 형식으로 주고받는다.
- 금액과 비율은 JSON number로 반환하되, DB 내부는 `numeric`을 사용한다.
- 대량 목록 API는 cursor 기반 페이지네이션을 기본으로 한다.
- 조회 API는 OpenDartReader 또는 FinanceDataReader를 직접 호출하지 않고 DB에 저장된 최신 성공 데이터만 읽는다.
- 외부 데이터 fetch는 `POST /jobs/...` 트리거가 생성한 DB job을 별도 worker가 처리한다.
- 분석 결과는 `as_of_date`, `report_year`, `report_period`, `statement_basis`, `price_window_days` 조합을 명시한다.
- 원천 데이터 결측과 계산 실패를 숨기지 않는다. `status`, `confidence`, `note`, `missing_fields`를 응답에 포함한다.

## 공통 규약

### Base URL

```text
/api/v1
```

### 공통 query parameter

| 이름 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `limit` | integer | 50 | 최대 200 |
| `cursor` | string nullable | null | 다음 페이지 커서 |
| `sort` | string nullable | null | 정렬 키. 예: `corp_name`, `-as_of_date` |

### 공통 list response

```json
{
  "items": [],
  "next_cursor": null,
  "total": null
}
```

`total`은 비용이 큰 경우 `null`을 허용한다.

### 공통 error response

```json
{
  "error": {
    "code": "COMPANY_NOT_FOUND",
    "message": "Company not found.",
    "details": {
      "stock_code": "005930"
    }
  }
}
```

주요 HTTP status:

| Status | 사용처 |
| --- | --- |
| 400 | 잘못된 파라미터 |
| 404 | 리소스 없음 |
| 409 | 이미 실행 중인 작업 또는 중복 요청 |
| 422 | 유효성 검증 실패 |
| 500 | 서버 내부 오류 |
| 503 | 외부 데이터 소스 장애 |

## 도메인 enum

### Market

```text
KOSPI
KOSDAQ
KONEX
```

초기 서비스에서는 `KOSPI`만 공식 지원한다.

### ReportPeriod

```text
FY
Q1
Q2
Q3
TTM
```

### StatementType

```text
BS
IS
CIS
CF
```

### StatementBasis

```text
CONSOLIDATED
SEPARATE
```

### CalculationStatus

```text
SUCCESS
PARTIAL
FAILED
```

### RiskLevel

```text
LOW
MEDIUM
HIGH
DISTRESS
```

## Health

### GET `/health`

서비스 상태 확인.

Response:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "time": "2026-06-01T16:00:00+09:00"
}
```

### GET `/health/dependencies`

DB 및 외부 의존성 상태 확인.

Response:

```json
{
  "status": "ok",
  "dependencies": {
    "database": "ok",
    "dart": "ok",
    "finance_datareader": "ok"
  }
}
```

## Companies

### GET `/companies`

기업 목록 조회.

Query:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `market` | string | 기본 `KOSPI` |
| `q` | string nullable | 회사명 또는 종목코드 검색 |
| `sector` | string nullable | 업종 |
| `is_active` | boolean | 기본 `true` |
| `limit` | integer | 페이지 크기 |
| `cursor` | string nullable | 페이지 커서 |

Response:

```json
{
  "items": [
    {
      "id": 1,
      "corp_code": "00126380",
      "stock_code": "005930",
      "corp_name": "삼성전자",
      "market": "KOSPI",
      "sector": "전기전자",
      "industry": "반도체",
      "fiscal_month": 12,
      "listed_at": "1975-06-11",
      "is_active": true
    }
  ],
  "next_cursor": null,
  "total": null
}
```

### GET `/companies/{company_id}`

기업 상세 조회.

Response:

```json
{
  "id": 1,
  "corp_code": "00126380",
  "stock_code": "005930",
  "corp_name": "삼성전자",
  "corp_name_eng": "SAMSUNG ELECTRONICS CO., LTD.",
  "market": "KOSPI",
  "sector": "전기전자",
  "industry": "반도체",
  "fiscal_month": 12,
  "listed_at": "1975-06-11",
  "delisted_at": null,
  "is_active": true,
  "updated_at": "2026-06-01T16:00:00+09:00"
}
```

### GET `/companies/by-stock/{stock_code}`

종목코드로 기업 조회.

### GET `/companies/{company_id}/listings`

상장 정보 이력 조회.

Response:

```json
{
  "items": [
    {
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "market": "KOSPI",
      "listed_at": "1975-06-11",
      "ended_at": null,
      "listing_status": "LISTED",
      "source": "FDR"
    }
  ],
  "next_cursor": null,
  "total": null
}
```

## Filings

### GET `/companies/{company_id}/filings`

DART 공시 목록 조회.

Query:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `year` | integer nullable | 보고 연도 |
| `period` | string nullable | `FY`, `Q1`, `Q2`, `Q3` |
| `report_code` | string nullable | DART 보고서 코드 |
| `from_date` | date nullable | 접수일 시작 |
| `to_date` | date nullable | 접수일 종료 |

Response:

```json
{
  "items": [
    {
      "id": 10,
      "rcept_no": "20260331000001",
      "report_code": "11011",
      "report_name": "사업보고서",
      "report_year": 2025,
      "report_period": "FY",
      "receipt_date": "2026-03-31",
      "filing_date": "2026-03-31",
      "is_consolidated": true,
      "source_url": "https://dart.fss.or.kr/..."
    }
  ],
  "next_cursor": null,
  "total": null
}
```

### GET `/filings/{filing_id}`

공시 상세 메타데이터 조회.

## Financials

### GET `/companies/{company_id}/financial-statements`

재무제표 헤더 목록 조회.

Query:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `year` | integer nullable | 보고 연도 |
| `period` | string nullable | `FY`, `Q1`, `Q2`, `Q3` |
| `statement_type` | string nullable | `BS`, `IS`, `CIS`, `CF` |
| `basis` | string | 기본 `CONSOLIDATED` |

Response:

```json
{
  "items": [
    {
      "id": 100,
      "report_year": 2025,
      "report_period": "FY",
      "statement_type": "BS",
      "currency": "KRW",
      "unit": 1,
      "is_consolidated": true,
      "accounting_standard": "IFRS",
      "period_start": "2025-01-01",
      "period_end": "2025-12-31"
    }
  ],
  "next_cursor": null,
  "total": null
}
```

### GET `/financial-statements/{statement_id}/items`

재무제표 항목 조회.

Query:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `standardized` | boolean | 기본 `false`. 표준 계정 매핑만 조회할지 여부 |

Response:

```json
{
  "items": [
    {
      "id": 1000,
      "standard_account": {
        "code": "total_assets",
        "name_ko": "자산총계"
      },
      "dart_account_id": "ifrs-full_Assets",
      "account_name": "자산총계",
      "account_detail": null,
      "amount": 455905980000000,
      "amount_previous": 455905980000000,
      "amount_before_previous": null,
      "ordinal": 1
    }
  ],
  "next_cursor": null,
  "total": null
}
```

### GET `/companies/{company_id}/financial-summary`

지표 계산에 필요한 표준 계정값 중심 요약 조회.

Query:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `year` | integer | 보고 연도 |
| `period` | string | 기본 `FY` |
| `basis` | string | 기본 `CONSOLIDATED` |

Response:

```json
{
  "company_id": 1,
  "report_year": 2025,
  "report_period": "FY",
  "basis": "CONSOLIDATED",
  "currency": "KRW",
  "unit": 1,
  "accounts": {
    "total_assets": 455905980000000,
    "total_liabilities": 93138800000000,
    "sales": 300870000000000,
    "operating_income": 32726000000000,
    "interest_expense": 650000000000,
    "operating_cash_flow": 68000000000000
  },
  "missing_accounts": [
    "ebitda"
  ]
}
```

## Prices

### GET `/companies/{company_id}/prices`

일별 주가 조회.

Query:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `from_date` | date | 시작일 |
| `to_date` | date | 종료일 |
| `adjusted` | boolean | 기본 `true` |

Response:

```json
{
  "items": [
    {
      "trade_date": "2026-05-29",
      "open": 72000,
      "high": 72800,
      "low": 71000,
      "close": 72500,
      "adjusted_close": 72500,
      "volume": 12000000,
      "change_rate": 0.0123,
      "market_cap": 432000000000000,
      "shares_outstanding": 5969782550
    }
  ],
  "next_cursor": null,
  "total": null
}
```

### GET `/companies/{company_id}/price-metrics`

MDD, 변동성 등 시장 지표 조회 또는 즉시 계산.

Query:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `as_of_date` | date | 분석 기준일 |
| `window_days` | integer | 기본 252 |

Response:

```json
{
  "company_id": 1,
  "as_of_date": "2026-05-29",
  "window_days": 252,
  "metrics": {
    "max_drawdown": -0.3125,
    "price_volatility": 0.2841
  },
  "raw_components": {
    "peak_date": "2025-07-10",
    "trough_date": "2026-02-03",
    "observations": 252
  }
}
```

## Events

### GET `/companies/{company_id}/events`

기업 이벤트 조회.

Query:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `event_type` | string nullable | 이벤트 타입 |
| `from_date` | date nullable | 시작일 |
| `to_date` | date nullable | 종료일 |
| `active_only` | boolean | 진행 중 이벤트만 조회 |

Response:

```json
{
  "items": [
    {
      "id": 200,
      "event_type": "AUDIT_OPINION",
      "event_subtype": "QUALIFIED",
      "event_date": "2026-03-31",
      "start_date": "2026-03-31",
      "end_date": null,
      "severity": 4,
      "title": "감사의견 한정",
      "description": "감사보고서상 한정 의견",
      "source": "DART",
      "source_id": "20260331000001",
      "source_url": "https://dart.fss.or.kr/..."
    }
  ],
  "next_cursor": null,
  "total": null
}
```

### GET `/events`

시장 전체 이벤트 조회.

Query:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `market` | string | 기본 `KOSPI` |
| `event_type` | string nullable | 이벤트 타입 |
| `from_date` | date nullable | 시작일 |
| `to_date` | date nullable | 종료일 |
| `severity_min` | integer nullable | 최소 심각도 |

## Metrics

### GET `/metrics/definitions`

지원 지표 목록 조회.

Response:

```json
{
  "items": [
    {
      "code": "altman_z_score",
      "name": "Altman Z-score",
      "category": "bankruptcy",
      "higher_is_better": true,
      "formula_version": "v1",
      "description": "기업 부실 가능성 평가 지표"
    }
  ],
  "next_cursor": null,
  "total": null
}
```

### GET `/companies/{company_id}/metrics`

기업의 분석 지표 조회.

Query:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `as_of_date` | date nullable | 없으면 최신 스냅샷 |
| `year` | integer nullable | 보고 연도 |
| `period` | string nullable | 기본 `FY` |
| `basis` | string | 기본 `CONSOLIDATED` |
| `window_days` | integer | 기본 252 |
| `metric_codes` | string nullable | 쉼표 구분. 예: `altman_z_score,piotroski_f_score` |

Response:

```json
{
  "snapshot": {
    "id": 500,
    "company_id": 1,
    "as_of_date": "2026-05-29",
    "report_year": 2025,
    "report_period": "FY",
    "statement_basis": "CONSOLIDATED",
    "price_window_days": 252,
    "data_quality_score": 0.91,
    "calculation_status": "PARTIAL",
    "created_at": "2026-06-01T16:00:00+09:00"
  },
  "metrics": [
    {
      "code": "altman_z_score",
      "name": "Altman Z-score",
      "value": 4.1234,
      "interpretation": "GOOD",
      "confidence": 0.95,
      "note": null,
      "raw_components": {
        "working_capital_to_assets": 0.21,
        "retained_earnings_to_assets": 0.62,
        "ebit_to_assets": 0.08,
        "market_value_equity_to_liabilities": 4.3,
        "sales_to_assets": 0.66
      }
    },
    {
      "code": "net_debt_to_ebitda",
      "name": "순차입금/EBITDA",
      "value": null,
      "interpretation": null,
      "confidence": 0.4,
      "note": "EBITDA 계정 매핑이 없어 계산하지 못했습니다.",
      "raw_components": {
        "missing_fields": [
          "ebitda"
        ]
      }
    }
  ]
}
```

### POST `/companies/{company_id}/metrics/recalculate`

기업 지표 재계산 작업 생성.

Request:

```json
{
  "as_of_date": "2026-05-29",
  "report_year": 2025,
  "report_period": "FY",
  "statement_basis": "CONSOLIDATED",
  "price_window_days": 252,
  "metric_codes": [
    "altman_z_score",
    "ohlson_o_score",
    "piotroski_f_score"
  ],
  "force": false
}
```

Response `202 Accepted`:

```json
{
  "job_id": "job_01HX0000000000000000000000",
  "status": "QUEUED",
  "message": "Metric recalculation queued."
}
```

### POST `/metrics/recalculate`

시장 또는 기업 목록 단위 지표 재계산 작업 생성.

Request:

```json
{
  "market": "KOSPI",
  "company_ids": null,
  "as_of_date": "2026-05-29",
  "report_year": 2025,
  "report_period": "FY",
  "statement_basis": "CONSOLIDATED",
  "price_window_days": 252,
  "force": false
}
```

## Risk

### GET `/companies/{company_id}/risk`

기업 신용/위험 평가 조회.

Query:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `as_of_date` | date nullable | 없으면 최신 평가 |
| `model_version` | string nullable | 없으면 최신 모델 |

Response:

```json
{
  "company": {
    "id": 1,
    "stock_code": "005930",
    "corp_name": "삼성전자",
    "market": "KOSPI"
  },
  "snapshot_id": 500,
  "model_version": "v1",
  "credit_grade": "A",
  "risk_score": 18.5,
  "risk_level": "LOW",
  "summary": "수익성, 현금흐름, 시장지표가 양호하며 이벤트 리스크가 낮습니다.",
  "strengths": [
    {
      "metric": "piotroski_f_score",
      "message": "재무 건전성 점수가 높습니다."
    }
  ],
  "weaknesses": [
    {
      "metric": "price_volatility",
      "message": "최근 주가 변동성이 업종 평균보다 높습니다."
    }
  ],
  "created_at": "2026-06-01T16:00:00+09:00"
}
```

### GET `/risk/rankings`

시장 전체 위험 순위 조회.

Query:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `market` | string | 기본 `KOSPI` |
| `as_of_date` | date nullable | 기준일 |
| `risk_level` | string nullable | 위험 등급 필터 |
| `sector` | string nullable | 업종 |
| `limit` | integer | 페이지 크기 |
| `cursor` | string nullable | 페이지 커서 |

Response:

```json
{
  "items": [
    {
      "rank": 1,
      "company_id": 99,
      "stock_code": "000000",
      "corp_name": "예시기업",
      "sector": "건설",
      "risk_score": 87.2,
      "risk_level": "DISTRESS",
      "credit_grade": "Watch",
      "as_of_date": "2026-05-29",
      "top_risk_factors": [
        "altman_z_score",
        "audit_opinion",
        "net_debt_to_ebitda"
      ]
    }
  ],
  "next_cursor": null,
  "total": null
}
```

### POST `/companies/{company_id}/risk/recalculate`

지표 스냅샷을 기반으로 위험 평가 재계산 작업 생성.

Request:

```json
{
  "snapshot_id": 500,
  "model_version": "v1",
  "force": false
}
```

Response `202 Accepted`:

```json
{
  "job_id": "job_01HX0000000000000000000001",
  "status": "QUEUED",
  "message": "Risk assessment recalculation queued."
}
```

## Collection jobs

수집/계산 작업은 API 응답 시간을 막지 않기 위해 DB-backed job queue로 비동기 처리한다. API 서버는 `data_collection_jobs` row만 생성하고 `202 Accepted`를 반환한다. 별도 worker가 `QUEUED` job을 가져가 OpenDartReader/FinanceDataReader를 호출하고 DB에 upsert한다.

MVP는 자동 스케줄러를 실행하지 않는다. `collection_schedules`는 권장 fetch 주기, 마지막 성공 시각, 다음 권장 실행 시각을 저장하고 수동 trigger 화면/API에서 freshness 판단에 사용한다.

공통 request field:

| 이름 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `force` | boolean | `false` | 이미 같은 범위의 성공 job/데이터가 있어도 다시 수집 |
| `enqueue_recalculation` | boolean | `true` | 수집 성공 후 metric/risk 후속 job 자동 생성 |

공통 job flow:

1. Trigger API가 `data_collection_jobs`에 `QUEUED` row를 생성한다.
2. Worker가 job을 `RUNNING`으로 변경하고 외부 provider를 호출한다.
3. Worker가 원천 테이블에 idempotent upsert한다.
4. 성공 또는 부분 성공 시 `progress`에 처리 수와 실패 항목을 저장한다.
5. `enqueue_recalculation = true`이면 metric recalculation job을 생성한다.
6. metric job 성공 후 risk assessment job을 생성한다.

중복 방지 기준:

| 데이터 | 적재 테이블 | 기준 |
| --- | --- | --- |
| 상장사 마스터 | `companies`, `company_listings` | `corp_code`, `stock_code` |
| DART 공시 목록 | `dart_filings` | `rcept_no` |
| DART 재무제표 | `financial_statements`, `financial_statement_items` | statement 유니크 키, items replace |
| 일별 주가 | `daily_prices` | `(company_id, trade_date)` |
| 이벤트 | `corporate_events` | source/source_id 우선, 없으면 회사/타입/일자 |

### POST `/jobs/collect/companies`

상장사 마스터 수집.

Request:

```json
{
  "market": "KOSPI",
  "source": "FDR",
  "enqueue_recalculation": false,
  "force": false
}
```

### POST `/jobs/collect/filings`

DART 공시 목록 수집.

Request:

```json
{
  "market": "KOSPI",
  "company_ids": null,
  "from_date": "2026-01-01",
  "to_date": "2026-06-01",
  "report_codes": [
    "11011",
    "11013",
    "11012",
    "11014"
  ],
  "enqueue_recalculation": true,
  "force": false
}
```

### POST `/jobs/collect/financials`

DART 재무제표 수집.

Request:

```json
{
  "market": "KOSPI",
  "company_ids": null,
  "year": 2025,
  "periods": [
    "FY"
  ],
  "basis": "CONSOLIDATED",
  "enqueue_recalculation": true,
  "force": false
}
```

### POST `/jobs/collect/prices`

일별 주가 수집.

Request:

```json
{
  "market": "KOSPI",
  "company_ids": null,
  "from_date": "2025-06-01",
  "to_date": "2026-06-01",
  "enqueue_recalculation": true,
  "force": false
}
```

### POST `/jobs/collect/events`

관리종목, 감사의견, 거래정지 이벤트 수집.

Request:

```json
{
  "market": "KOSPI",
  "company_ids": null,
  "from_date": "2025-06-01",
  "to_date": "2026-06-01",
  "event_types": [
    "MANAGEMENT_ISSUE",
    "AUDIT_OPINION",
    "TRADING_SUSPENSION"
  ],
  "enqueue_recalculation": true,
  "force": false
}
```

공통 job response `202 Accepted`:

```json
{
  "job_id": "job_01HX0000000000000000000002",
  "status": "QUEUED",
  "message": "Collection job queued."
}
```

### GET `/jobs/{job_id}`

작업 상태 조회.

Response:

```json
{
  "job_id": "job_01HX0000000000000000000002",
  "type": "COLLECT_FINANCIALS",
  "status": "RUNNING",
  "progress": {
    "total": 842,
    "processed": 120,
    "succeeded": 118,
    "failed": 2,
    "failed_items": [
      {
        "company_id": 10,
        "stock_code": "000000",
        "error_code": "PROVIDER_TIMEOUT",
        "message": "FinanceDataReader request timed out."
      }
    ]
  },
  "parent_job_id": null,
  "enqueue_recalculation": true,
  "started_at": "2026-06-01T16:00:00+09:00",
  "finished_at": null,
  "error": null
}
```

### GET `/jobs`

작업 목록 조회.

Query:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `type` | string nullable | 작업 타입 |
| `status` | string nullable | `QUEUED`, `RUNNING`, `SUCCESS`, `FAILED`, `CANCELED` |
| `from_date` | date nullable | 생성일 시작 |
| `to_date` | date nullable | 생성일 종료 |

### GET `/jobs/schedules`

데이터 종류별 권장 수집 주기와 freshness 상태 조회.

Response:

```json
{
  "items": [
    {
      "id": 1,
      "schedule_code": "kospi_financials_quarterly",
      "job_type": "COLLECT_FINANCIALS",
      "market": "KOSPI",
      "recommended_interval": "QUARTERLY",
      "is_active": true,
      "params": {
        "basis": "CONSOLIDATED"
      },
      "last_success_job_id": 123,
      "last_success_at": "2026-05-15T03:10:00+09:00",
      "next_recommended_at": "2026-08-15T03:10:00+09:00",
      "is_stale": false
    }
  ],
  "next_cursor": null,
  "total": null
}
```

### PATCH `/jobs/schedules/{schedule_id}`

권장 주기와 활성 여부 수정. 자동 실행은 하지 않고 freshness 판단 기준만 바꾼다.

Request:

```json
{
  "recommended_interval": "DAILY",
  "is_active": true,
  "params": {
    "basis": "CONSOLIDATED"
  },
  "next_recommended_at": "2026-06-02T03:00:00+09:00"
}
```

Response:

```json
{
  "id": 3,
  "schedule_code": "kospi_financials_quarterly",
  "job_type": "COLLECT_FINANCIALS",
  "market": "KOSPI",
  "recommended_interval": "DAILY",
  "is_active": true,
  "params": {
    "basis": "CONSOLIDATED"
  },
  "last_success_at": "2026-05-15T03:10:00+09:00",
  "next_recommended_at": "2026-06-02T03:00:00+09:00",
  "updated_at": "2026-06-01T16:10:00+09:00"
}
```

## Accounts

### GET `/accounts/standard`

표준 계정 목록 조회.

Response:

```json
{
  "items": [
    {
      "code": "total_assets",
      "name_ko": "자산총계",
      "statement_type": "BS",
      "normal_sign": 1,
      "description": "Altman, Ohlson, Zmijewski 등에서 사용하는 총자산"
    }
  ],
  "next_cursor": null,
  "total": null
}
```

### GET `/accounts/aliases`

계정 매핑 조회. 운영자/개발자용 API로 시작한다.

Query:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `account_code` | string nullable | 표준 계정 코드 |
| `source` | string nullable | DART 등 |
| `q` | string nullable | 원천 계정명 검색 |

### POST `/accounts/aliases`

계정 매핑 추가.

Request:

```json
{
  "account_code": "ebitda",
  "source": "DART",
  "dart_account_id": null,
  "raw_account_name": "EBITDA",
  "match_rule": "EXACT",
  "priority": 100,
  "is_active": true
}
```

## Dashboard convenience APIs

프론트엔드 대시보드에서 여러 API를 조합하지 않도록 제공하는 읽기 전용 요약 API다.

### GET `/dashboard/overview`

시장 전체 요약.

Query:

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `market` | string | 기본 `KOSPI` |
| `as_of_date` | date nullable | 기준일 |

Response:

```json
{
  "market": "KOSPI",
  "as_of_date": "2026-05-29",
  "company_count": 842,
  "risk_distribution": {
    "LOW": 520,
    "MEDIUM": 240,
    "HIGH": 70,
    "DISTRESS": 12
  },
  "recent_event_count": 18,
  "failed_metric_snapshot_count": 5,
  "last_collection_at": "2026-06-01T15:30:00+09:00",
  "stale_data_warnings": [
    {
      "schedule_code": "kospi_prices_daily",
      "job_type": "COLLECT_PRICES",
      "last_success_at": "2026-05-29T18:30:00+09:00",
      "next_recommended_at": "2026-05-30T18:30:00+09:00",
      "message": "일별 주가 데이터가 권장 업데이트 시각을 지났습니다."
    }
  ]
}
```

### GET `/companies/{company_id}/dashboard`

기업 상세 화면용 요약.

Response:

```json
{
  "company": {
    "id": 1,
    "stock_code": "005930",
    "corp_name": "삼성전자",
    "market": "KOSPI",
    "sector": "전기전자"
  },
  "risk": {
    "risk_score": 18.5,
    "risk_level": "LOW",
    "credit_grade": "A"
  },
  "key_metrics": {
    "altman_z_score": 4.1234,
    "ohlson_o_score": -2.4,
    "piotroski_f_score": 8,
    "interest_coverage_ratio": 50.35,
    "net_debt_to_ebitda": null,
    "max_drawdown": -0.3125,
    "price_volatility": 0.2841
  },
  "latest_events": [],
  "latest_price": {
    "trade_date": "2026-05-29",
    "close": 72500,
    "change_rate": 0.0123
  },
  "data_quality_score": 0.91
}
```

## MVP 구현 순서

1. `GET /health`
2. `GET /companies`, `GET /companies/{company_id}`, `GET /companies/by-stock/{stock_code}`
3. `POST /jobs/collect/companies`
4. `POST /jobs/collect/financials`, `GET /companies/{company_id}/financial-summary`
5. `POST /jobs/collect/prices`, `GET /companies/{company_id}/prices`
6. `GET /metrics/definitions`, `POST /companies/{company_id}/metrics/recalculate`, `GET /companies/{company_id}/metrics`
7. `GET /companies/{company_id}/risk`, `GET /risk/rankings`
8. `POST /jobs/collect/events`, `GET /companies/{company_id}/events`
9. `GET /jobs/schedules`, `PATCH /jobs/schedules/{schedule_id}`
10. `GET /dashboard/overview`, `GET /companies/{company_id}/dashboard`

## 테스트 시나리오

- 수집 trigger API 호출 시 OpenDartReader/FinanceDataReader mock이 호출되지 않고 `data_collection_jobs` row만 생성되며 `202 Accepted`를 반환한다.
- 동일한 DART 공시를 반복 수집해도 `dart_filings.rcept_no` 기준으로 중복 row가 생기지 않는다.
- 동일한 재무제표를 반복 수집하면 `financial_statements`는 upsert되고 해당 statement의 `financial_statement_items`는 replace 후 insert된다.
- 동일한 일별 주가를 반복 수집해도 `daily_prices (company_id, trade_date)` 기준으로 중복 row가 생기지 않는다.
- `source_id`가 있는 이벤트는 `(source, source_id)`, 없는 이벤트는 회사/타입/일자/source fallback 기준으로 중복 row가 생기지 않는다.
- 재무제표 fetch job이 `SUCCESS` 또는 `PARTIAL_SUCCESS`로 끝나고 `enqueue_recalculation = true`이면 metric recalculation job이 `parent_job_id`를 가진 후속 job으로 생성된다.
- metric recalculation job이 `SUCCESS`로 끝나면 risk assessment job이 후속 job으로 생성된다.
- 일부 기업 fetch 실패 시 성공 데이터는 DB에 반영되고 `progress.failed`, `progress.failed_items`, `error`에 실패 내역이 저장된다.
- `GET /jobs/schedules`는 `next_recommended_at < now()`인 active schedule에 `is_stale = true`를 반환한다.
- `GET /dashboard/overview`는 stale schedule이 있을 때 `stale_data_warnings`를 반환한다.
- 모든 조회 API는 provider client dependency 없이 DB repository/mock만으로 응답한다.

## 보류 사항

- 인증/인가 방식: 로컬 분석 도구라면 API key부터 시작하고, 팀 단위 서비스라면 OAuth/OIDC를 붙인다.
- OpenDartReader 호출 제한과 캐시 정책.
- FinanceDataReader 데이터 정합성 검증과 수정주가 기준.
- 이벤트 원천의 확정 범위. 감사의견은 DART 기반, 거래정지/관리종목은 KRX 기반 수집을 우선 검토한다.
