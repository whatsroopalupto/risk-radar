"""Pure day-bucketed route risk trend, derived from stored assessments — no I/O, no clock reads."""
from ..schemas import RiskAssessment
from .scorer import band_for_score, noisy_or


def route_score_timeseries(assessments: list[RiskAssessment], seed: dict) -> list[dict]:
    """Bucket assessments by published date and compute a cumulative-to-date
    noisy-OR per route/day, so a multi-day replay or wide ingestion window
    renders as a real trend line whose final point matches the route's
    current live news_score, instead of a single snapshot or a
    day-isolated figure that would read inconsistently against it."""
    dated = [item for item in assessments if item.published_at is not None]
    dates = sorted({item.published_at.date() for item in dated})
    series = []
    for route in seed["routes"]:
        chokepoints = set(route["chokepoints"])
        matching = [item for item in dated if set(item.extraction.affected_chokepoints) & chokepoints]
        points = []
        for day in dates:
            to_date_scores = [item.final_score for item in matching if item.published_at.date() <= day]
            same_day_count = sum(1 for item in matching if item.published_at.date() == day)
            news = noisy_or(to_date_scores) if to_date_scores else 0.0
            points.append({
                "date": day.isoformat(),
                "news_score": round(news * 100.0, 2),
                "band": band_for_score(news * 100.0),
                "signal_count": same_day_count,
            })
        series.append({"route_id": route["id"], "name": route["name"], "points": points})
    return series
