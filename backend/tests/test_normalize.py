from datetime import datetime,timezone
from app.pipeline.normalize import *
from app.schemas import Signal
def s(i,title): return Signal(signal_id=i,source_type="news",source_name="x",title=title,published_at=datetime.now(timezone.utc),fetched_at=datetime.now(timezone.utc),raw={})
def test_suffix(): assert normalize_title("Oil rises - Reuters")=="oil rises"
def test_exact(): assert len(dedupe([s("a","Oil tanker Hormuz"),s("a","Oil tanker Hormuz")])[0])==1
def test_near(): assert len(dedupe([s("a","Iran oil tanker attack Hormuz"),s("b","Hormuz tanker oil attack Iran")])[0])==1
def test_distinct(): assert len(dedupe([s("a","Iran oil tanker"),s("b","Suez shipping cargo")])[0])==2
