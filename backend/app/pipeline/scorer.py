"""Pure, reproducible deterministic scoring functions."""
import math
from datetime import datetime
from ..schemas import RiskAssessment, RiskBand, RiskExtraction
from .credibility import credibility_for_domain
TYPE_WEIGHTS = {"blockade_or_closure":1.0,"attack_on_vessel":.9,"military_strike":.85,"port_or_terminal_disruption":.75,"sanctions":.6,"naval_buildup":.55,"diplomatic_escalation":.35,"policy_change":.3,"other":.15}
LOW_MAX, MEDIUM_MAX, RECENCY_HOURS = 30.0, 65.0, 48.0
def band_for_score(score: float) -> RiskBand:
    """Convert the shared 0–100 display scale into a named risk band."""
    return "low" if score < LOW_MAX else "medium" if score < MEDIUM_MAX else "high"
def recency_weight(published_at: datetime, reference_time: datetime) -> float:
    """Decay stale reporting relative to a caller-provided clock."""
    return math.exp(-max(0., (reference_time-published_at).total_seconds()/3600)/RECENCY_HOURS)
def score_extraction(signal_id: str, extraction: RiskExtraction, domain: str | None, published_at: datetime, reference_time: datetime) -> RiskAssessment:
    """Calculate an audit-ready score without I/O or implicit time."""
    tier, credibility = credibility_for_domain(domain); recency = recency_weight(published_at, reference_time)
    type_weight = TYPE_WEIGHTS[extraction.event_type]; speculative = .6 if extraction.is_speculative else 1.
    final = type_weight*extraction.severity*extraction.confidence*credibility*recency*speculative
    components = {"type_weight":type_weight,"severity":extraction.severity,"confidence":extraction.confidence,"credibility_weight":credibility,"recency_weight":recency,"speculative_weight":speculative}
    return RiskAssessment(signal_id=signal_id, extraction=extraction, credibility_tier=tier, credibility_weight=credibility, recency_weight=recency, type_weight=type_weight, speculative_weight=speculative, component_scores=components, final_score=final, band=band_for_score(final*100))
def noisy_or(scores: list[float]) -> float:
    """Aggregate corroborating bounded signal evidence monotonically."""
    return 1-math.prod(1-max(0., min(1., score)) for score in scores)
def market_score(pct_change_24h: float) -> float:
    """Normalize a one-day Brent movement to the corroboration scale."""
    return min(1., abs(pct_change_24h)/8.)
def composite_score(news: float, market: float | None) -> float:
    """Combine market evidence only where a route already has news evidence."""
    if news <= 0: return 0.
    return 100*(news if market is None else .75*news+.25*market)
