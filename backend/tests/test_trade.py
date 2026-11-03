import pytest
from app.connectors.trade import parse_ppac_table,parse_eia,refresh_trade,trade_summary

PPAC="""2025-26 (P) 2026-27 (P)
7
MMT 243.2 246.6 20.3 21.7 121.8 122.7
10 % 88.3 88.7 87.8 88.9 88.3 88.1
2. Crude oil, LNG and petroleum products at a glance
Details Unit/ Base September April-September2024-25
"""

def test_ppac_columns_keep_month_and_fiscal_year_separate():
    records=parse_ppac_table(PPAC)
    assert records[1]["period"]=="FY 2025-26" and records[1]["value"]==246.6
    assert records[3]["period"]=="2026-09" and records[3]["value"]==21.7
    assert records[5]["period"]=="FY 2026-27 April–September" and records[5]["value"]==122.7
    assert records[9]["value"]==88.9

def test_changed_layout_is_not_guessed():
    with pytest.raises(ValueError): parse_ppac_table(PPAC.replace("MMT", "USD"))
    with pytest.raises(ValueError): parse_eia("No recognized country data")

def test_failed_refresh_keeps_previous_source_snapshot(monkeypatch):
    good={"status":"ok","records":[{"metric":"test","value":1}],"source_url":"https://ppac.gov.in"}
    monkeypatch.setattr("app.connectors.trade.fetch_ppac",lambda:good)
    monkeypatch.setattr("app.connectors.trade.fetch_eia",lambda:good)
    refresh_trade()
    def fail(): raise ValueError("Changed layout")
    monkeypatch.setattr("app.connectors.trade.fetch_ppac",fail)
    refresh_trade()
    ppac=trade_summary()["sources"][0]
    assert ppac["latest_status"]=="unavailable" and ppac["serving_previous_snapshot"]
    assert ppac["snapshot"]["records"][0]["value"]==1
