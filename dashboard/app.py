"""Single-page Phase 1 analyst dashboard; communicates only via api_client."""
import pandas as pd
import streamlit as st
import api_client
from components import risk_badge
st.set_page_config(page_title="Geopolitical Risk Radar",layout="wide")
@st.cache_data(ttl=60)
def read(path:str): return api_client.get(path)
try: health=read("/api/health")
except Exception:
    st.error(f"Backend unavailable at {api_client.API_BASE_URL}. Start it with: uvicorn app.main:app --reload"); st.stop()
st.title("Geopolitical Risk Radar")
st.caption(f"Extractor: {health['extractor']} | Stored assessments: {health['db_counts']['assessments']}")
st.header("Controls")
hours=st.selectbox("Ingestion window (hours)",[6,12,24,48],index=2)
if st.button("Run ingestion"):
    with st.spinner("Fetching and scoring sources..."): st.success(f"Run complete: {api_client.post('/api/ingest/run',{'window_hours':hours})['extracted']} extracted"); st.cache_data.clear()
scenarios=read("/api/scenarios")
if scenarios and st.button("Replay Hormuz June 2025 scenario"): api_client.post("/api/replay/hormuz_june2025"); st.success("Scenario replay completed")
if health['db_counts']['assessments']==0: st.info("No signals have been ingested yet. Run ingestion to distinguish data absence from calm conditions.")
st.header("Route risk")
for route in read("/api/risk/routes"):
    col=st.container(); col.subheader(route['name']); risk_badge(route['composite_score'],route['band']); col.caption(f"Contributing signals: {len(route['contributing_signal_ids'])}")
st.header("Refinery exposure")
refineries=read("/api/risk/refineries"); st.dataframe(pd.DataFrame([{**{k:v for k,v in item.items() if k!='contributions'},'top contributing route':item['contributions'][0]['route_id'] if item['contributions'] else ''} for item in refineries]))
st.header("Signal feed")
for signal in read("/api/signals"):
    st.subheader(signal['signal_id']); st.write(f"{signal['extraction']['event_type']} — Evidence: {signal['extraction']['evidence']}"); risk_badge(signal['final_score']*100,signal['band'])
    with st.expander("Score breakdown"): st.json(signal['component_scores']); st.caption(f"Extractor: {signal['extraction']['extractor']}")
st.header("Supply chain graph")
graph=read("/api/graph")
st.graphviz_chart("digraph supply {"+";".join(f'\"{edge["source"]}\" -> \"{edge["target"]}\"' for edge in graph["edges"])+"}")
st.dataframe(pd.DataFrame(graph['edges'])); st.caption("The edge table is the accessible equivalent of the topology diagram.")
st.header("About")
st.write("Phase 1 is a local walking skeleton. AIS, learned credibility, maps, and production deployment are deliberately deferred.")
