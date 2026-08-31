"""Primary RSS connector with timezone-safe date handling."""
import hashlib, logging
from datetime import datetime, timezone
from urllib.parse import quote_plus, urlparse
import feedparser
from .base import BaseConnector
from ..config import settings
from ..pipeline.normalize import normalize_title
from ..schemas import Signal
LOGGER = logging.getLogger(__name__)
USER_AGENT = "RiskRadarPhase1/1.0"
class RSSConnector(BaseConnector):
    name = "rss"
    def fetch(self, window_hours: int) -> list[Signal]:
        """Fetch configured Google News searches, skipping failed feeds."""
        signals: list[Signal] = []
        feeds = [f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en" for query in settings.rss_queries] + settings.rss_feeds
        for feed in feeds:
            try:
                parsed = feedparser.parse(feed, agent=USER_AGENT, request_headers={"User-Agent":USER_AGENT})
                for entry in parsed.entries: signals.append(self._signal(entry))
            except (OSError, ValueError, AttributeError) as exc: LOGGER.warning("rss feed unavailable %s: %s", feed, exc)
        return signals
    def _signal(self, entry: object) -> Signal:
        fetched = datetime.now(timezone.utc); title = getattr(entry, "title", "Untitled"); url = getattr(entry, "link", None); domain = urlparse(url or "").hostname or "unknown"
        normalized = normalize_title(title); ident = hashlib.sha256(f"{normalized}|{domain}".encode()).hexdigest()[:16]; raw = dict(entry)
        try: published = datetime(*getattr(entry, "published_parsed")[:6]).replace(tzinfo=timezone.utc) if getattr(entry, "published_parsed", None) else fetched
        except (TypeError, ValueError): published = fetched; raw["_date_parse_failed"] = True
        return Signal(signal_id=ident, source_type="news", source_name=domain, title=title, body=getattr(entry,"summary",None), url=url, published_at=published, fetched_at=fetched, raw=raw)
