"""Force fully offline, deterministic, isolated test behavior regardless of the developer's local .env.

Both overrides must happen before any test module imports app.config/app.db, since Settings() and the
SQLAlchemy engine are both constructed once at module import time.
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ["EXTRACTOR"] = "heuristic"
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir()}/risk_radar_test.db"
