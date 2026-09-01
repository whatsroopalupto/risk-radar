from fastapi.testclient import TestClient
from app.main import app
def test_health():
 with TestClient(app) as client: assert client.get("/api/health").status_code==200
def test_graph():
 with TestClient(app) as client: assert client.get("/api/graph").status_code==200
def test_scenarios():
 with TestClient(app) as client:
  ids={s["id"] for s in client.get("/api/scenarios").json()}
  assert {"hormuz_june2025","red_sea_dec2023"}<=ids
def test_replay():
 with TestClient(app) as client: assert client.post("/api/replay/hormuz_june2025").status_code==200
def test_replay_escalates_to_high_band():
 with TestClient(app) as client:
  client.post("/api/replay/hormuz_june2025")
  routes={r["route_id"]:r for r in client.get("/api/risk/routes").json()}
  assert routes["hormuz_west_coast"]["band"]=="high"
def test_ingest_history_after_replay():
 with TestClient(app) as client:
  client.post("/api/replay/hormuz_june2025")
  history=client.get("/api/ingest/history").json()
  assert len(history)>=1 and history[0]["extracted"]>=1
def test_routes_timeseries_has_multiple_points_after_replay():
 with TestClient(app) as client:
  client.post("/api/replay/hormuz_june2025")
  series=client.get("/api/risk/routes/timeseries").json()
  hormuz=next(item for item in series if item["route_id"]=="hormuz_west_coast")
  assert len(hormuz["points"])>=5
def test_red_sea_replay_escalates_red_sea_suez_route():
 with TestClient(app) as client:
  client.post("/api/replay/red_sea_dec2023")
  routes={r["route_id"]:r for r in client.get("/api/risk/routes").json()}
  assert routes["red_sea_suez"]["band"] in ("medium","high")
  assert routes["red_sea_suez"]["composite_score"]>0
