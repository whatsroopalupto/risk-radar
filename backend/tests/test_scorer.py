from datetime import datetime, timedelta, timezone
from app.pipeline.scorer import *
from app.schemas import RiskExtraction
NOW=datetime(2025,1,2,tzinfo=timezone.utc)
def e(**kw):
 data=dict(is_relevant=True,event_type="blockade_or_closure",severity=.5,affected_chokepoints=["hormuz"],affected_countries=[],is_speculative=False,confidence=.5,evidence="x",extractor="heuristic-v1"); data.update(kw); return RiskExtraction(**data)
def score(**kw): return score_extraction("id",e(**kw),"reuters.com",NOW,NOW).final_score
def test_severity_monotonic(): assert score(severity=.8)>score(severity=.2)
def test_confidence_monotonic(): assert score(confidence=.8)>score(confidence=.2)
def test_recency_reduces(): assert recency_weight(NOW-timedelta(hours=48),NOW)<1
def test_recency_approaches_zero(): assert recency_weight(NOW-timedelta(days=100),NOW)<.001
def test_noisy_or_bounds(): assert 0<=noisy_or([.2,.3])<1
def test_noisy_or_one(): assert noisy_or([.4])==.4
def test_noisy_or_empty(): assert noisy_or([])==0
def test_bands(): assert [band_for_score(x) for x in (29.9,30,65)]==["low","medium","high"]
def test_speculative_discount(): assert score(is_speculative=True)<score()
def test_market_only_does_not_score(): assert composite_score(0,.8)==0
