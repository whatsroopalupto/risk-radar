import json
from datetime import datetime,timezone
import httpx
from app.pipeline.extractors.gemini import GeminiExtractor
from app.schemas import Signal

def signal(ident):
    now=datetime.now(timezone.utc)
    return Signal(signal_id=ident,source_type="news",source_name="test",title="Hormuz oil tanker",published_at=now,fetched_at=now)

def test_long_evidence_retains_ai_provenance(monkeypatch):
    item={"is_relevant":True,"event_type":"attack_on_vessel","severity":0.9,
        "affected_chokepoints":["hormuz"],"affected_countries":[],"is_speculative":False,
        "confidence":0.8,"evidence":"A long source-based sentence. "*15,"extractor":"model"}
    monkeypatch.setattr("app.pipeline.extractors.gemini.httpx.post",lambda url,**kwargs:httpx.Response(200,
        json={"candidates":[{"content":{"parts":[{"text":json.dumps([item])}]}}]},request=httpx.Request("POST",url)))
    result=GeminiExtractor(api_key="test")._request([signal("long-evidence")])[0]
    assert len(result.evidence)<=200 and result.evidence_truncated
    assert result.extractor.startswith("gemini")

def test_service_failure_opens_batch_circuit_after_retry(monkeypatch):
    calls=[]
    extractor=GeminiExtractor(api_key="test")
    def request(*args,**kwargs):
        calls.append(1)
        raise httpx.HTTPStatusError("Unavailable",request=httpx.Request("POST","https://example.org"),response=httpx.Response(503))
    monkeypatch.setattr(extractor,"_request",request)
    monkeypatch.setattr(extractor,"_throttle",lambda:None)
    monkeypatch.setattr("app.pipeline.extractors.gemini.load",lambda ident:None)
    values=extractor.extract([signal(str(i)) for i in range(17)])
    assert len(calls)==2 and len(values)==17
    assert {value.extractor for value in values}=={"heuristic-v1"}
