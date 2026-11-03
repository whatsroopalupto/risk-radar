"""SQLite persistence models and session factory for local Phase 1 runs."""
from datetime import datetime, timezone
from sqlalchemy import JSON, DateTime, Float, Integer, String, Text, UniqueConstraint, create_engine
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

class DisplayState(Base):
    __tablename__ = "display_state"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    namespace: Mapped[str] = mapped_column(String(80), default="live")

class RiskSnapshot(Base):
    """Append-only evidence and scores, isolated from the current display tables."""
    __tablename__ = "risk_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String(40), unique=True)
    namespace: Mapped[str] = mapped_column(String(80), index=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payload: Mapped[dict] = mapped_column(JSON)

class VesselObservation(Base):
    __tablename__ = "vessel_observations"
    __table_args__ = (UniqueConstraint("mmsi", "observed_at", "latitude", "longitude"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mmsi: Mapped[str] = mapped_column(String(9), index=True)
    corridor: Mapped[str] = mapped_column(String(40), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    speed_knots: Mapped[float | None] = mapped_column(Float, nullable=True)
    ship_name: Mapped[str] = mapped_column(String(255), default="")

class CollectorState(Base):
    __tablename__ = "collector_state"
    name: Mapped[str] = mapped_column(String(40), primary_key=True)
    status: Mapped[str] = mapped_column(String(40))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    detail: Mapped[str] = mapped_column(String(255), default="")

class AlertRecord(Base):
    __tablename__ = "risk_alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    namespace: Mapped[str] = mapped_column(String(80), index=True)
    route_id: Mapped[str] = mapped_column(String(80))
    run_id: Mapped[str] = mapped_column(String(40))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payload: Mapped[dict] = mapped_column(JSON)

def display_namespace(db) -> str:
    state = db.get(DisplayState, 1)
    return state.namespace if state else "live"

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def init_db() -> None:
    """Create Phase 1 tables without migration machinery."""
    Base.metadata.create_all(engine)

def utcnow() -> datetime:
    """Provide a single timezone-safe current time for orchestration."""
    return datetime.now(timezone.utc)
