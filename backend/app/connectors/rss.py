"""Primary RSS connector with timezone-safe date handling."""
import hashlib, logging
from datetime import datetime, timezone
from urllib.parse import quote_plus, urlparse
import feedparser
import httpx
from .base import BaseConnector
from ..config import settings
from ..pipeline.normalize import normalize_title
from ..schemas import Signal
LOGGER = logging.getLogger(__name__)
USER_AGENT = "RiskRadarPhase1/1.0"
FEED_TIMEOUT_SECONDS = 20
class RSSConnector(BaseConnector):
    name = "rss"
    def fetch(self, window_hours: int) -> list[Signal]:
        """Fetch configured Google News searches, skipping failed feeds."""
        signals: list[Signal] = []
        feeds = [f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en" for query in settings.rss_queries] + settings.rss_feeds
        for feed in feeds:
            try:
                # feedparser.parse(url) has no enforced request timeout; fetch with httpx (which does) and hand it raw bytes instead.
                response = httpx.get(feed, headers={"User-Agent": USER_AGENT}, timeout=FEED_TIMEOUT_SECONDS, follow_redirects=True)
                response.raise_for_status()
                parsed = feedparser.parse(response.content)
                for entry in parsed.entries: signals.append(self._signal(entry))
            except (OSError, ValueError, AttributeError, httpx.HTTPError) as exc: LOGGER.warning("rss feed unavailable %s: %s", feed, exc)
        return signals
    def _signal(self, entry: object) -> Signal:
        fetched = datetime.now(timezone.utc)
        title = getattr(entry, "title", "Untitled")
        url = getattr(entry, "link", None)
        domain = "unknown"
        source_obj = getattr(entry, "source", None)
        if isinstance(source_obj, dict):
            src_href = source_obj.get("href")
            if src_href:
                domain = urlparse(src_href).hostname or "unknown"
        if domain == "unknown" or domain == "news.google.com":
            domain = urlparse(url or "").hostname or "unknown"

        normalized = normalize_title(title)
        ident = hashlib.sha256(f"{normalized}|{domain}".encode()).hexdigest()[:16]
        raw = dict(entry)

        published = fetched
        pub_parsed = getattr(entry, "published_parsed", None)
        if pub_parsed:
            try:
                published = datetime(*pub_parsed[:6]).replace(tzinfo=timezone.utc)
            except (TypeError, ValueError) as exc:
                LOGGER.warning("Failed to parse RSS published_parsed date for '%s': %s. Falling back to fetched_at.", title, exc)
                published = fetched
                raw["_date_parse_failed"] = True
        else:
            published = fetched

        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)

        return Signal(signal_id=ident, source_type="news", source_name=domain, title=title, body=getattr(entry,"summary",None), url=url, published_at=published, fetched_at=fetched, raw=raw)

