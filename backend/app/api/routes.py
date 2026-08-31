"""Declared FastAPI endpoints used exclusively over HTTP by the dashboard."""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select
from ..db import AssessmentRecord, RefineryRecord, RouteRecord, SessionLocal
from ..graph.builder import build_graph
from ..pipeline.orchestrator import run_cycle
from ..schemas import IngestRunStats, RefineryExposure, RiskAssessment, RouteRisk, Signal
router=APIRouter(prefix="/api")
FIXTURE=Path(__file__).parents[2]/"data"/"fixtures"/"hormuz_june2025.json"
@router.get("/health",response_model=dict)
def health() -> dict:
    """Expose local health and data state for the dashboard header."""
    with SessionLocal() as db: count=db.scalar(select(func.count()).select_from(AssessmentRecord)) or 0
    return {"sources":{"rss":"available","gdelt":"unavailable_optional","prices":"on_demand","ais":"not_implemented_phase_2"},"extractor":"configured at cycle startup","db_counts":{"assessments":count},"version":"0.1.0","last_run_time":None}
@router.post("/ingest/run",response_model=IngestRunStats)
def ingest(window_hours:int=24)->IngestRunStats: return run_cycle(window_hours)
@router.get("/signals",response_model=list[RiskAssessment])
def signals(limit:int=100,band:str|None=None,route_id:str|None=None)->list[RiskAssessment]:
    with SessionLocal() as db: records=db.scalars(select(AssessmentRecord).where(AssessmentRecord.namespace=="live").order_by(AssessmentRecord.id.desc()).limit(limit)).all()
    values=[RiskAssessment.model_validate(record.assessment) for record in records]
    if band: values=[value for value in values if value.band==band]
    return values
@router.get("/risk/routes",response_model=list[RouteRisk])
def routes()->list[RouteRisk]:
    with SessionLocal() as db: return [RouteRisk.model_validate(item.payload) for item in db.scalars(select(RouteRecord).where(RouteRecord.namespace=="live")).all()]
@router.get("/risk/refineries",response_model=list[RefineryExposure])
def refineries()->list[RefineryExposure]:
    with SessionLocal() as db: return [RefineryExposure.model_validate(item.payload) for item in db.scalars(select(RefineryRecord).where(RefineryRecord.namespace=="live")).all()]
@router.get("/graph",response_model=dict)
def graph()->dict:
    graph=build_graph(); return {"nodes":[{"id":node,**attrs} for node,attrs in graph.nodes(data=True)],"edges":[{"source":a,"target":b} for a,b in graph.edges()]}
@router.get("/scenarios",response_model=list[str])
def scenarios()->list[str]: return ["hormuz_june2025"] if FIXTURE.exists() else []
@router.post("/replay/{scenario_id}",response_model=IngestRunStats)
def replay(scenario_id:str)->IngestRunStats:
    if scenario_id!="hormuz_june2025" or not FIXTURE.exists(): raise HTTPException(404,"Scenario not found")
    payload=json.loads(FIXTURE.read_text()); signals=[Signal.model_validate(value) for value in payload["signals"]]
    return run_cycle(fixture_signals=signals,reference_time=Signal.model_validate(payload["signals"][-1]).published_at,namespace=f"scenario:{scenario_id}",sources=[])
