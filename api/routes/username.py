from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ScanHistory, ScanResult
from database.session import get_db
from modules.username_search.models import ScanSummary
from modules.username_search.scanner import scan_username

router = APIRouter(prefix="/scan", tags=["Username scans"])


class UsernameScanRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    concurrency: int = Field(default=15, ge=1, le=20)


@router.post("/username", response_model=ScanSummary)
async def username_scan(request: UsernameScanRequest, db: AsyncSession = Depends(get_db)) -> ScanSummary:
    """Check enabled public-profile endpoints and retain the raw public results."""
    summary = await scan_username(request.username, request.concurrency)
    history = ScanHistory(scan_type="username", target_query=request.username)
    db.add(history)
    await db.flush()
    for result in summary.results:
        db.add(ScanResult(
            scan_id=history.id,
            platform_or_provider=result.platform,
            target_url=result.url,
            exists=result.exists,
            confidence=result.confidence,
            details={
                "bio": result.bio,
                "avatar_url": result.avatar_url,
                "follower_count": result.follower_count,
                "location": result.location,
                "website": result.website,
                "created_at": result.created_at.isoformat() if result.created_at else None,
                "response_time_ms": result.response_time_ms,
            },
            error=result.error,
            checked_at=result.checked_at.replace(tzinfo=None),
        ))
    await db.flush()
    return summary
