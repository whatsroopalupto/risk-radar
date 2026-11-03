from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import select
import pytest
from app.main import app
from app.db import SessionLocal, RiskSnapshot, AssessmentRecord, DisplayState
from app.pipeline.orchestrator import run_cycle
from app.pipeline.locking import exclusive_job, JobBusy

def test_replay_keeps_live_snapshot_and_health_matches_display():
    now = datetime.now(timezone.utc)
    run_cycle(fixture_signals=[], sources=[], reference_time=now)
    with TestClient(app) as client:
        response = client.post("/api/replay/hormuz_june2025")
        assert response.status_code == 200
        health = client.get("/api/health").json()
        assert health["dataset"] == "replay:hormuz_june2025"
        assert health["latest_run"]["run_id"] == response.json()["run_id"]
        assert health["db_counts"]["assessments"] == len(client.get("/api/signals?limit=2000").json())
        assert client.post("/api/display/live").status_code == 200
        assert client.get("/api/signals").json() == []
    with SessionLocal() as db:
        snapshots = db.scalars(select(RiskSnapshot)).all()
        assert {r.namespace for r in snapshots} == {"live", "replay:hormuz_june2025"}

def test_repeated_replay_does_not_repeat_alerts_but_keeps_history():
    with TestClient(app) as client:
        client.post("/api/replay/hormuz_june2025")
        first = client.get("/api/alerts").json()
        assert first and first[0]["signal_ids"]
        client.post("/api/replay/hormuz_june2025")
        assert client.get("/api/alerts").json() == first
        assert len(client.get("/api/risk/history").json()) == 2

def test_background_poll_does_not_replace_selected_replay():
    with TestClient(app) as client:
        client.post("/api/replay/red_sea_dec2023")
        run_cycle(fixture_signals=[], sources=[], update_display=False)
        assert client.get("/api/health").json()["dataset"] == "replay:red_sea_dec2023"

def test_ingestion_overlap_is_rejected_and_lock_released():
    with exclusive_job("ingestion"):
        with pytest.raises(JobBusy): run_cycle(fixture_signals=[], sources=[])
        with TestClient(app) as client:
            assert client.post("/api/replay/hormuz_june2025").status_code == 409
    run_cycle(fixture_signals=[], sources=[])

def test_cors_and_input_limits():
    with TestClient(app) as client:
        response = client.options("/api/health", headers={"Origin":"http://localhost:5173", "Access-Control-Request-Method":"GET"})
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert client.get("/api/signals?limit=-1").status_code == 422
        assert client.post("/api/ingest/run?window_hours=999").status_code == 422

def test_total_news_outage_keeps_previous_scores(monkeypatch):
    import json
    from pathlib import Path
    from app.schemas import Signal
    payload=json.loads((Path(__file__).parents[1]/"data"/"fixtures"/"hormuz_june2025.json").read_text())
    run_cycle(fixture_signals=[Signal.model_validate(item) for item in payload["signals"]],sources=[],reference_time=datetime.fromisoformat(payload["reference_time"]))
    with TestClient(app) as client:
        previous=client.get("/api/risk/routes").json()
        def unavailable(*args): raise RuntimeError("Offline")
        monkeypatch.setattr("app.pipeline.orchestrator.RSSConnector.fetch",unavailable)
        monkeypatch.setattr("app.pipeline.orchestrator.GDELTConnector.fetch",unavailable)
        result=client.post("/api/ingest/run").json()
        assert result["data_quality"]=="news_unavailable_previous_risk_retained"
        assert client.get("/api/risk/routes").json()==previous

def test_illustrative_replay_never_exposes_placeholder_links_as_reporting():
    with TestClient(app) as client:
        client.post("/api/replay/hormuz_june2025")
        values=client.get("/api/signals").json()
        assert values and all(value["url"] is None for value in values)
        assert all(value["source_name"].startswith("Synthetic fixture") for value in values)
