"""Small disk cache prevents repeat extraction costs in demos."""
import json
from pathlib import Path
from ...schemas import RiskExtraction
CACHE_DIR = Path(__file__).parents[3] / "data" / "cache"
def load(signal_id: str) -> RiskExtraction | None:
    """Return a cached validated extraction if this input was already processed."""
    path = CACHE_DIR / f"{signal_id}.json"
    return RiskExtraction.model_validate_json(path.read_text()) if path.exists() else None
def save(signal_id: str, value: RiskExtraction) -> None:
    """Persist validated extraction by stable connector signal ID."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True); (CACHE_DIR / f"{signal_id}.json").write_text(value.model_dump_json())
