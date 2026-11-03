"""Validation helpers for the historical event research dataset.

These checks are intentionally strict and descriptive so invalid rows are surfaced
without silently rewriting the CSV files.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

VALID_RISK_LABELS = {"LOW", "MEDIUM", "HIGH"}
VALID_SEVERITY_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
EVENT_COLUMNS = [
    "event_id",
    "event_name",
    "event_date",
    "event_end_date",
    "region",
    "affected_route",
    "event_type",
    "severity",
    "route_risk_label",
    "india_impact",
    "india_impact_evidence",
    "evidence_confidence",
    "label_rationale",
    "source_ids",
    "review_status",
]
SOURCE_COLUMNS = [
    "source_id",
    "event_id",
    "source_name",
    "source_type",
    "publisher",
    "publication_date",
    "URL",
    "claim_supported",
    "credibility_level",
    "verification_notes",
]


def _read_csv_rows(path: str | Path, sample_rows: Iterable[dict[str, str]] | None = None) -> list[dict[str, str]]:
    if sample_rows is not None:
        return [dict(row) for row in sample_rows]
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def _ensure_required_columns(rows: list[dict[str, str]], required: list[str], label: str) -> list[str]:
    errors: list[str] = []
    if not rows:
        return [f"{label}: CSV is empty."]
    missing = [column for column in required if column not in rows[0]]
    if missing:
        errors.append(f"{label}: missing required columns: {', '.join(missing)}")
    return errors


def _is_valid_date(value: str | None) -> bool:
    if not value or not isinstance(value, str):
        return False
    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        return False
    year, month, day = value.split("-")
    if not year.isdigit() or not month.isdigit() or not day.isdigit():
        return False
    try:
        import datetime as dt

        dt.date(int(year), int(month), int(day))
    except ValueError:
        return False
    return True


def _is_valid_url(value: str | None) -> bool:
    if not value or not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return bool(parsed.scheme in {"http", "https"} and parsed.netloc)


def _duplicate_ids(rows: list[dict[str, str]], key_field: str) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for row in rows:
        value = (row.get(key_field) or "").strip()
        if not value:
            continue
        if value in seen:
            duplicates.append(value)
        else:
            seen.add(value)
    return sorted(set(duplicates))


def validate_historical_dataset(
    events_path: str | Path,
    source_register_path: str | Path,
    sample_rows: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Validate the historical event and source datasets.

    If `sample_rows` is supplied, it bypasses file reads and is used for unit coverage
    of duplicate detection and schema edge cases without altering project data files.
    """

    errors: list[str] = []
    warnings: list[str] = []
    duplicate_checks: dict[str, list[str]] = {}

    event_rows = _read_csv_rows(events_path, sample_rows) if sample_rows is not None else _read_csv_rows(events_path)
    source_rows = _read_csv_rows(source_register_path) if sample_rows is None else []

    errors.extend(_ensure_required_columns(event_rows, EVENT_COLUMNS, "historical_events.csv"))
    if not sample_rows:
        errors.extend(_ensure_required_columns(_read_csv_rows(source_register_path), SOURCE_COLUMNS, "source_register.csv"))
        source_rows = _read_csv_rows(source_register_path)

    if "event_id" in (event_rows[0].keys() if event_rows else []) and event_rows:
        duplicate_event_ids = _duplicate_ids(event_rows, "event_id")
        if duplicate_event_ids:
            duplicate_checks["duplicate_event_id"] = duplicate_event_ids
            errors.append(f"historical_events.csv: duplicate event IDs found: {', '.join(duplicate_event_ids)}")

    if source_rows and "source_id" in source_rows[0]:
        duplicate_source_ids = _duplicate_ids(source_rows, "source_id")
        if duplicate_source_ids:
            duplicate_checks["duplicate_source_id"] = duplicate_source_ids
            errors.append(f"source_register.csv: duplicate source IDs found: {', '.join(duplicate_source_ids)}")

    valid_labels = {label.upper() for label in VALID_RISK_LABELS}
    valid_severity = {label.upper() for label in VALID_SEVERITY_LEVELS}
    for index, row in enumerate(event_rows, start=2):
        for field in ["event_id", "event_name", "event_date", "region", "affected_route", "event_type", "severity", "route_risk_label", "india_impact", "india_impact_evidence", "evidence_confidence", "label_rationale", "source_ids", "review_status"]:
            if not str(row.get(field, "") or "").strip():
                errors.append(f"historical_events.csv row {index}: missing required value in '{field}'")
        if row.get("event_date") and not _is_valid_date(row.get("event_date")):
            errors.append(f"historical_events.csv row {index}: invalid event_date '{row.get('event_date')}'")
        if row.get("event_end_date") and not _is_valid_date(row.get("event_end_date")):
            errors.append(f"historical_events.csv row {index}: invalid event_end_date '{row.get('event_end_date')}'")
        if row.get("route_risk_label", "").upper() not in valid_labels:
            errors.append(f"historical_events.csv row {index}: invalid route_risk_label '{row.get('route_risk_label')}'")
        if row.get("severity", "").upper() not in valid_severity:
            errors.append(f"historical_events.csv row {index}: invalid severity '{row.get('severity')}'")
        if row.get("evidence_confidence", "").upper() not in valid_labels:
            errors.append(f"historical_events.csv row {index}: invalid evidence_confidence '{row.get('evidence_confidence')}'")

    for index, row in enumerate(source_rows, start=2):
        for field in ["source_id", "event_id", "source_name", "source_type", "publisher", "publication_date", "URL", "claim_supported", "credibility_level", "verification_notes"]:
            if not str(row.get(field, "") or "").strip():
                errors.append(f"source_register.csv row {index}: missing required value in '{field}'")
        if row.get("publication_date") and not _is_valid_date(row.get("publication_date")):
            errors.append(f"source_register.csv row {index}: invalid publication_date '{row.get('publication_date')}'")
        if row.get("URL") and not _is_valid_url(row.get("URL")):
            errors.append(f"source_register.csv row {index}: invalid URL '{row.get('URL')}'")

    if event_rows and source_rows:
        source_ids = {str(row.get("source_id", "")).strip() for row in source_rows if str(row.get("source_id", "")).strip()}
        for row in event_rows:
            event_source_ids = [value.strip() for value in str(row.get("source_ids", "") or "").split(";") if value.strip()]
            missing = [value for value in event_source_ids if value not in source_ids]
            if missing:
                errors.append(f"historical_events.csv row {row.get('event_id', '?')}: source IDs not registered: {', '.join(missing)}")

    summary = {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "event_count": len(event_rows),
        "source_count": len(source_rows),
        "duplicate_checks": duplicate_checks,
    }
    return summary


def validate_historical_data(
    events_path: str | Path,
    source_register_path: str | Path,
    sample_rows: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Backward-compatible alias used by CLI scripts and tests."""

    return validate_historical_dataset(events_path, source_register_path, sample_rows=sample_rows)
