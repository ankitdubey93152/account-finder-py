from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class PlatformResult(BaseModel):
    platform: str
    url: str
    exists: bool | None
    confidence: Literal["high", "low"]
    bio: str | None = None
    avatar_url: str | None = None
    follower_count: int | None = None
    location: str | None = None
    website: str | None = None
    created_at: datetime | None = None
    error: str | None = None
    response_time_ms: int | None = None
    checked_at: datetime


class ScanSummary(BaseModel):
    username: str
    total_platforms: int
    found: int
    not_found: int
    errored: int
    duration_ms: int
    results: list[PlatformResult]
