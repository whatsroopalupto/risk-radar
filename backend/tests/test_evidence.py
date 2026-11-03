import json
from datetime import datetime, timezone
import httpx
from app.config import settings
from app.db import ArticleRecord, SessionLocal
from app.evidence import answer_question, retrieve

def seed():
    with SessionLocal() as db:
        for namespace, title, ident in [("live","Hormuz oil tanker disruption","a"),("replay:test","Red Sea vessel attack","b")]:
            db.add(ArticleRecord(namespace=namespace,signal_id=ident,published_at=datetime.now(timezone.utc),
                payload={"signal":{"title":title,"source_name":"test source","url":"https://example.org/evidence","published_at":"2025-01-01T00:00:00Z"},
                    "extraction":{"evidence":"Test evidence","affected_chokepoints":["hormuz"]}}))
        db.commit()

def test_retrieval_never_mixes_replay_and_live():
    seed()
    assert [r["id"] for r in retrieve("Hormuz oil", "live")] == ["a"]
    assert retrieve("Red Sea", "live") == []
    assert retrieve("Hormuz", "live", "red_sea_suez") == []

def test_generated_unknown_citation_falls_back_without_exposing_provider_error(monkeypatch):
    seed()
    monkeypatch.setattr(settings,"gemini_api_key","offline-test")
    def post(*args,**kwargs):
        assert "offline-test" not in args[0]
        return httpx.Response(200,json={"candidates":[{"content":{"parts":[{"text":json.dumps({"paragraphs":[{"text":"Unsupported answer","citations":["invented"]}]})}]}}]},request=httpx.Request("POST",args[0]))
    monkeypatch.setattr("app.evidence.httpx.post",post)
    result=answer_question("Hormuz oil", "live")
    assert result["mode"] == "retrieval_only"
    assert result["paragraphs"][0]["citations"] == ["a"]

def test_generation_requires_retrieved_evidence(monkeypatch):
    monkeypatch.setattr("app.evidence.httpx.post",lambda *a,**k: (_ for _ in ()).throw(AssertionError("No model call expected")))
    assert answer_question("Hormuz", "live")["sources"] == []

def test_valid_cited_generation(monkeypatch):
    seed()
    monkeypatch.setattr(settings,"gemini_api_key","offline-test")
    value={"paragraphs":[{"text":"The stored report concerns Hormuz shipping.","citations":["S1"]}]}
    monkeypatch.setattr("app.evidence.httpx.post",lambda url,**kwargs: httpx.Response(200,
        json={"candidates":[{"content":{"parts":[{"text":json.dumps(value)}]}}]},request=httpx.Request("POST",url)))
    result=answer_question("Hormuz shipping", "live")
    assert result["mode"] == "rag"
    assert result["paragraphs"][0]["citations"] == ["a"]

def test_synthetic_publisher_links_are_never_treated_as_real_sources():
    with SessionLocal() as db:
        db.add(ArticleRecord(namespace="replay:test",signal_id="fixture",published_at=datetime.now(timezone.utc),
            payload={"signal":{"title":"Hormuz closure scenario","source_name":"reuters.com","url":"https://reuters.com/fake","raw":{"_fixture":True}},"extraction":{}}))
        db.commit()
    result=answer_question("Hormuz closure","replay:test",generate=False)
    assert result["sources"][0]["url"] is None
    assert "Synthetic" in result["sources"][0]["source"]
    assert "Illustrative" in result["notice"]
