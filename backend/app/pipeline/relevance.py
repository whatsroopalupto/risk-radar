"""Cheap lexical relevance filter that protects extractor quotas."""
from ..schemas import Signal
GEO_TERMS = {"hormuz", "persian gulf", "red sea", "bab el-mandeb", "suez", "gulf of oman", "strait", "iran", "iraq", "saudi", "uae", "kuwait", "qatar", "yemen", "houthi"}
COMMODITY_TERMS = {"oil", "crude", "tanker", "vlcc", "refinery", "petroleum", "shipping", "cargo", "opec", "barrel", "freight"}
def is_relevant(signal: Signal) -> bool:
    """Require both geography and oil/shipping evidence before extraction."""
    text = f"{signal.title} {signal.body or ''}".lower()
    return any(term in text for term in GEO_TERMS) and any(term in text for term in COMMODITY_TERMS)
