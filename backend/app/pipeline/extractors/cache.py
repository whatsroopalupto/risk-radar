"""Small disk cache prevents repeat extraction costs in demos."""
import json, logging
from pathlib import Path
from pydantic import ValidationError
from ...schemas import RiskExtraction
LOGGER = logging.getLogger(__name__)
CACHE_DIR = Path(__file__).parents[3] / "data" / "cache"
def load(signal_id: str) -> RiskExtraction | None:
    """Return a cached validated extraction if this input was already processed.

    The cache is a pure performance optimization, never a correctness dependency —
    a corrupt or unreadable entry (e.g. written before UTF-8 was enforced here) must
    degrade to a cache miss and re-extract, not crash the run."""
    path = CACHE_DIR / f"{signal_id}.json"
    if not path.exists(): return None
    try:
        return RiskExtraction.model_validate_json(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, ValidationError, OSError, ValueError) as exc:
        LOGGER.warning("Discarding unreadable cache entry %s: %s", signal_id, exc)
        return None
def save(signal_id: str, value: RiskExtraction) -> None:
    """Persist validated extraction by stable connector signal ID."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True); (CACHE_DIR / f"{signal_id}.json").write_text(value.model_dump_json(), encoding="utf-8")
