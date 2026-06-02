from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0", time=datetime.now(ZoneInfo("Asia/Seoul")))


@router.get("/health/dependencies")
def health_dependencies(db: Session = Depends(get_db)) -> dict:
    db.execute(text("select 1"))
    return {
        "status": "ok",
        "dependencies": {
            "database": "ok",
            "dart": "configured",
            "finance_datareader": "not_checked",
        },
    }

