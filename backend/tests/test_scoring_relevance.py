from datetime import datetime,timezone
from app.schemas import RiskExtraction
from app.pipeline.scorer import score_extraction

def test_extraction_explicitly_marked_irrelevant_cannot_inflate_route_risk():
    extraction=RiskExtraction(is_relevant=False,event_type="attack_on_vessel",severity=1,
        confidence=1,affected_chokepoints=["hormuz"],affected_countries=[],is_speculative=False,
        evidence="This report is not relevant to crude supply",extractor="test")
    now=datetime.now(timezone.utc)
    result=score_extraction("irrelevant",extraction,"reuters.com",now,now)
    assert result.final_score==0
    assert result.component_scores["relevance_weight"]==0
