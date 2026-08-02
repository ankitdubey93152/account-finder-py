import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Integer, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class ScanHistory(Base):
    __tablename__ = "scan_histories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # username, phone, email
    target_query: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False)
    
    results: Mapped[List["ScanResult"]] = relationship("ScanResult", back_populates="scan", cascade="all, delete-orphan")

class ScanResult(Base):
    __tablename__ = "scan_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[int] = mapped_column(Integer, ForeignKey("scan_histories.id", ondelete="CASCADE"), nullable=False)
    platform_or_provider: Mapped[str] = mapped_column(String(100), nullable=False)
    target_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    exists: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    confidence: Mapped[str] = mapped_column(String(20), default="high", nullable=False)
    
    # Metadata fields stored as JSON dictionary or dedicated columns
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )

    scan: Mapped["ScanHistory"] = relationship("ScanHistory", back_populates="results")
