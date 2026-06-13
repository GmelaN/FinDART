# FinDART

KOSPI 기업 대상 신용도 및 재무 분석 데이터를 제공하는 FastAPI 서비스입니다. 데이터 수집과 업로드는 이 서버 밖의 별도 파이프라인이 담당하며, 이 애플리케이션은 PostgreSQL에 적재된 데이터를 읽어서 제공합니다.

## Environment

`.env`에는 DB 접속 정보만 필요합니다.

```env
POSTGRE_USERNAME=
POSTGRE_PASSWORD=
POSTGRE_HOST=
POSTGRE_PORT=
POSTGRE_DB=findart
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

## MVP APIs

- `GET /api/v1/health`
- `GET /api/v1/health/dependencies`
- `GET /api/v1/companies`
- `GET /api/v1/companies/{company_id}`
- `GET /api/v1/companies/by-stock/{stock_code}`
- `POST /api/v1/ingest/companies`
- `POST /api/v1/ingest/company-listings`
- `POST /api/v1/ingest/dart-filings`
- `POST /api/v1/ingest/financial-statement-items`
