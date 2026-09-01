"""Raw HTTP Gemini extraction adapter with heuristic fallthrough."""
import json, logging, time
import httpx
from ...config import settings
from ...schemas import RiskExtraction, Signal
from .base import BaseExtractor
from .cache import load, save
from .heuristic import HeuristicExtractor
LOGGER = logging.getLogger(__name__)
EVENT_TYPES = "blockade_or_closure, attack_on_vessel, military_strike, port_or_terminal_disruption, sanctions, naval_buildup, diplomatic_escalation, policy_change, other"
CHOKEPOINTS = "hormuz, bab_el_mandeb, suez, malacca, none"
MIN_INTERVAL_SECONDS = 4.0  # Free-tier quotas run roughly 5-15 requests/minute; stay comfortably under that.
class GeminiExtractor(BaseExtractor):
    """Use Gemini only for typed fact extraction, never risk scoring."""
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.gemini_api_key
        self.fallback = HeuristicExtractor()
        self._last_call = 0.0
        self._rate_limited = False  # Once quota is hit, stop spending the run's remaining time on doomed retries.
    def _throttle(self) -> None:
        """A simple sleep-based throttle so batches never arrive faster than the free-tier rate limit allows."""
        elapsed = time.monotonic() - self._last_call
        if elapsed < MIN_INTERVAL_SECONDS: time.sleep(MIN_INTERVAL_SECONDS - elapsed)
        self._last_call = time.monotonic()
    def extract(self, signals: list[Signal]) -> list[RiskExtraction]:
        """Extract in batches of eight; on a schema mismatch retry once with a stricter instruction, then fall back per failed batch."""
        output: list[RiskExtraction] = []
        for chunk_start in range(0, len(signals), 8):
            chunk = signals[chunk_start:chunk_start+8]; cached = [load(item.signal_id) for item in chunk]
            if all(cached): output.extend(cached); continue
            if self._rate_limited: output.extend(self.fallback.extract(chunk)); continue
            self._throttle()
            try:
                values = self._request(chunk, strict=False)
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                if self._is_rate_limit(exc):
                    LOGGER.warning("gemini rate limit reached; using the rule-based fallback for the rest of this run")
                    self._rate_limited = True; output.extend(self.fallback.extract(chunk)); continue
                LOGGER.warning("gemini extraction failed, retrying with a stricter instruction: %s", exc)
                self._throttle()
                try:
                    values = self._request(chunk, strict=True)
                except (httpx.HTTPError, ValueError, KeyError) as exc2:
                    if self._is_rate_limit(exc2): self._rate_limited = True
                    LOGGER.warning("gemini retry failed; heuristic fallback for this batch: %s", exc2)
                    output.extend(self.fallback.extract(chunk)); continue
            for signal, value in zip(chunk, values): save(signal.signal_id, value)
            output.extend(values)
        return output
    @staticmethod
    def _is_rate_limit(exc: Exception) -> bool:
        return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429
    def _request(self, signals: list[Signal], strict: bool = False) -> list[RiskExtraction]:
        payload = [{"title": s.title, "body": s.body or ""} for s in signals]
        schema_note = (
            f"event_type must be exactly one of: {EVENT_TYPES}. "
            "severity and confidence must be JSON numbers between 0.0 and 1.0, never words. "
            f"affected_chokepoints must be a JSON array using only: {CHOKEPOINTS}. "
            "is_relevant and is_speculative must be JSON booleans."
        )
        if strict:
            schema_note += " Your previous response used values outside this exact schema — match it precisely this time, with no extra text or commentary."
        prompt = (
            "Return a JSON array, one object per input item in the same order, with exactly these RiskExtraction "
            "fields: is_relevant, event_type, severity, affected_chokepoints, affected_countries, is_speculative, "
            "confidence, evidence (<=200 chars), extractor. " + schema_note + " " + json.dumps(payload)
        )
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
        response = httpx.post(
            url, params={"key": self.api_key},
            json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0, "thinkingConfig": {"thinkingLevel": "low"}}},
            timeout=60
        )
        response.raise_for_status(); text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        values = [RiskExtraction.model_validate({**item, "extractor": settings.gemini_model}) for item in json.loads(text)]
        if len(values) != len(signals): raise ValueError("Gemini response count mismatch")
        return values
