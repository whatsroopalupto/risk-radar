"""Run one complete live ingestion and retain a credential-free verification summary."""
import json
from pathlib import Path
from backend.app.db import init_db
from backend.app.pipeline.orchestrator import run_cycle

if __name__=="__main__":
    init_db()
    result=run_cycle()
    output=Path("output/verification/live_cycle.json")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(result.model_dump_json(indent=2),encoding="utf-8")
    print(result.model_dump_json(indent=2))
