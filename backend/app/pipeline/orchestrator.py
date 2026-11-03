"""One complete, independently degrading ingestion cycle."""
import logging, uuid
from functools import wraps
from datetime import datetime, timezone
from sqlalchemy import delete, select
from ..connectors.gdelt import GDELTConnector
from ..connectors.prices import PriceConnector
from ..connectors.rss import RSSConnector
from ..db import AssessmentRecord, RefineryRecord, RouteRecord, RunLogRecord, SessionLocal, DisplayState, RiskSnapshot, ArticleRecord
from ..graph.builder import load_seed
from ..graph.propagate import propagate
from ..schemas import IngestRunStats, RouteRisk, Signal, SourceRun
from .normalize import dedupe
from .relevance import is_relevant
from .scorer import band_for_score, composite_score, market_score, noisy_or, score_extraction
from .extractors.gemini import GeminiExtractor
from .extractors.heuristic import HeuristicExtractor
from ..config import settings
from .alerts import add_alerts
LOGGER=logging.getLogger(__name__)

def serialized_ingestion(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        from .locking import exclusive_job
        with exclusive_job("ingestion"):
            return function(*args, **kwargs)
    return wrapped
def choose_extractor():
    """Select the explicit fallback path; never relabel heuristics as LLM output."""
    if settings.extractor == "gemini" or (settings.extractor == "auto" and settings.gemini_api_key): return GeminiExtractor()
    return HeuristicExtractor()
def extractor_status() -> dict:
    """Report which extractor is active and why, as a config check, not a network probe."""
    if settings.extractor == "gemini" or (settings.extractor == "auto" and settings.gemini_api_key):
        reason = "EXTRACTOR=gemini forced" if settings.extractor == "gemini" else "GEMINI_API_KEY present"
        return {"active": settings.gemini_model, "reason": reason}
    reason = "EXTRACTOR=heuristic forced" if settings.extractor == "heuristic" else "no GEMINI_API_KEY configured"
    return {"active": "heuristic-v1", "reason": reason}
@serialized_ingestion
def run_cycle(window_hours: int = 24, sources: list[str] | None = None, fixture_signals: list[Signal] | None = None, reference_time: datetime | None = None, namespace: str = "live", scenario_id: str | None = None, update_display: bool = True) -> IngestRunStats:
    """Run fetch through propagation while isolating failures to each source."""
    started=datetime.now(timezone.utc); reference_time=reference_time or started; selected=["rss","gdelt","prices"] if sources is None else sources; connectors={"rss":RSSConnector(),"gdelt":GDELTConnector()}; per_source={}; signals=list(fixture_signals or [])
    for name in selected:
        if name == "prices": continue
        connector=connectors.get(name)
        if not connector: continue
        try:
            values=connector.fetch(window_hours); signals.extend(values); per_source[name]=SourceRun(status=getattr(connector,"last_status","ok"),fetched=len(values))
        except (OSError, ValueError, RuntimeError) as exc:
            per_source[name]=SourceRun(status="unavailable",error=str(exc)); LOGGER.warning("%s unavailable: %s",name,exc)
    if fixture_signals is not None: per_source["fixture"]=SourceRun(status="ok",fetched=len(fixture_signals))
    news_sources=[per_source[name] for name in ("rss","gdelt") if name in per_source]
    if fixture_signals is None and news_sources and all(source.status=="unavailable" for source in news_sources):
        stats=IngestRunStats(run_id=uuid.uuid4().hex,started_at=started,finished_at=datetime.now(timezone.utc),
            per_source=per_source,deduped=0,filtered_out=0,extracted=0,extractor_used="no_extractions",
            errors=[source.error for source in news_sources if source.error],data_quality="news_unavailable_previous_risk_retained")
        with SessionLocal() as db:
            db.add(RunLogRecord(namespace=namespace,run_id=stats.run_id,finished_at=stats.finished_at,stats=stats.model_dump(mode="json")))
            if update_display: db.merge(DisplayState(id=1,namespace=namespace))
            db.commit()
        return stats
    unique, removed=dedupe(signals)
    relevant=sorted([signal for signal in unique if is_relevant(signal)],key=lambda signal:signal.published_at,reverse=True)
    all_relevant=list(relevant)
    if fixture_signals is None:
        relevant=relevant[:max(1,settings.max_articles_per_run)]
    deferred=len(all_relevant)-len(relevant)
    extractor=choose_extractor(); extractions=extractor.extract(relevant)
    assessments=[score_extraction(signal.signal_id, extraction, signal.source_name, signal.published_at, reference_time) for signal,extraction in zip(relevant,extractions)]
    price=None
    if "prices" in selected:
        value=PriceConnector().percent_change_24h(); price=market_score(value) if value is not None else None; per_source["prices"]=SourceRun(status="ok" if value is not None else "unavailable", fetched=1 if value is not None else 0, error=None if value is not None else "market corroboration skipped")
    seed=load_seed(); routes=[]
    ais_by_corridor={}
    if fixture_signals is None and namespace=="live":
        from ..connectors.ais import activity_summary
        activity=activity_summary(reference_time)
        ais_by_corridor={item["id"]:item["features"] for item in activity["corridors"]}
        per_source["ais"]=SourceRun(status=activity["health"]["status"],fetched=0)
    for route in seed["routes"]:
        route_assessments=[assessment for assessment in assessments if set(assessment.extraction.affected_chokepoints)&set(route["chokepoints"])]
        news=noisy_or([assessment.final_score for assessment in route_assessments]); composite=composite_score(news,price)
        corridor="hormuz" if "hormuz" in route["chokepoints"] else "red_sea" if "bab_el_mandeb" in route["chokepoints"] else None
        features=ais_by_corridor.get(corridor)
        before_ais=composite
        if features:
            from .vessel_features import fuse_activity
            composite=fuse_activity(composite,news,features)
        routes.append(RouteRisk(route_id=route["id"],name=route["name"],chokepoints=route["chokepoints"],news_score=news,market_score=price or 0,composite_score=composite,band=band_for_score(composite),contributing_signal_ids=[item.signal_id for item in route_assessments],computed_at=reference_time,ais_evidence=features,score_before_ais=before_ais))
    exposures=propagate(routes,seed)
    mix=sorted({extraction.extractor for extraction in extractions})
    stats=IngestRunStats(run_id=uuid.uuid4().hex,started_at=started,finished_at=datetime.now(timezone.utc),per_source=per_source,deduped=removed,filtered_out=len(unique)-len(all_relevant),extracted=len(assessments),extractor_used=",".join(mix) if mix else "no_extractions",errors=[v.error for v in per_source.values() if v.error],scenario_id=scenario_id,deferred=deferred)
    with SessionLocal() as db:
        add_alerts(db,namespace,stats.run_id,reference_time,routes,relevant,assessments)
        for signal,extraction in zip(relevant,extractions):
            db.merge(ArticleRecord(namespace=namespace,signal_id=signal.signal_id,published_at=signal.published_at,
                payload={"signal":signal.model_dump(mode="json"),"extraction":extraction.model_dump(mode="json")}))
        for signal in all_relevant[len(relevant):]:
            if db.get(ArticleRecord,(namespace,signal.signal_id)) is None:
                db.add(ArticleRecord(namespace=namespace,signal_id=signal.signal_id,published_at=signal.published_at,
                    payload={"signal":signal.model_dump(mode="json"),"extraction":{}}))
        db.execute(delete(AssessmentRecord).where(AssessmentRecord.namespace==namespace)); db.execute(delete(RouteRecord).where(RouteRecord.namespace==namespace)); db.execute(delete(RefineryRecord).where(RefineryRecord.namespace==namespace))
        db.add_all([AssessmentRecord(namespace=namespace,signal_id=s.signal_id,title=s.title,source_name=s.source_name,published_at=s.published_at,signal=s.model_dump(mode="json"),assessment=a.model_dump(mode="json")) for s,a in zip(relevant,assessments)])
        db.add_all([RouteRecord(namespace=namespace,route_id=r.route_id,payload=r.model_dump(mode="json")) for r in routes]); db.add_all([RefineryRecord(namespace=namespace,refinery_id=e.refinery_id,payload=e.model_dump(mode="json")) for e in exposures])
        db.add(RunLogRecord(namespace=namespace,run_id=stats.run_id,finished_at=stats.finished_at,stats=stats.model_dump(mode="json")))
        db.add(RiskSnapshot(run_id=stats.run_id, namespace=namespace, computed_at=reference_time,
            payload={"signals": [s.model_dump(mode="json") for s in relevant],
                     "assessments": [a.model_dump(mode="json") for a in assessments],
                     "routes": [r.model_dump(mode="json") for r in routes],
                     "refineries": [r.model_dump(mode="json") for r in exposures],
                     "market": {"brent_change_24h_pct":value if "prices" in selected else None,
                                "retrieved_at":stats.finished_at.isoformat() if "prices" in selected else None}}))
        if update_display:
            db.merge(DisplayState(id=1, namespace=namespace))
        db.commit()
    return stats
