from fastapi.testclient import TestClient
from app.main import app
def test_health():
 with TestClient(app) as client: assert client.get("/api/health").status_code==200
def test_graph():
 with TestClient(app) as client: assert client.get("/api/graph").status_code==200
def test_scenarios():
 with TestClient(app) as client: assert client.get("/api/scenarios").status_code==200
def test_replay():
 with TestClient(app) as client: assert client.post("/api/replay/hormuz_june2025").status_code==200
