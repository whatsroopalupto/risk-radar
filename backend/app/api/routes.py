"""Declared FastAPI endpoints used exclusively over HTTP by the dashboard."""
import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select
from ..db import AssessmentRecord, RefineryRecord, RouteRecord, RunLogRecord, SessionLocal
from ..graph.builder import build_graph, load_seed
from ..pipeline.orchestrator import extractor_status, run_cycle
from ..pipeline.trends import route_score_timeseries
from ..schemas import IngestRunStats, RefineryExposure, RiskAssessment, RouteRisk, Signal
router=APIRouter(prefix="/api")
FIXTURES_DIR=Path(__file__).parents[2]/"data"/"fixtures"
NOT_YET_RUN={"rss":{"status":"not_yet_run","fetched":0},"gdelt":{"status":"not_yet_run","fetched":0},"prices":{"status":"not_yet_run","fetched":0}}
@router.get("/health",response_model=dict)
def health() -> dict:
    """Expose real per-source status, active extractor and DB state for the dashboard header."""
    with SessionLocal() as db:
        count=db.scalar(select(func.count()).select_from(AssessmentRecord)) or 0
        last_run=db.scalars(select(RunLogRecord).where(RunLogRecord.namespace=="live").order_by(RunLogRecord.finished_at.desc())).first()
        records=db.scalars(select(AssessmentRecord).where(AssessmentRecord.namespace=="live")).all()
    if last_run:
        sources={name:{"status":item.get("status"),"fetched":item.get("fetched",0),"error":item.get("error")} for name,item in last_run.stats.get("per_source",{}).items()}
        for name in ("rss","gdelt","prices"): sources.setdefault(name,{"status":"not_polled_last_run","fetched":0,"error":None})
        last_run_time=last_run.finished_at
    else:
        sources=dict(NOT_YET_RUN); last_run_time=None
    sources.setdefault("ais",{"status":"not_implemented_phase_2","fetched":0})
    extractor_mix:dict[str,int]={}
    for record in records:
        used=(record.assessment or {}).get("extraction",{}).get("extractor","unknown")
        extractor_mix[used]=extractor_mix.get(used,0)+1
    return {"sources":sources,"extractor":extractor_status(),"extractor_mix":extractor_mix,"db_counts":{"assessments":count},"version":"0.1.0","last_run_time":last_run_time}
@router.post("/ingest/run",response_model=IngestRunStats)
def ingest(window_hours:int=24)->IngestRunStats: return run_cycle(window_hours)
@router.get("/ingest/history",response_model=list[IngestRunStats])
def ingest_history(limit:int=20)->list[IngestRunStats]:
    with SessionLocal() as db: records=db.scalars(select(RunLogRecord).order_by(RunLogRecord.finished_at.desc()).limit(limit)).all()
    return [IngestRunStats.model_validate(record.stats) for record in records]
@router.get("/signals",response_model=list[RiskAssessment])
def signals(limit:int=100,band:str|None=None,route_id:str|None=None)->list[RiskAssessment]:
    with SessionLocal() as db: records=db.scalars(select(AssessmentRecord).where(AssessmentRecord.namespace=="live").order_by(AssessmentRecord.published_at.desc(), AssessmentRecord.signal_id.asc()).limit(limit)).all()
    values=[]
    for record in records:
        data=dict(record.assessment)
        data["title"]=record.title; data["source_name"]=record.source_name; data["published_at"]=record.published_at
        if record.signal and isinstance(record.signal,dict): data["url"]=record.signal.get("url")
        values.append(RiskAssessment.model_validate(data))
    if band: values=[value for value in values if value.band==band]
    return values
@router.get("/risk/routes",response_model=list[RouteRisk])
def routes()->list[RouteRisk]:
    with SessionLocal() as db: return [RouteRisk.model_validate(item.payload) for item in db.scalars(select(RouteRecord).where(RouteRecord.namespace=="live")).all()]
@router.get("/risk/routes/timeseries",response_model=list[dict])
def routes_timeseries()->list[dict]:
    """Day-bucketed noisy-OR per route from whatever is currently stored, so a multi-day replay or wide window renders as a trend."""
    with SessionLocal() as db: records=db.scalars(select(AssessmentRecord).where(AssessmentRecord.namespace=="live")).all()
    assessments=[]
    for record in records:
        data=dict(record.assessment); data["published_at"]=record.published_at
        assessments.append(RiskAssessment.model_validate(data))
    return route_score_timeseries(assessments,load_seed())
@router.get("/risk/refineries",response_model=list[RefineryExposure])
def refineries()->list[RefineryExposure]:
    with SessionLocal() as db: return [RefineryExposure.model_validate(item.payload) for item in db.scalars(select(RefineryRecord).where(RefineryRecord.namespace=="live")).all()]
@router.get("/graph",response_model=dict)
def graph()->dict:
    graph=build_graph(); return {"nodes":[{"id":node,**attrs} for node,attrs in graph.nodes(data=True)],"edges":[{"source":a,"target":b} for a,b in graph.edges()]}
@router.get("/scenarios",response_model=list[dict])
def scenarios()->list[dict]:
    """Discover every saved fixture, not just one hardcoded scenario, so adding a fixture file is enough to expose it."""
    if not FIXTURES_DIR.exists(): return []
    results=[]
    for path in sorted(FIXTURES_DIR.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        results.append({"id":path.stem,"label":payload.get("scenario_label",path.stem),"description":payload.get("scenario_description","")})
    return results
@router.post("/replay/{scenario_id}",response_model=IngestRunStats)
def replay(scenario_id:str)->IngestRunStats:
    fixture_path=FIXTURES_DIR/f"{scenario_id}.json"
    if not fixture_path.exists(): raise HTTPException(404,"Scenario not found")
    payload=json.loads(fixture_path.read_text(encoding="utf-8")); signals=[Signal.model_validate(value) for value in payload["signals"]]
    ref_time_str = payload.get("reference_time")
    ref_time = datetime.fromisoformat(ref_time_str) if ref_time_str else Signal.model_validate(payload["signals"][-1]).published_at
    return run_cycle(fixture_signals=signals,reference_time=ref_time,namespace="live",sources=[],scenario_id=scenario_id)

