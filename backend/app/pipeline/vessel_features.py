"""Coverage-gated, explainable observed-activity corroboration.

Connection heartbeat coverage is a proxy, not a receiver delivery guarantee.
Never interpret a total loss of observations as a traffic collapse.
"""
from datetime import timedelta, timezone
from statistics import mean
from sqlalchemy import func, select
from ..config import settings
from ..db import AisCoverageMinute, VesselObservation, SessionLocal

def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

def assess_activity(baseline_counts, current_count, coverage_fraction, required_hours, fresh):
    result={"baseline_hours":len(baseline_counts),"required_hours":required_hours,
        "current_unique_vessels":current_count,"coverage_fraction":round(coverage_fraction,3),
        "status":"collecting","anomaly":None,
        "limitation":"Observed Class A activity, not verified crude tanker flow; heartbeat coverage does not guarantee receiver coverage."}
    if len(baseline_counts)<required_hours:
        return result
    expected=mean(baseline_counts)
    result.update(status="ready",expected_unique_vessels=round(expected,2))
    if not fresh or coverage_fraction<0.8 or current_count==0 or expected<5:
        result["status"]="insufficient_current_coverage"
        return result
    drop=max(0.0,1-current_count/expected)
    if drop>=0.5:
        result["anomaly"]={"kind":"observed_activity_drop","fraction":round(drop,3),
            "confidence":round(min(1.0,coverage_fraction),3),"interpretation":"Activity corroboration; not proof of a closure or attack"}
    return result

def corridor_features(corridor, now, fresh):
    end=now.replace(minute=0,second=0,microsecond=0)
    start=end-timedelta(hours=1)
    earliest=start-timedelta(days=max(45,settings.ais_baseline_days*2))
    with SessionLocal() as db:
        minutes=db.scalars(select(AisCoverageMinute.minute).where(AisCoverageMinute.minute>=earliest,AisCoverageMinute.minute<end)).all()
        coverage={}
        for minute in minutes:
            hour=utc(minute).replace(minute=0,second=0,microsecond=0)
            coverage[hour]=coverage.get(hour,0)+1
        rows=db.execute(select(func.strftime("%Y-%m-%dT%H:00:00",VesselObservation.observed_at),func.count(func.distinct(VesselObservation.mmsi))).where(
            VesselObservation.corridor==corridor,VesselObservation.observed_at>=earliest,VesselObservation.observed_at<end).group_by(func.strftime("%Y-%m-%dT%H:00:00",VesselObservation.observed_at))).all()
    from datetime import datetime
    counts={datetime.fromisoformat(hour).replace(tzinfo=timezone.utc):count for hour,count in rows}
    baseline=[count for hour,count in sorted(counts.items()) if hour<start and coverage.get(hour,0)>=48]
    required=settings.ais_baseline_days*24
    result=assess_activity(baseline[-required:],counts.get(start,0),min(1.0,coverage.get(start,0)/60),required,fresh)
    result.update(window_start=start.isoformat(),window_end=end.isoformat())
    return result

def fuse_activity(base_score, news_score, features):
    anomaly=features.get("anomaly")
    if news_score<=0 or not anomaly or features.get("status")!="ready":
        return base_score
    # At most 10% of remaining headroom; corroboration never creates a risk
    # assessment by itself and never hides news evidence when AIS is missing.
    return min(100.0,base_score+(100-base_score)*0.1*anomaly["fraction"]*anomaly["confidence"])
