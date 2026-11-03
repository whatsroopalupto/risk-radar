"""Validate the historical event and source CSV files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.historical.validation import validate_historical_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the historical event dataset and its source register.")
    parser.add_argument(
        "--events",
        default=str(ROOT / "data" / "historical" / "processed" / "historical_events.csv"),
        help="Path to historical_events.csv",
    )
    parser.add_argument(
        "--sources",
        default=str(ROOT / "data" / "historical" / "source_register.csv"),
        help="Path to source_register.csv",
    )
    args = parser.parse_args()

    summary = validate_historical_dataset(args.events, args.sources)
    print(f"Event rows: {summary['event_count']}")
    print(f"Source rows: {summary['source_count']}")
    print(f"Valid: {summary['valid']}")
    if summary["duplicate_checks"]:
        print("Duplicate checks:")
        for name, values in summary["duplicate_checks"].items():
            print(f"  - {name}: {', '.join(values) if values else 'none'}")
    if summary["errors"]:
        print("Errors:")
        for error in summary["errors"]:
            print(f"  - {error}")
    if summary["warnings"]:
        print("Warnings:")
        for warning in summary["warnings"]:
            print(f"  - {warning}")

    return 0 if summary["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
