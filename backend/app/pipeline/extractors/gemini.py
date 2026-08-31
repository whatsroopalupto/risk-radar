"""Raw HTTP Gemini extraction adapter with heuristic fallthrough."""
import json, logging
import httpx
from ...config import settings
from ...schemas import RiskExtraction, Signal
from .base import BaseExtractor
from .cache import load, save
from .heuristic import HeuristicExtractor
LOGGER = logging.getLogger(__name__)
class GeminiExtractor(BaseExtractor):
    """Use Gemini only for typed fact extraction, never risk scoring."""
    def __init__(self, api_key: str | None = None) -> None: self.api_key = api_key or settings.gemini_api_key; self.fallback = HeuristicExtractor()
    def extract(self, signals: list[Signal]) -> list[RiskExtraction]:
        """Extract in batches of eight and fall back per failed batch."""
        output: list[RiskExtraction] = []
        for chunk_start in range(0, len(signals), 8):
            chunk = signals[chunk_start:chunk_start+8]; cached = [load(item.signal_id) for item in chunk]
            if all(cached): output.extend(cached); continue
            try:
                values = self._request(chunk)
                for signal, value in zip(chunk, values): save(signal.signal_id, value)
                output.extend(values)
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                LOGGER.warning("gemini extraction failed; heuristic fallback: %s", exc); output.extend(self.fallback.extract(chunk))
        return output
    def _request(self, signals: list[Signal]) -> list[RiskExtraction]:
        payload = [{"title":s.title,"body":s.body or ""} for s in signals]
        prompt = "Return JSON array in input order; each object exactly RiskExtraction fields: is_relevant,event_type,severity,affected_chokepoints,affected_countries,is_speculative,confidence,evidence,extractor. Evidence <=200 chars. " + json.dumps(payload)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
        response = httpx.post(url, params={"key":self.api_key}, json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"responseMimeType":"application/json","temperature":0}}, timeout=20)
        response.raise_for_status(); text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        values = [RiskExtraction.model_validate({**item,"extractor":settings.gemini_model}) for item in json.loads(text)]
        if len(values) != len(signals): raise ValueError("Gemini response count mismatch")
        return values
