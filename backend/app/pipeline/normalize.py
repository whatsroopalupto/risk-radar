"""Canonical title processing prevents connector-specific duplicate IDs."""
import re
from collections.abc import Iterable
from ..schemas import Signal

PUNCTUATION = re.compile(r"[^\w\s]")
PUBLISHER_SUFFIX = re.compile(r"\s+-\s+[^-]+$")

def normalize_title(title: str) -> str:
    """Normalize headline text before hashing or similarity comparison."""
    return " ".join(PUNCTUATION.sub("", PUBLISHER_SUFFIX.sub("", title).lower()).split())

def token_jaccard(left: str, right: str) -> float:
    """Compare title token sets to collapse syndicated wire copies."""
    a, b = set(normalize_title(left).split()), set(normalize_title(right).split())
    return len(a & b) / len(a | b) if a or b else 1.0

def dedupe(signals: Iterable[Signal], prior_titles: Iterable[str] = ()) -> tuple[list[Signal], int]:
    """Remove exact IDs and near-title duplicates without external state."""
    seen_ids: set[str] = set(); titles = list(prior_titles)[-500:]; kept: list[Signal] = []; removed = 0
    for signal in signals:
        if signal.signal_id in seen_ids or any(token_jaccard(signal.title, title) >= .85 for title in titles[-500:]):
            removed += 1; continue
        seen_ids.add(signal.signal_id); titles.append(signal.title); kept.append(signal)
    return kept, removed
