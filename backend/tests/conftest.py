"""Force fully offline, deterministic, isolated test behavior regardless of the developer's local .env.

Both overrides must happen before any test module imports app.config/app.db, since Settings() and the
SQLAlchemy engine are both constructed once at module import time.
"""
import os
import tempfile

os.environ["EXTRACTOR"] = "heuristic"
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir()}/risk_radar_test.db"
