"""Bounded live source diagnostics; report never includes credentials or raw articles."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import httpx
from backend.app.config import settings
from backend.app.connectors.rss import RSSConnector
from backend.app.connectors.gdelt import GDELTConnector
from backend.app.connectors.prices import PriceConnector
from backend.app.pipeline.extractors.gemini import GeminiExtractor
from backend.app.schemas import Signal
from backend.app.db import utcnow

def news(connector):
    try:
        values=connector.fetch(24)
        return {"status":getattr(connector,"last_status","ok"),"articles":len(values),
            "latest_publication":max((v.published_at.isoformat() for v in values),default=None)}
    except Exception as exc:
        return {"status":"unavailable","error_type":type(exc).__name__}

def gemini():
    if not settings.gemini_api_key:
        return {"status":"not_configured"}
    now=utcnow()
    signal=Signal(signal_id="live-model-probe",source_type="news",source_name="test",
        title="Diagnostic example: oil tanker traffic through Hormuz continues",published_at=now,fetched_at=now)
    try:
        result=GeminiExtractor()._request([signal])
        return {"status":"ok","model":settings.gemini_model,"valid_extractions":len(result)}
    except httpx.HTTPStatusError as exc:
        return {"status":"unavailable","http_status":exc.response.status_code,"model":settings.gemini_model}
    except Exception as exc:
        return {"status":"unavailable","error_type":type(exc).__name__,"model":settings.gemini_model}

def price():
    try:
        change=PriceConnector().percent_change_24h()
        return {"status":"ok" if change is not None else "unavailable","change_pct":change}
    except Exception as exc:
        return {"status":"unavailable","error_type":type(exc).__name__}

def main():
    checks={"rss":lambda:news(RSSConnector()),"gdelt":lambda:news(GDELTConnector()),"gemini":gemini,"brent":price}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures={name:executor.submit(function) for name,function in checks.items()}
        report={"checked_at":utcnow().isoformat(),"sources":{name:future.result() for name,future in futures.items()}}
    output=Path("output/verification/live_sources.json")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__": main()
