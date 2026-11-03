from datetime import datetime,timedelta,timezone
from types import SimpleNamespace
import httpx
import pytest
from feedparser import FeedParserDict
from app.config import settings
from app.connectors.rss import RSSConnector
from app.connectors.gdelt import GDELTConnector

def test_rss_window_excludes_old_and_missing_dates(monkeypatch):
    now=datetime.now(timezone.utc)
    entries=[FeedParserDict(title="Hormuz oil shipping",published_parsed=(now-timedelta(hours=age)).timetuple(),link="https://example.org/news") for age in (1,72)]
    entries.append(FeedParserDict(title="Undated oil shipping"))
    monkeypatch.setattr(settings,"rss_queries",["test"])
    monkeypatch.setattr(settings,"rss_feeds",[])
    monkeypatch.setattr("app.connectors.rss.httpx.get",lambda url,**kwargs:httpx.Response(200,content=b"test",request=httpx.Request("GET",url)))
    monkeypatch.setattr("app.connectors.rss.feedparser.parse",lambda data:SimpleNamespace(entries=entries,bozo=False))
    assert len(RSSConnector().fetch(24))==1

def test_gdelt_preserves_observed_news_date_and_failure_status(monkeypatch):
    now=datetime.now(timezone.utc)-timedelta(hours=2)
    def response(url,**kwargs):
        assert kwargs["params"]["timespan"]=="24h"
        return httpx.Response(200,json={"articles":[{"title":"Hormuz oil","url":"https://example.org/a","seendate":now.strftime("%Y%m%dT%H%M%SZ")}]},request=httpx.Request("GET",url))
    monkeypatch.setattr("app.connectors.gdelt.httpx.get",response)
    signal=GDELTConnector().fetch(24)[0]
    assert abs((signal.published_at-now).total_seconds())<1
    monkeypatch.setattr("app.connectors.gdelt.httpx.get",lambda url,**kwargs:httpx.Response(503,text="Unavailable",request=httpx.Request("GET",url)))
    with pytest.raises(RuntimeError):GDELTConnector().fetch(24)
