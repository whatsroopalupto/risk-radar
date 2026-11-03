"""Force fully offline, deterministic, isolated test behavior regardless of the developer's local .env.

Both overrides must happen before any test module imports app.config/app.db, since Settings() and the
SQLAlchemy engine are both constructed once at module import time.
"""
import os
import tempfile

os.environ["EXTRACTOR"] = "heuristic"
_test_directory = tempfile.TemporaryDirectory(prefix="risk-radar-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_test_directory.name}/risk_radar_test.db"
os.environ["AISSTREAM_API_KEY"] = ""

import pytest
from app.db import Base, engine

@pytest.fixture(autouse=True)
def isolated_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield

def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    _test_directory.cleanup()
