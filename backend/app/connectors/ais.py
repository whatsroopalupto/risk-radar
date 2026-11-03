"""Server-side AISStream collection. Observations are not confirmed tanker transits."""
import asyncio
import json
import math
import random
import re
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from ..config import settings
from ..db import CollectorState, SessionLocal, VesselObservation, VesselProfile, AisCoverageMinute, init_db, utcnow
from .base import BaseConnector

# Research bounding boxes, not official transit gates.
CORRIDORS = {"hormuz": ((25.0, 55.0), (27.5, 58.0)),
             "red_sea": ((12.0, 42.0), (16.0, 44.5))}
STREAM_URL = "wss://stream.aisstream.io/v0/stream"


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def parse_position(message: dict, received_at: datetime) -> dict | None:
    """Reject invalid, stale, future and out-of-scope positions."""
    if message.get("MessageType") != "PositionReport":
        return None
    try:
        meta = message["MetaData"]
        report = message["Message"]["PositionReport"]
        if report.get("Valid") is False:
            return None
        mmsi = str(meta["MMSI"])
        if len(mmsi) != 9 or not mmsi.isdigit() or mmsi.startswith("0"):
            return None
        latitude = float(report.get("Latitude", meta.get("latitude", meta.get("Latitude"))))
        longitude = float(report.get("Longitude", meta.get("longitude", meta.get("Longitude"))))
        if not math.isfinite(latitude) or not math.isfinite(longitude):
            return None
        corridor = next((name for name, (lo, hi) in CORRIDORS.items()
                         if lo[0] <= latitude <= hi[0] and lo[1] <= longitude <= hi[1]), None)
        if corridor is None:
            return None
        # AIS Timestamp is seconds-of-minute; only provider metadata dates the fix.
        raw_time = meta.get("time_utc")
        if not raw_time:
            return None
        raw_time = str(raw_time).strip()
        explicit_utc = raw_time.endswith(" UTC")
        timestamp = raw_time.removesuffix(" UTC").replace("Z", "+00:00")
        timestamp = re.sub(r"\s+([+-]\d{4})$", r"\1", timestamp)
        observed_at = datetime.fromisoformat(timestamp)
        if observed_at.tzinfo is None and explicit_utc:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        if observed_at.tzinfo is None:
            return None
        if not received_at - timedelta(hours=24) <= observed_at <= received_at + timedelta(minutes=5):
            return None
        speed = float(report["Sog"]) if report.get("Sog") is not None else None
        if speed is not None and (not math.isfinite(speed) or not 0 <= speed < 102.3):
            speed = None
        return dict(mmsi=mmsi, corridor=corridor, observed_at=observed_at.astimezone(timezone.utc),
                    received_at=received_at.astimezone(timezone.utc), latitude=latitude, longitude=longitude,
                    speed_knots=speed, ship_name=str(meta.get("ShipName", "")).strip()[:255])
    except (KeyError, ValueError, TypeError, OverflowError):
        return None


def save_position(message: dict, received_at: datetime | None = None) -> bool:
    position = parse_position(message, received_at or utcnow())
    if position is None:
        return False
    with SessionLocal() as db:
        db.add(VesselObservation(**position))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return False
    return True


def set_collector_state(status: str, detail: str = ""):
    with SessionLocal() as db:
        db.merge(CollectorState(name="ais", status=status, updated_at=utcnow(), detail=detail))
        if status=="connected":
            db.merge(AisCoverageMinute(minute=utcnow().replace(second=0,microsecond=0)))
        db.commit()

def save_profile(message):
    if message.get("MessageType")!="ShipStaticData":
        return False
    try:
        report=message["Message"]["ShipStaticData"]
        mmsi=str(message.get("MetaData",{}).get("MMSI") or report["UserID"])
        ship_type=int(report["Type"])
        if len(mmsi)!=9 or not mmsi.isdigit() or not 0<=ship_type<=99:
            return False
        with SessionLocal() as db:
            db.merge(VesselProfile(mmsi=mmsi,ship_type=ship_type,updated_at=utcnow()))
            db.commit()
        return True
    except (KeyError,ValueError,TypeError):
        return False


def collector_health() -> dict:
    with SessionLocal() as db:
        state = db.get(CollectorState, "ais")
        latest = db.scalar(select(func.max(VesselObservation.observed_at)))
        count = db.scalar(select(func.count()).select_from(VesselObservation)) or 0
    stale = latest is None or (utcnow() - aware(latest)).total_seconds() > settings.ais_stale_minutes * 60
    heartbeat_stale = state is None or (utcnow() - aware(state.updated_at)).total_seconds() > 120
    status = "not_configured" if not settings.aisstream_api_key else "not_started" if state is None else "disconnected" if heartbeat_stale else state.status
    return {"status":status, "fetched":count, "latest_observation":latest,
            "stale":stale, "heartbeat_stale":heartbeat_stale,
            "detail":state.detail if state else "Start the separate AIS collector after configuring a key."}


def activity_summary(now: datetime | None = None) -> dict:
    now = now or utcnow()
    health=collector_health()
    corridors = []
    with SessionLocal() as db:
        for name, bounds in CORRIDORS.items():
            conditions = (
                VesselObservation.corridor == name,
                VesselObservation.observed_at >= now - timedelta(hours=24),
                VesselObservation.observed_at <= now,
            )
            count, unique_count = db.execute(select(func.count(), func.count(func.distinct(VesselObservation.mmsi))).where(*conditions)).one()
            ranked = select(VesselObservation.id,
                func.row_number().over(partition_by=VesselObservation.mmsi,
                    order_by=(VesselObservation.observed_at.desc(), VesselObservation.id.desc())).label("rank")
                ).where(*conditions).subquery()
            recent = db.scalars(select(VesselObservation).join(ranked, VesselObservation.id == ranked.c.id)
                .where(ranked.c.rank == 1).order_by(VesselObservation.observed_at.desc()).limit(100)).all()
            first = db.scalar(select(func.min(VesselObservation.observed_at)).where(VesselObservation.corridor == name))
            profiles={p.mmsi:p.ship_type for p in db.scalars(select(VesselProfile).where(VesselProfile.updated_at>=now-timedelta(days=30))).all()}
            from ..pipeline.vessel_features import corridor_features
            fresh=bool(recent) and (now-aware(recent[0].observed_at)).total_seconds()<=settings.ais_stale_minutes*60 and not health["heartbeat_stale"]
            features=corridor_features(name,now,fresh)
            corridors.append({"id":name, "bounds":bounds, "observations_24h":count,
                "unique_vessels_24h":unique_count,
                "first_observation":first, "latest_observation":recent[0].observed_at if recent else None,
                "baseline_status":features["status"] if first else "no_observations",
                "baseline_target_days":settings.ais_baseline_days,
                "anomaly":features["anomaly"],"features":features,
                "vessels":[{"mmsi":r.mmsi,"name":r.ship_name,"latitude":r.latitude,
                    "longitude":r.longitude,"speed_knots":r.speed_knots,"observed_at":r.observed_at,
                    "vessel_class":"tanker" if 80<=profiles.get(r.mmsi,-1)<=89 else "unknown" if r.mmsi not in profiles else "other",
                    "ship_type":profiles.get(r.mmsi)}
                    for r in recent]})
    return {"health":health, "computed_at":now, "corridors":corridors,
            "scope":"Observed Class A vessel positions; tanker classification uses received static ship type when available, not verified crude cargo or completed transits.",
            "limitation":"Anomalies require a coverage-qualified baseline and current observations. Missing AIS is not evidence of disruption; zero-observation windows are excluded from anomaly scoring."}


async def collect_forever():
    """Run one collector process. API credentials remain on the server."""
    from websockets.asyncio.client import connect
    from websockets.exceptions import WebSocketException
    init_db()
    if not settings.aisstream_api_key:
        set_collector_state("not_configured", "AISSTREAM_API_KEY is missing")
        raise SystemExit("Set AISSTREAM_API_KEY in backend/.env before starting AIS.")
    delay = 1
    try:
        while True:
            try:
                set_collector_state("connecting")
                async with connect(STREAM_URL, compression="deflate", open_timeout=20,
                                   ping_interval=20, ping_timeout=20, max_size=2**20) as socket:
                    await socket.send(json.dumps({"APIKey":settings.aisstream_api_key,
                        "BoundingBoxes":list(CORRIDORS.values()), "FilterMessageTypes":["PositionReport","ShipStaticData"]}))
                    set_collector_state("subscribing")
                    confirmed = False
                    last_heartbeat = utcnow()
                    while True:
                        try:
                            raw = await asyncio.wait_for(socket.recv(), timeout=30 if confirmed else 10)
                        except asyncio.TimeoutError:
                            if not confirmed:
                                raise ValueError("AIS subscription was not confirmed")
                            set_collector_state("connected", "No recent position messages; check coverage separately")
                            continue
                        try:
                            message = json.loads(raw)
                        except (ValueError, TypeError):
                            continue
                        if not isinstance(message, dict):
                            continue
                        if message.get("error") or message.get("Error"):
                            # Never persist provider error text: it can echo credentials.
                            raise ValueError("Provider rejected AIS subscription")
                        if message.get("MessageType") == "SubscriptionConfirmation":
                            confirmed = True
                            set_collector_state("connected")
                            delay = 1
                        await asyncio.to_thread(save_position, message)
                        await asyncio.to_thread(save_profile, message)
                        if (utcnow() - last_heartbeat).total_seconds() >= 30:
                            set_collector_state("connected")
                            last_heartbeat = utcnow()
            except (OSError, WebSocketException, TimeoutError, ValueError):
                set_collector_state("reconnecting", "Connection unavailable; retrying with backoff")
                await asyncio.sleep(delay + random.random())
                delay = min(60, delay * 2)
    finally:
        set_collector_state("stopped")


class AISConnector(BaseConnector):
    """Compatibility boundary; raw positions are not fabricated risk signals."""
    name = "ais"

    def fetch(self, window_hours: int):
        return []


if __name__ == "__main__":
    from ..pipeline.locking import exclusive_job, JobBusy
    try:
        with exclusive_job("ais"):
            asyncio.run(collect_forever())
    except KeyboardInterrupt:
        pass
    except JobBusy as exc:
        raise SystemExit(str(exc)) from exc
