"""Public PPAC report and EIA country-brief ingestion with explicit periods/units.

These sources establish national context, never refinery procurement shares.
Parsers fail closed when a source changes layout rather than guessing columns.
"""
from io import BytesIO
import hashlib
import re
from urllib.parse import urljoin, urlsplit
import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy import select
from ..db import TradeSnapshot, SessionLocal, utcnow

PPAC_HOME="https://ppac.gov.in/home"
EIA_BRIEF="https://www.eia.gov/international/content/analysis/countries_long/india/"
MONTHS="January February March April May June July August September October November December".split()

def parse_ppac_table(text):
    if "Crude oil, LNG and petroleum products at a glance" not in text:
        raise ValueError("PPAC overview table not found")
    years=sorted(set(re.findall(r"(?<!\d)(20\d{2}-\d{2})(?!\d)",text)))
    month_match=re.search(r"Unit/\s*Base\s+("+"|".join(MONTHS)+r")",text,re.I)
    if len(years)!=3 or not month_match:
        raise ValueError("Unrecognized PPAC period columns")
    def row(pattern):
        match=re.search(pattern+r"\s+((?:\d+(?:\.\d+)?\s+){5}\d+(?:\.\d+)?)",text)
        if not match:
            raise ValueError("Missing six-column PPAC data row")
        return [float(v) for v in match.group(1).split()]
    imports=row(r"(?:^|\n)7\s*\nMMT")
    dependency=row(r"(?:^|\n)10\s+%")
    month=MONTHS.index(month_match.group(1).capitalize())+1
    start_year=int(years[-1][:4])
    current=f"{start_year+(month<4):04d}-{month:02d}"
    periods=[f"FY {years[0]}",f"FY {years[1]}",f"{int(current[:4])-1}-{month:02d}",current,
             f"FY {years[1]} April–{MONTHS[month-1]}",f"FY {years[2]} April–{MONTHS[month-1]}"]
    return [{"metric":"crude_import_quantity","period":period,"value":value,"unit":"million_metric_tonnes","geography":"India","provisional":index>0}
            for index,(period,value) in enumerate(zip(periods,imports))]+[
        {"metric":"crude_import_dependency","period":period,"value":value,"unit":"percent","geography":"India","provisional":index>0}
            for index,(period,value) in enumerate(zip(periods,dependency))]

def fetch_ppac():
    page=httpx.get(PPAC_HOME,timeout=25,follow_redirects=True)
    page.raise_for_status()
    soup=BeautifulSoup(page.text,"html.parser")
    link=next((a.get("href") for a in soup.find_all("a",href=True)
               if "snapshot_of_india" in a["href"].lower() and ".pdf" in a["href"].lower()),None)
    if not link:
        raise ValueError("Public PPAC snapshot link unavailable")
    url=urljoin(PPAC_HOME,link)
    if urlsplit(url).hostname not in ("ppac.gov.in","www.ppac.gov.in"):
        raise ValueError("Unexpected PPAC report host")
    report=httpx.get(url,timeout=45,follow_redirects=True)
    report.raise_for_status()
    if not report.content.startswith(b"%PDF") or len(report.content)>30_000_000:
        raise ValueError("PPAC download unavailable or not a supported public PDF")
    reader=PdfReader(BytesIO(report.content))
    for number,page in enumerate(reader.pages):
        text=page.extract_text()
        if "2. Crude oil, LNG and petroleum products at a glance" in text:
            return {"status":"ok","source_url":url,"source_title":"PPAC Monthly Oil and Gas Snapshot",
                "source_page":number+1,"sha256":hashlib.sha256(report.content).hexdigest(),
                "scope":"National crude imports and consumption-based import dependence; not refinery dependencies",
                "records":parse_ppac_table(text)}
    raise ValueError("PPAC table layout changed")

def parse_eia(html):
    text=" ".join(BeautifulSoup(html,"html.parser").stripped_strings)
    total=re.search(r"India imported ([\d.]+) million b/d of crude oil and condensate in (20\d{2})",text)
    share=re.search(r"Russia was the primary source.*?accounting for about ([\d.]+)%",text)
    update=re.search(r"Last Updated:\s*([A-Za-z]+ \d{1,2}, 20\d{2})",text)
    if not total or not share or not update:
        raise ValueError("EIA country brief layout changed")
    return {"status":"ok","source_url":EIA_BRIEF,"source_title":"EIA Country Analysis Brief: India",
        "published":update.group(1),"scope":"National imports; this annual historical brief is not a live trade feed",
        "records":[{"metric":"crude_condensate_imports","period":total.group(2),"geography":"India","value":float(total.group(1)),"unit":"million_barrels_per_day"},
            {"metric":"supplier_share","period":total.group(2),"geography":"India","supplier":"Russia","value":float(share.group(1)),"unit":"percent"}]}

def fetch_eia():
    response=httpx.get(EIA_BRIEF,timeout=30,follow_redirects=True)
    response.raise_for_status()
    result=parse_eia(response.text)
    result["sha256"]=hashlib.sha256(response.content).hexdigest()
    return result

def refresh_trade():
    results={}
    for name,function in (("ppac",fetch_ppac),("eia",fetch_eia)):
        try:
            payload=function()
        except (httpx.HTTPError,ValueError,KeyError,TypeError,PdfReadError) as exc:
            payload={"status":"unavailable","error":type(exc).__name__,"records":[],
                "notice":"Source could not be parsed; no numbers were inferred. Last successful snapshot remains available."}
        with SessionLocal() as db:
            db.add(TradeSnapshot(provider=name,retrieved_at=utcnow(),payload=payload))
            db.commit()
        results[name]=payload["status"]
    return results

def trade_summary():
    sources=[]
    with SessionLocal() as db:
        for name in ("ppac","eia"):
            records=db.scalars(select(TradeSnapshot).where(TradeSnapshot.provider==name).order_by(TradeSnapshot.id.desc())).all()
            latest=records[0] if records else None
            good=next((record for record in records if record.payload.get("status")=="ok"),None)
            sources.append({"provider":name,"latest_status":latest.payload["status"] if latest else "not_fetched",
                "last_attempt":latest.retrieved_at if latest else None,"retrieved_at":good.retrieved_at if good else None,
                "snapshot":good.payload if good else None,"serving_previous_snapshot":bool(good and latest.id!=good.id)})
    return {"sources":sources,"limitation":"National statistics do not identify refinery-specific supplier/route dependencies. Units and periods must not be combined without conversion."}

if __name__=="__main__":
    from ..db import init_db
    init_db()
    print(refresh_trade())
