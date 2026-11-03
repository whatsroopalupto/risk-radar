"""Optional GDELT connector that degrades on blocked campus networks."""
import hashlib, logging
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
import httpx
from .base import BaseConnector
from ..pipeline.normalize import normalize_title
from ..schemas import Signal
LOGGER = logging.getLogger(__name__)
class GDELTConnector(BaseConnector):
    name = "gdelt"
    def fetch(self, window_hours: int) -> list[Signal]:
        """Return no signals rather than propagating unreachable API errors."""
        try:
            response = httpx.get("https://api.gdeltproject.org/api/v2/doc/doc", params={"query":"(hormuz OR \"red sea\" OR \"bab el mandeb\") (oil OR tanker OR shipping)","mode":"artlist","format":"json","maxrecords":50,"timespan":f"{window_hours}h"}, timeout=20)
            if not response.text.lstrip().startswith("{"): raise ValueError("GDELT returned non-JSON body")
            response.raise_for_status(); fetched = datetime.now(timezone.utc); output=[]
            for article in response.json().get("articles", []):
                title, url = article.get("title","Untitled"), article.get("url"); domain=urlparse(url or "").hostname or "unknown"; ident=hashlib.sha256(f"{normalize_title(title)}|{domain}".encode()).hexdigest()[:16]
                timestamp=article.get("seendate","")
                try:
                    published=datetime.strptime(timestamp,"%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                except (ValueError,TypeError):
                    continue
                if not fetched-timedelta(hours=window_hours)<=published<=fetched+timedelta(minutes=5):
                    continue
                output.append(Signal(signal_id=ident,source_type="news",source_name=domain,title=title,body=None,url=url,published_at=published,fetched_at=fetched,raw=article))
            return output
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            LOGGER.warning("gdelt unavailable: %s",type(exc).__name__)
            raise RuntimeError("GDELT was unavailable or returned an invalid response") from exc
