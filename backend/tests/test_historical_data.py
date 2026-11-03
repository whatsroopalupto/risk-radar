from __future__ import annotations

from pathlib import Path
import csv

import httpx

from app.historical.validation import validate_historical_dataset
from scripts.collect_gdelt_history import (
    collect_gdelt_articles,
    parse_gdelt_response,
    write_article_csv,
)


ROOT = Path(__file__).resolve().parents[2]
EVENTS_PATH = ROOT / "data" / "historical" / "processed" / "historical_events.csv"
SOURCES_PATH = ROOT / "data" / "historical" / "source_register.csv"


def test_historical_dataset_is_valid():
    summary = validate_historical_dataset(EVENTS_PATH, SOURCES_PATH)
    assert summary["valid"] is True, summary["errors"]


def test_duplicate_detection():
    duplicate_rows = [
        {
            "event_id": "EVT-001",
            "event_name": "Test Event",
            "event_date": "2024-01-01",
            "event_end_date": "2024-01-02",
            "region": "Red Sea",
            "affected_route": "Red Sea",
            "event_type": "shipping_disruption",
            "severity": "HIGH",
            "route_risk_label": "MEDIUM",
            "india_impact": "Possible",
            "india_impact_evidence": "Need verification",
            "evidence_confidence": "MEDIUM",
            "label_rationale": "This is a sample event.",
            "source_ids": "SRC-001",
            "review_status": "draft",
        },
        {
            "event_id": "EVT-001",
            "event_name": "Test Event",
            "event_date": "2024-01-01",
            "event_end_date": "2024-01-02",
            "region": "Red Sea",
            "affected_route": "Red Sea",
            "event_type": "shipping_disruption",
            "severity": "HIGH",
            "route_risk_label": "MEDIUM",
            "india_impact": "Possible",
            "india_impact_evidence": "Need verification",
            "evidence_confidence": "MEDIUM",
            "label_rationale": "This is a sample event.",
            "source_ids": "SRC-001",
            "review_status": "draft",
        },
    ]
    assert "duplicate_event_id" in validate_historical_dataset(__file__, __file__, sample_rows=duplicate_rows)["duplicate_checks"]


def test_gdelt_failure_is_handled_without_crashing(monkeypatch):
    def fake_get(*args, **kwargs):
        raise httpx.RequestError("offline")

    monkeypatch.setattr("httpx.get", fake_get)
    assert collect_gdelt_articles(["strait of hormuz"], max_records=5) == []


def test_missing_article_fields_are_ignored():
    payload = {"articles": [{"title": "Missing URL article"}]}
    assert parse_gdelt_response(payload, "test query") == []


def test_empty_api_response_is_safe():
    assert parse_gdelt_response({}, "test query") == []


def test_archive_survives_outage_and_accumulates_deduplicated_rows(tmp_path, monkeypatch):
    archive = tmp_path / "articles.csv"
    rows = parse_gdelt_response({"articles": [{"title": "First", "url": "https://example.org/one"}]}, "oil")
    write_article_csv(rows, archive)
    original = archive.read_bytes()
    def offline(*args, **kwargs):
        raise httpx.RequestError("offline")
    monkeypatch.setattr("httpx.get", offline)
    assert collect_gdelt_articles(["oil"], output_path=archive) == []
    assert archive.read_bytes() == original
    write_article_csv(rows + parse_gdelt_response({"articles": [{"title": "Second", "url": "https://example.org/two"}]}, "oil"), archive)
    with archive.open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 2


def test_reversed_dates_rejected():
    with EVENTS_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows[0]["event_end_date"] = "1900-01-01"
    result = validate_historical_dataset(EVENTS_PATH, SOURCES_PATH, sample_rows=rows)
    assert any("precedes" in error for error in result["errors"])


def test_cross_event_sources_and_orphans_rejected(tmp_path):
    with SOURCES_PATH.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        sources = list(reader)
    sources[0]["event_id"] = sources[3]["event_id"]
    sources[1]["event_id"] = "unknown-event"
    path = tmp_path / "sources.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sources)
    result = validate_historical_dataset(EVENTS_PATH, path)
    assert not result["valid"]
    assert any("different event" in error for error in result["errors"])
    assert any("unknown event_id" in error for error in result["errors"])
