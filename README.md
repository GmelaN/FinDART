# FinDART

KOSPI 기업 대상 신용도 및 재무 분석 플랫폼입니다. FastAPI, PostgreSQL, SQLAlchemy, Alembic 기반으로 시작합니다.

## Environment

`.env`에 아래 값이 필요합니다.

```env
POSTGRE_USERNAME=
POSTGRE_PASSWORD=
POSTGRE_HOST=
POSTGRE_PORT=
POSTGRE_DB=findart
OPENDART_API_KEY=
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

## Worker

수집 API는 job row만 생성합니다. 실제 fetch와 DB 적재는 worker가 처리합니다.

```powershell
python -m app.worker run-once
python -m app.worker run --sleep 5
```

현재 구현된 worker job:

- `COLLECT_COMPANIES`: FinanceDataReader `StockListing("KOSPI")`를 호출해 `companies`, `company_listings`에 upsert

## Docker image CI

GitHub Actions가 `main`/`master` push, `v*` tag push, 수동 실행에서 Docker 이미지를 빌드합니다.

- Registry: GitHub Container Registry
- Image: `ghcr.io/<owner>/<repo>`
- Tags: branch name, git tag, `sha-<commit>`, default branch의 `latest`
- Pull request에서는 push 없이 build만 검증합니다.

GitHub repository의 Actions permissions에서 `Read and write permissions` 또는 workflow의 `packages: write` 권한이 허용되어 있어야 GHCR push가 됩니다.

## MVP APIs

- `GET /api/v1/health`
- `GET /api/v1/health/dependencies`
- `GET /api/v1/companies`
- `GET /api/v1/companies/{company_id}`
- `GET /api/v1/companies/by-stock/{stock_code}`
- `POST /api/v1/jobs/collect/companies`
- `POST /api/v1/jobs/collect/filings`
- `POST /api/v1/jobs/collect/financials`
- `POST /api/v1/jobs/collect/prices`
- `POST /api/v1/jobs/collect/events`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs/schedules`
- `PATCH /api/v1/jobs/schedules/{schedule_id}`
