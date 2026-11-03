"""Rebuild the small demo evaluation and link cases to the research register.

No network calls, generated labels, threshold tuning, or live database mutations.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from backend.app.evaluation import LabelledCase, evaluate
from backend.app.historical.validation import validate_historical_dataset

ROOT = Path(__file__).resolve().parents[1]
EVENT_LINKS = {
    "redsea_shipping_crisis_2023_2024": "HIST-2023-11-19",
    "hormuz_june_2025_tensions": "HIST-2025-06-13",
}


def main():
    events = ROOT / "data/historical/processed/historical_events.csv"
    sources = ROOT / "data/historical/source_register.csv"
    audit = validate_historical_dataset(events, sources)
    if not audit["valid"]:
        raise SystemExit("Historical register failed structural validation: " + "; ".join(audit["errors"]))
    dataset = ROOT / "backend/data/evaluation/pilot_cases.json"
    cases = [LabelledCase.model_validate(row) for row in json.loads(dataset.read_text(encoding="utf-8"))]
    report = evaluate(cases)
    report["dataset_sha256"] = hashlib.sha256(dataset.read_bytes()).hexdigest()
    report["evaluated_at"] = datetime.now(timezone.utc).isoformat()
    report["research_register_sha256"] = hashlib.sha256(events.read_bytes() + sources.read_bytes()).hexdigest()
    report["research_register_audit"] = audit
    for case in report["cases"]:
        case["research_event_id"] = EVENT_LINKS[case["event_id"]]
    report["limitations"].append("Research event links supply context only; CSV risk labels are not converted into disruption ground truth. Only the separately source-reviewed pilot windows are scored.")
    target = ROOT / "output/evaluation/pilot_heuristic.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Register: {audit['event_count']} events, {audit['source_count']} sources; {len(audit['warnings'])} review requirements")
    print(f"Pilot: {report['sample_size']} windows; {report['metrics']}")


if __name__ == "__main__":
    main()
