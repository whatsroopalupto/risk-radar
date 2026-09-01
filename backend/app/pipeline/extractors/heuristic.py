"""Deterministic no-network extraction fallback for reliable demos."""
import re
from ...schemas import RiskExtraction, Signal
from .base import BaseExtractor
RULES = [("blockade_or_closure", ("close the strait","closes the strait","blockade","closure"), .95), ("attack_on_vessel", ("attacked","attack","missile","struck"), .9), ("military_strike", ("airstrike","military strike","bombed"), .85), ("port_or_terminal_disruption", ("terminal disruption","port closed","port disruption"), .75), ("sanctions", ("sanction",), .6), ("naval_buildup", ("naval buildup","warship","naval deployment"), .55), ("diplomatic_escalation", ("escalat","tension","diplomatic"), .35), ("policy_change", ("policy change","ban on imports"), .3)]
# Real headlines spell Bab-el-Mandeb with hyphens, spaces, or "al" instead of "el" — match any of them, not one exact spelling.
CHOKEPOINT_TERMS = {
    "hormuz": ("hormuz",),
    "bab_el_mandeb": ("bab-el-mandeb", "bab el-mandeb", "bab al-mandeb", "bab el mandeb", "bab al mandeb"),
    "suez": ("suez",),
    "malacca": ("malacca",),
}
COUNTRIES = ("iran","iraq","saudi arabia","uae","kuwait","qatar","yemen","india")
SPECULATIVE = re.compile(r"\b(threaten|could|may|warns?|if|considering)\b", re.I)
class HeuristicExtractor(BaseExtractor):
    """Provide transparent baseline extraction whenever an LLM is unavailable."""
    def extract(self, signals: list[Signal]) -> list[RiskExtraction]:
        """Classify headlines using stable rules, preserving input order."""
        return [self._one(signal) for signal in signals]
    def _one(self, signal: Signal) -> RiskExtraction:
        text = f"{signal.title}. {signal.body or ''}"; lower = text.lower(); event, severity, evidence = "other", .15, signal.title[:200]
        for candidate, terms, weight in RULES:
            match = next((term for term in terms if term in lower), None)
            if match: event, severity = candidate, weight; evidence = self._sentence(text, match); break
        chokepoints = [key for key, terms in CHOKEPOINT_TERMS.items() if any(term in lower for term in terms)] or ["none"]
        countries = [country.title() for country in COUNTRIES if country in lower]
        return RiskExtraction(is_relevant=event != "other", event_type=event, severity=severity, affected_chokepoints=chokepoints, affected_countries=countries, is_speculative=bool(SPECULATIVE.search(text)), confidence=.5, evidence=evidence[:200], extractor="heuristic-v1")
    @staticmethod
    def _sentence(text: str, term: str) -> str:
        """Keep evidence limited to the source sentence containing the match."""
        return next((part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if term.lower() in part.lower()), text)
