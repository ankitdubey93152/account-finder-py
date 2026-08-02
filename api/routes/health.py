import time
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database.session import get_db

router = APIRouter(tags=["Health"])

START_TIME = time.time()

class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    uptime_seconds: float
    database: str

@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unreachable"

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        app_name="OSINT Digital Footprint Analyzer",
        environment="development",
        uptime_seconds=round(time.time() - START_TIME, 2),
        database=db_status,
    )
