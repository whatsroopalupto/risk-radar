"""Frozen Pydantic contracts shared by all application layers."""
from datetime import datetime
from typing import Annotated, Any, Literal
from pydantic import BaseModel, Field, field_validator

Chokepoint = Literal["hormuz", "bab_el_mandeb", "suez", "malacca", "none"]
EventType = Literal["blockade_or_closure", "attack_on_vessel", "military_strike", "port_or_terminal_disruption", "sanctions", "naval_buildup", "diplomatic_escalation", "policy_change", "other"]
RiskBand = Literal["low", "medium", "high"]

class TimeAwareModel(BaseModel):
    @field_validator("published_at", "fetched_at", "started_at", "finished_at", "computed_at", check_fields=False)
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")
        return value

class Signal(TimeAwareModel):
    signal_id: str
    source_type: Literal["news", "price", "vessel"]
    source_name: str
    title: str
    body: str | None = None
    url: str | None = None
    published_at: datetime
    fetched_at: datetime
    raw: dict[str, Any] = Field(default_factory=dict)

class RiskExtraction(BaseModel):
    is_relevant: bool
    event_type: EventType
    severity: Annotated[float, Field(ge=0, le=1)]
    affected_chokepoints: list[Chokepoint]
    affected_countries: list[str]
    is_speculative: bool
    confidence: Annotated[float, Field(ge=0, le=1)]
    evidence: Annotated[str, Field(max_length=200)]
    extractor: str

class RiskAssessment(BaseModel):
    signal_id: str
    extraction: RiskExtraction
    credibility_tier: int
    credibility_weight: float
    recency_weight: float
    type_weight: float
    speculative_weight: float
    component_scores: dict[str, float]
    final_score: Annotated[float, Field(ge=0, le=1)]
    band: RiskBand
    title: str | None = None
    source_name: str | None = None
    published_at: datetime | None = None
    url: str | None = None

class RouteRisk(TimeAwareModel):
    route_id: str
    name: str
    chokepoints: list[Chokepoint]
    news_score: float
    market_score: float
    composite_score: Annotated[float, Field(ge=0, le=100)]
    band: RiskBand
    contributing_signal_ids: list[str]
    computed_at: datetime

class RouteContribution(BaseModel):
    route_id: str
    dependency_share: float
    route_score: float

class RefineryExposure(BaseModel):
    refinery_id: str
    name: str
    operator: str
    port_id: str
    exposure_score: Annotated[float, Field(ge=0, le=100)]
    band: RiskBand
    contributions: list[RouteContribution]

class SourceRun(BaseModel):
    status: str
    fetched: int = 0
    error: str | None = None

class IngestRunStats(TimeAwareModel):
    run_id: str
    started_at: datetime
    finished_at: datetime
    per_source: dict[str, SourceRun]
    deduped: int
    filtered_out: int
    extracted: int
    extractor_used: str
    errors: list[str] = Field(default_factory=list)
    scenario_id: str | None = None
