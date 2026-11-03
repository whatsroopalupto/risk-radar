"""Collect recent GDELT article metadata for historical research.

This script is intentionally isolated from the live production connectors and should
be run manually or via a scheduled maintenance job. It never rewrites the live risk
scoring pipeline and safely degrades when GDELT is unavailable.
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.parse import urlparse

import httpx

LOGGER = logging.getLogger(__name__)
DEFAULT_QUERY_LIST = [
    "\"Strait of Hormuz\" OR \"Hormuz\"",
    "\"Gulf of Oman\"",
    "\"Red Sea\" AND shipping",
    "\"Bab el-Mandeb\"",
    "\"Suez Canal\"",
    "\"crude oil supply disruption\"",
    "\"tanker attacks\"",
    "\"oil infrastructure attacks\"",
]


def normalize_queries(queries: Sequence[str] | str | None) -> list[str]:
    if queries is None:
        return list(DEFAULT_QUERY_LIST)
    if isinstance(queries, str):
        values = [item.strip() for item in queries.split(",") if item.strip()]
        return values or list(DEFAULT_QUERY_LIST)
    values = [str(item).strip() for item in queries if str(item).strip()]
    return values or list(DEFAULT_QUERY_LIST)


def parse_gdelt_response(payload: dict[str, Any] | None, query: str, collection_timestamp: datetime | None = None) -> list[dict[str, str]]:
    """Normalize a GDELT JSON payload into a consistent row format.

    Missing or malformed records are ignored rather than crashing the collection run.
    """

    if not isinstance(payload, dict):
        LOGGER.warning("GDELT payload was not a JSON object for query %r", query)
        return []

    articles = payload.get("articles")
    if not isinstance(articles, list):
        return []

    timestamp = (collection_timestamp or datetime.now(timezone.utc)).isoformat()
    seen_urls: set[str] = set()
    records: list[dict[str, str]] = []

    for article in articles:
        if not isinstance(article, dict):
            continue

        title = str(article.get("title") or "").strip()
        url = str(article.get("url") or article.get("link") or "").strip()
        if not title or not url:
            continue

        domain = str(article.get("domain") or urlparse(url).netloc or "unknown").strip() or "unknown"
        gathered = {
            "title": title,
            "url": url,
            "domain": domain,
            "seendate": str(article.get("seendate") or "").strip(),
            "language": str(article.get("language") or "unknown").strip() or "unknown",
            "source_country": str(article.get("sourcecountry") or article.get("source_country") or "unknown").strip() or "unknown",
            "search_query": query,
            "collection_timestamp": timestamp,
        }

        if gathered["url"] in seen_urls:
            continue
        seen_urls.add(gathered["url"])
        records.append(gathered)

    return records


def write_article_csv(rows: Iterable[dict[str, str]], output_path: str | Path) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "title",
        "url",
        "domain",
        "seendate",
        "language",
        "source_country",
        "search_query",
        "collection_timestamp",
    ]

    incoming = list(rows)
    if not incoming:
        return  # Empty or failed retrieval must never erase the research archive.
    existing = []
    if destination.exists():
        with destination.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != fieldnames:
                raise ValueError("Existing article archive has an incompatible schema")
            existing = list(reader)
    merged = {row["url"]: row for row in existing + incoming}
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in merged.values():
                writer.writerow({field: row.get(field, "") for field in fieldnames})
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def collect_gdelt_articles(
    queries: Sequence[str] | str | None = None,
    max_records: int = 100,
    output_path: str | Path | None = None,
) -> list[dict[str, str]]:
    """Call the GDELT DOC API and persist deduplicated article metadata.

    The function never raises on API failures. Instead it logs the problem and returns
    an empty list or a partial list when the network is unavailable or malformed data
    is received.
    """

    if max_records <= 0:
        LOGGER.info("No GDELT records requested: max_records=%s", max_records)
        return []

    query_list = normalize_queries(queries)
    collected: dict[str, dict[str, str]] = {}
    for query in query_list:
        try:
            response = httpx.get(
                "https://api.gdeltproject.org/api/v2/doc/doc",
                params={
                    "query": query,
                    "mode": "artlist",
                    "format": "json",
                    "maxrecords": min(max_records, 250),
                },
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, httpx.TimeoutException, ValueError, TypeError, KeyError) as exc:
            LOGGER.warning("GDELT query %r failed: %s", query, exc)
            continue

        for item in parse_gdelt_response(payload, query):
            if item["url"] not in collected and len(collected) < max_records:
                collected[item["url"]] = item

    deduped = list(collected.values())[:max_records]
    if output_path is not None:
        write_article_csv(deduped, output_path)
    return deduped


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect recent GDELT article metadata for historical research.")
    parser.add_argument("--queries", nargs="+", default=None, help="One or more GDELT search queries.")
    parser.add_argument("--max-records", type=int, default=100, help="Maximum deduplicated article rows to collect.")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parents[1] / "data" / "historical" / "raw" / "gdelt_articles.csv"),
        help="CSV output path for collected article metadata.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    records = collect_gdelt_articles(args.queries, args.max_records, output_path=args.output)
    LOGGER.info("Collected %s deduplicated GDELT article rows.", len(records))


if __name__ == "__main__":
    main()
