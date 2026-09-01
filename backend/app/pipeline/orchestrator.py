"""One complete, independently degrading ingestion cycle."""
import logging, uuid
from datetime import datetime, timezone
from sqlalchemy import delete, select
from ..connectors.gdelt import GDELTConnector
from ..connectors.prices import PriceConnector
from ..connectors.rss import RSSConnector
from ..db import AssessmentRecord, RefineryRecord, RouteRecord, RunLogRecord, SessionLocal
from ..graph.builder import load_seed
from ..graph.propagate import propagate
from ..schemas import IngestRunStats, RouteRisk, Signal, SourceRun
from .normalize import dedupe
from .relevance import is_relevant
from .scorer import band_for_score, composite_score, market_score, noisy_or, score_extraction
from .extractors.gemini import GeminiExtractor
from .extractors.heuristic import HeuristicExtractor
from ..config import settings
LOGGER=logging.getLogger(__name__)
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
def run_cycle(window_hours: int = 24, sources: list[str] | None = None, fixture_signals: list[Signal] | None = None, reference_time: datetime | None = None, namespace: str = "live", scenario_id: str | None = None) -> IngestRunStats:
    """Run fetch through propagation while isolating failures to each source."""
    started=datetime.now(timezone.utc); reference_time=reference_time or started; selected=["rss","gdelt","prices"] if sources is None else sources; connectors={"rss":RSSConnector(),"gdelt":GDELTConnector()}; per_source={}; signals=list(fixture_signals or [])
    for name in selected:
        if name == "prices": continue
        connector=connectors.get(name)
        if not connector: continue
        try:
            values=connector.fetch(window_hours); signals.extend(values); per_source[name]=SourceRun(status="ok",fetched=len(values))
        except (OSError, ValueError, RuntimeError) as exc:
            per_source[name]=SourceRun(status="unavailable",error=str(exc)); LOGGER.warning("%s unavailable: %s",name,exc)
    if fixture_signals is not None: per_source["fixture"]=SourceRun(status="ok",fetched=len(fixture_signals))
    unique, removed=dedupe(signals); relevant=[signal for signal in unique if is_relevant(signal)]; extractor=choose_extractor(); extractions=extractor.extract(relevant)
    assessments=[score_extraction(signal.signal_id, extraction, signal.source_name, signal.published_at, reference_time) for signal,extraction in zip(relevant,extractions)]
    price=None
    if "prices" in selected:
        value=PriceConnector().percent_change_24h(); price=market_score(value) if value is not None else None; per_source["prices"]=SourceRun(status="ok" if value is not None else "unavailable", fetched=1 if value is not None else 0, error=None if value is not None else "market corroboration skipped")
    seed=load_seed(); routes=[]
    for route in seed["routes"]:
        route_assessments=[assessment for assessment in assessments if set(assessment.extraction.affected_chokepoints)&set(route["chokepoints"])]
        news=noisy_or([assessment.final_score for assessment in route_assessments]); composite=composite_score(news,price)
        routes.append(RouteRisk(route_id=route["id"],name=route["name"],chokepoints=route["chokepoints"],news_score=news,market_score=price or 0,composite_score=composite,band=band_for_score(composite),contributing_signal_ids=[item.signal_id for item in route_assessments],computed_at=reference_time))
    exposures=propagate(routes,seed)
    stats=IngestRunStats(run_id=uuid.uuid4().hex,started_at=started,finished_at=datetime.now(timezone.utc),per_source=per_source,deduped=removed,filtered_out=len(unique)-len(relevant),extracted=len(assessments),extractor_used=extractions[0].extractor if extractions else ("gemini-2.5-flash" if isinstance(extractor,GeminiExtractor) else "heuristic-v1"),errors=[v.error for v in per_source.values() if v.error],scenario_id=scenario_id)
    with SessionLocal() as db:
        db.execute(delete(AssessmentRecord).where(AssessmentRecord.namespace==namespace)); db.execute(delete(RouteRecord).where(RouteRecord.namespace==namespace)); db.execute(delete(RefineryRecord).where(RefineryRecord.namespace==namespace))
        db.add_all([AssessmentRecord(namespace=namespace,signal_id=s.signal_id,title=s.title,source_name=s.source_name,published_at=s.published_at,signal=s.model_dump(mode="json"),assessment=a.model_dump(mode="json")) for s,a in zip(relevant,assessments)])
        db.add_all([RouteRecord(namespace=namespace,route_id=r.route_id,payload=r.model_dump(mode="json")) for r in routes]); db.add_all([RefineryRecord(namespace=namespace,refinery_id=e.refinery_id,payload=e.model_dump(mode="json")) for e in exposures])
        db.add(RunLogRecord(namespace=namespace,run_id=stats.run_id,finished_at=stats.finished_at,stats=stats.model_dump(mode="json")))
        db.commit()
    return stats
