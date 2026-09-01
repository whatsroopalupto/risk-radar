"""SQLite persistence models and session factory for local Phase 1 runs."""
from datetime import datetime, timezone
from sqlalchemy import JSON, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import settings

class Base(DeclarativeBase): pass

class AssessmentRecord(Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    namespace: Mapped[str] = mapped_column(String(80), default="live", index=True)
    signal_id: Mapped[str] = mapped_column(String(16), index=True)
    title: Mapped[str] = mapped_column(Text)
    source_name: Mapped[str] = mapped_column(String(255))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    signal: Mapped[dict] = mapped_column(JSON)
    assessment: Mapped[dict] = mapped_column(JSON)

class RouteRecord(Base):
    __tablename__ = "route_risks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    namespace: Mapped[str] = mapped_column(String(80), default="live", index=True)
    route_id: Mapped[str] = mapped_column(String(80), index=True)
    payload: Mapped[dict] = mapped_column(JSON)

class RefineryRecord(Base):
    __tablename__ = "refinery_exposures"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    namespace: Mapped[str] = mapped_column(String(80), default="live", index=True)
    refinery_id: Mapped[str] = mapped_column(String(80), index=True)
    payload: Mapped[dict] = mapped_column(JSON)

class RunLogRecord(Base):
    """Append-only ingestion run history; never wiped, unlike the per-namespace tables above."""
    __tablename__ = "run_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    namespace: Mapped[str] = mapped_column(String(80), index=True)
    run_id: Mapped[str] = mapped_column(String(40))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    stats: Mapped[dict] = mapped_column(JSON)

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def init_db() -> None:
    """Create Phase 1 tables without migration machinery."""
    Base.metadata.create_all(engine)

def utcnow() -> datetime:
    """Provide a single timezone-safe current time for orchestration."""
    return datetime.now(timezone.utc)
