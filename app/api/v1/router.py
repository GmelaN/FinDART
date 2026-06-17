from fastapi import APIRouter

from app.api.v1 import companies, health, ingest, today

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(today.router, prefix="/today", tags=["today"])

