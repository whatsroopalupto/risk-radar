"""Declared FastAPI endpoints used exclusively over HTTP by the dashboard."""
import json
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from ..db import AssessmentRecord, RefineryRecord, RouteRecord, RunLogRecord, SessionLocal, RiskSnapshot, AlertRecord, DisplayState, display_namespace
from ..graph.builder import build_graph, load_seed
from ..pipeline.orchestrator import extractor_status, run_cycle
from ..pipeline.trends import route_score_timeseries
from ..pipeline.scorer import band_for_score
from ..schemas import IngestRunStats, RefineryExposure, RiskAssessment, RouteRisk, Signal
router=APIRouter(prefix="/api")
FIXTURES_DIR=Path(__file__).parents[2]/"data"/"fixtures"
NOT_YET_RUN={"rss":{"status":"not_yet_run","fetched":0},"gdelt":{"status":"not_yet_run","fetched":0},"prices":{"status":"not_yet_run","fetched":0}}
@router.get("/health",response_model=dict)
def health() -> dict:
    """Expose real per-source status, active extractor and DB state for the dashboard header."""
    with SessionLocal() as db:
        namespace=display_namespace(db)
        count=db.scalar(select(func.count()).select_from(AssessmentRecord).where(AssessmentRecord.namespace==namespace)) or 0
        last_run=db.scalars(select(RunLogRecord).where(RunLogRecord.namespace==namespace).order_by(RunLogRecord.finished_at.desc())).first()
        records=db.scalars(select(AssessmentRecord).where(AssessmentRecord.namespace==namespace)).all()
        saved_route=db.scalars(select(RouteRecord).where(RouteRecord.namespace==namespace)).first()
        risk_computed_at=saved_route.payload.get("computed_at") if saved_route else None
    if last_run:
        sources={name:{"status":item.get("status"),"fetched":item.get("fetched",0),"error":item.get("error")} for name,item in last_run.stats.get("per_source",{}).items()}
        for name in ("rss","gdelt","prices"): sources.setdefault(name,{"status":"not_polled_last_run","fetched":0,"error":None})
        last_run_time=last_run.finished_at
    else:
        sources=dict(NOT_YET_RUN); last_run_time=None
    from ..connectors.ais import collector_health
    sources["ais"]=collector_health()
    extractor_mix:dict[str,int]={}
    for record in records:
        used=(record.assessment or {}).get("extraction",{}).get("extractor","unknown")
        extractor_mix[used]=extractor_mix.get(used,0)+1
    return {"sources":sources,"extractor":extractor_status(),"extractor_mix":extractor_mix,"db_counts":{"assessments":count},"version":"0.3.0","last_run_time":last_run_time,"risk_computed_at":risk_computed_at,"dataset":namespace,"provenance":"recorded_run" if last_run else "legacy_snapshot_unverified", "latest_run": last_run.stats if last_run else None}
@router.post("/ingest/run",response_model=IngestRunStats)
def ingest(window_hours:int=Query(24,ge=1,le=168))->IngestRunStats: return run_cycle(window_hours)
@router.get("/ingest/history",response_model=list[IngestRunStats])
def ingest_history(limit:int=Query(20,ge=1,le=200))->list[IngestRunStats]:
    with SessionLocal() as db: records=db.scalars(select(RunLogRecord).order_by(RunLogRecord.finished_at.desc()).limit(limit)).all()
    return [IngestRunStats.model_validate(record.stats) for record in records]
@router.get("/signals",response_model=list[RiskAssessment])
def signals(limit:int=Query(100,ge=1,le=2000),band:str|None=None,route_id:str|None=None)->list[RiskAssessment]:
    with SessionLocal() as db:
        namespace=display_namespace(db)
        records=db.scalars(select(AssessmentRecord).where(AssessmentRecord.namespace==namespace).order_by(AssessmentRecord.published_at.desc(), AssessmentRecord.signal_id.asc())).all()
        route=db.scalars(select(RouteRecord).where(RouteRecord.namespace==namespace,RouteRecord.route_id==route_id)).first() if route_id else None
    values=[]
    for record in records:
        data=dict(record.assessment)
        synthetic=bool((record.signal or {}).get("raw",{}).get("_fixture"))
        data["title"]=record.title; data["source_name"]=f"Synthetic fixture ({record.source_name} weight)" if synthetic else record.source_name; data["published_at"]=record.published_at
        if record.signal and isinstance(record.signal,dict): data["url"]=None if synthetic else record.signal.get("url")
        values.append(RiskAssessment.model_validate(data))
    if band: values=[value for value in values if value.band==band]
    if route_id: values=[value for value in values if route and value.signal_id in route.payload.get("contributing_signal_ids",[])]
    return values[:limit]
@router.get("/risk/routes",response_model=list[RouteRisk])
def routes()->list[RouteRisk]:
    with SessionLocal() as db: return [RouteRisk.model_validate(item.payload) for item in db.scalars(select(RouteRecord).where(RouteRecord.namespace==display_namespace(db))).all()]
@router.get("/risk/routes/timeseries",response_model=list[dict])
def routes_timeseries()->list[dict]:
    """Day-bucketed noisy-OR per route from whatever is currently stored, so a multi-day replay or wide window renders as a trend."""
    with SessionLocal() as db:
        namespace=display_namespace(db)
        snapshots=db.scalars(select(RiskSnapshot).where(RiskSnapshot.namespace==namespace).order_by(RiskSnapshot.computed_at, RiskSnapshot.id)).all()
        records=db.scalars(select(AssessmentRecord).where(AssessmentRecord.namespace==namespace)).all()
    if namespace=="live" and snapshots:
        series={}
        # Last observed news score per UTC day; never backdate today's score.
        for snapshot in snapshots:
            day=snapshot.computed_at.date().isoformat()
            for route in snapshot.payload["routes"]:
                item=series.setdefault(route["route_id"],{"route_id":route["route_id"],"name":route["name"],"days":{}})
                item["days"][day]={"date":day,"news_score":round(route["news_score"]*100,2),"band":band_for_score(route["news_score"]*100),"signal_count":len(route["contributing_signal_ids"])}
        return [{"route_id":s["route_id"],"name":s["name"],"points":list(s["days"].values())} for s in series.values()]
    assessments=[]
    for record in records:
        data=dict(record.assessment); data["published_at"]=record.published_at
        assessments.append(RiskAssessment.model_validate(data))
    return route_score_timeseries(assessments,load_seed())
@router.get("/risk/refineries",response_model=list[RefineryExposure])
def refineries()->list[RefineryExposure]:
    with SessionLocal() as db: return [RefineryExposure.model_validate(item.payload) for item in db.scalars(select(RefineryRecord).where(RefineryRecord.namespace==display_namespace(db))).all()]
@router.get("/graph",response_model=dict)
def graph()->dict:
    graph=build_graph(); return {"nodes":[{"id":node,**attrs} for node,attrs in graph.nodes(data=True)],"edges":[{"source":a,"target":b,**attrs} for a,b,attrs in graph.edges(data=True)],"provenance":{"supplier_routes":"Possible geographic paths, not observed shipments","refinery_dependencies":"Illustrative assumptions; national PPAC/EIA totals cannot establish these shares"}}
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
    if scenario_id not in {item["id"] for item in scenarios()}: raise HTTPException(404,"Scenario not found")
    fixture_path=FIXTURES_DIR/f"{scenario_id}.json"
    if not fixture_path.exists(): raise HTTPException(404,"Scenario not found")
    payload=json.loads(fixture_path.read_text(encoding="utf-8")); signals=[Signal.model_validate(value).model_copy(update={"url":None}) for value in payload["signals"]]
    ref_time_str = payload.get("reference_time")
    ref_time = datetime.fromisoformat(ref_time_str) if ref_time_str else Signal.model_validate(payload["signals"][-1]).published_at
    return run_cycle(fixture_signals=signals,reference_time=ref_time,namespace=f"replay:{scenario_id}",sources=[],scenario_id=scenario_id)

@router.get("/risk/history")
def risk_history(limit:int=Query(100,ge=1,le=1000)):
    with SessionLocal() as db:
        records=db.scalars(select(RiskSnapshot).where(RiskSnapshot.namespace==display_namespace(db)).order_by(RiskSnapshot.id.desc()).limit(limit)).all()
        return [{"run_id":r.run_id,"namespace":r.namespace,"computed_at":r.computed_at,"routes":r.payload["routes"]} for r in records]

@router.get("/ais/activity")
def ais_activity():
    from ..connectors.ais import activity_summary
    return activity_summary()

@router.get("/alerts")
def alerts(limit:int=Query(50,ge=1,le=200)):
    with SessionLocal() as db:
        records=db.scalars(select(AlertRecord).where(AlertRecord.namespace==display_namespace(db)).order_by(AlertRecord.id.desc()).limit(limit)).all()
        return [{"id":r.id,"dataset":r.namespace,"route_id":r.route_id,"run_id":r.run_id,"occurred_at":r.occurred_at,**r.payload} for r in records]

@router.post("/display/live")
def show_live():
    with SessionLocal() as db:
        db.merge(DisplayState(id=1,namespace="live"))
        db.commit()
    return {"dataset":"live"}

class EvidenceQuestion(BaseModel):
    question: str = Field(min_length=3,max_length=500)
    route_id: str | None = None
    generate: bool = True

@router.post("/evidence/ask")
def evidence_ask(request: EvidenceQuestion):
    from ..evidence import answer_question
    with SessionLocal() as db:
        namespace=display_namespace(db)
    try:
        return answer_question(request.question,namespace,request.route_id,request.generate)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc

@router.get("/trade")
def trade_data():
    from ..connectors.trade import trade_summary
    return trade_summary()

@router.post("/trade/refresh")
def trade_refresh():
    from ..connectors.trade import refresh_trade
    from ..pipeline.locking import exclusive_job
    with exclusive_job("trade"):
        return refresh_trade()

@router.get("/validation")
def validation_reports():
    directory=Path(__file__).resolve().parents[3]/"output"/"evaluation"
    reports=[]
    for filename in ("pilot_heuristic.json","pilot_gemini.json"):
        path=directory/filename
        if path.exists():
            reports.append(json.loads(path.read_text(encoding="utf-8")))
    return {"status":"provisional_pilot" if reports else "not_evaluated","reports":reports,
        "notice":"Small, provisionally source-reviewed paraphrase corpus. These are not final held-out accuracy or real-time lead-time results."}

