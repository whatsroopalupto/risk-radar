"""Evidence-linked route threshold crossings, committed with their source run."""
from sqlalchemy import select
from ..db import AlertRecord, RouteRecord

def add_alerts(db, namespace, run_id, computed_at, routes, signals, assessments):
    evidence = {s.signal_id:{"signal_id":s.signal_id,"title":s.title,"url":s.url,
        "published_at":s.published_at.isoformat(),"source":s.source_name,
        "explanation":a.extraction.evidence,"extractor":a.extraction.extractor}
        for s,a in zip(signals, assessments)}
    previous = {row.route_id: row.payload for row in db.scalars(
        select(RouteRecord).where(RouteRecord.namespace == namespace)).all()}
    for route in routes:
        prior = previous.get(route.route_id, {})
        threshold = 65 if route.composite_score >= 65 else 30 if route.composite_score >= 30 else None
        if threshold is None or not route.contributing_signal_ids:
            continue
        if prior.get("composite_score", 0) >= threshold:
            continue
        db.add(AlertRecord(namespace=namespace, route_id=route.route_id, run_id=run_id,
            occurred_at=computed_at, payload={"route_name":route.name,
                "previous_score":prior.get("composite_score"), "score":route.composite_score,
                "threshold":threshold, "band":route.band, "signal_ids":route.contributing_signal_ids,
                "kind":"threshold_crossing" if prior else "initial_elevated_risk",
                "evidence":[evidence[sid] for sid in route.contributing_signal_ids[:5] if sid in evidence]}))
