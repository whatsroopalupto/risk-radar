from datetime import datetime, timedelta, timezone
import pytest
from app.evaluation import LabelledCase, evaluate, metrics
from app.schemas import Signal

def test_metrics_report_false_positives_and_undefined_values():
    result=metrics([True,True,False,False],[True,False,True,False])
    assert result["precision"] == result["recall"] == result["f1"] == 0.5
    assert metrics([False],[False])["precision"] is None
    assert metrics([False],[False])["recall"] is None

def case():
    now=datetime(2025,6,24,tzinfo=timezone.utc)
    return LabelledCase(case_id="test-case",event_id="test-event",split="test",
        route_id="hormuz_west_coast",window_start=now-timedelta(days=1),as_of=now,
        disruption=True,label_sources=["https://example.org/test-only-label"],
        label_rationale="Synthetic test label; not an academic result",labelled_by="test",
        signals=[Signal(signal_id="test-signal",source_type="news",source_name="reuters.com",
            title="Hormuz oil tanker blockade closure",published_at=now-timedelta(hours=1),fetched_at=now+timedelta(hours=1))])

def test_future_availability_cannot_leak_into_prediction():
    result=evaluate([case()])
    assert result["cases"][0]["available_articles"] == 0
    assert result["cases"][0]["predicted"] is False
    assert result["metrics"]["false_negative"] == 1

def test_same_event_cannot_leak_across_splits():
    first=case()
    second=first.model_copy(update={"case_id":"other","split":"development"})
    with pytest.raises(ValueError,match="event"):
        evaluate([first,second])
