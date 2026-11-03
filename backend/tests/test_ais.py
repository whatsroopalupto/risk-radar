import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import pytest
from sqlalchemy import func, select
from app.connectors.ais import parse_position, save_position, activity_summary, collect_forever
from app.db import SessionLocal, VesselObservation
from app.config import settings

NOW = datetime(2026, 11, 3, 8, tzinfo=timezone.utc)

def message():
    return {"MessageType":"PositionReport", "MetaData":{"MMSI":123456789,
        "ShipName":"EXAMPLE", "time_utc":NOW.isoformat()},
        "Message":{"PositionReport":{"Valid":True,"Latitude":26.2,"Longitude":56.5,"Sog":12.4}}}

def test_valid_position_and_real_observation_time():
    position = parse_position(message(), NOW)
    assert position["corridor"] == "hormuz"
    assert position["observed_at"] == NOW

@pytest.mark.parametrize("timestamp", ["2026-11-03 08:00:00.000000 +0000 UTC", "2026-11-03 08:00:00 UTC"])
def test_provider_utc_timestamp_variants(timestamp):
    payload=message()
    payload["MetaData"]["time_utc"]=timestamp
    assert parse_position(payload,NOW)["observed_at"] == NOW

@pytest.mark.parametrize("change", ["outside", "nan", "invalid", "missing_time", "future", "stale", "mmsi"])
def test_reject_unusable_positions(change):
    payload = message()
    report = payload["Message"]["PositionReport"]
    if change == "outside": report["Latitude"] = 0
    if change == "nan": report["Longitude"] = float("nan")
    if change == "invalid": report["Valid"] = False
    if change == "missing_time": del payload["MetaData"]["time_utc"]
    if change == "future": payload["MetaData"]["time_utc"] = (NOW + timedelta(hours=1)).isoformat()
    if change == "stale": payload["MetaData"]["time_utc"] = (NOW - timedelta(days=2)).isoformat()
    if change == "mmsi": payload["MetaData"]["MMSI"] = 1
    assert parse_position(payload, NOW) is None

def test_duplicate_does_not_inflate_counts_or_unique_vessels():
    assert save_position(message(), NOW)
    assert not save_position(message(), NOW)
    second = deepcopy(message())
    second["MetaData"]["time_utc"] = (NOW + timedelta(minutes=1)).isoformat()
    assert save_position(second, NOW + timedelta(minutes=1))
    summary = activity_summary(NOW + timedelta(minutes=2))
    hormuz = summary["corridors"][0]
    assert hormuz["observations_24h"] == 2
    assert hormuz["unique_vessels_24h"] == 1
    assert hormuz["anomaly"] is None
    assert hormuz["baseline_status"] == "collecting"

def test_no_key_never_connects(monkeypatch):
    monkeypatch.setattr(settings, "aisstream_api_key", "")
    with pytest.raises(SystemExit, match="AISSTREAM_API_KEY"):
        asyncio.run(collect_forever())
    assert activity_summary(NOW)["health"]["status"] == "not_configured"

def test_stream_subscribes_and_persists_binary_frames_without_live_network(monkeypatch):
    sent = []
    frames = [json.dumps({"MessageType":"SubscriptionConfirmation"}).encode(), json.dumps(message()).encode()]
    class Socket:
        async def send(self, subscription): sent.append(json.loads(subscription))
        async def recv(self):
            if frames: return frames.pop(0)
            raise asyncio.CancelledError
    class Connection:
        async def __aenter__(self): return Socket()
        async def __aexit__(self, *args): return False
    monkeypatch.setattr("websockets.asyncio.client.connect", lambda *args, **kwargs: Connection())
    monkeypatch.setattr(settings, "aisstream_api_key", "offline-test-key")
    monkeypatch.setattr("app.connectors.ais.utcnow", lambda: NOW)
    with pytest.raises(asyncio.CancelledError): asyncio.run(collect_forever())
    assert sent[0]["APIKey"] == "offline-test-key"
    assert len(sent[0]["BoundingBoxes"]) == 2
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(VesselObservation)) == 1
