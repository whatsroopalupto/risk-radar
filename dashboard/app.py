"""Single-page analyst dashboard; communicates only via api_client."""
import pandas as pd
import streamlit as st
import api_client
from components import (
    render_credibility_chart,
    render_event_type_chart,
    render_extractor_mix_chart,
    render_kpi_card,
    render_refinery_chart,
    render_route_chart,
    render_route_timeseries_chart,
    render_run_history_table,
    render_severity_confidence_scatter,
    render_signal_card,
    render_status_strip,
    risk_badge
)

st.set_page_config(
    page_title="Geopolitical Risk Radar — India Crude Supply Chain",
    layout="wide"
)

# Serif headings read as an analyst report rather than a generic app template; body text stays plain sans.
st.markdown(
    """
    <style>
    header[data-testid="stHeader"] { display: none; }
    .main .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    h1, h2, h3 { font-family: Georgia, 'Iowan Old Style', 'Times New Roman', serif; font-weight: 700; letter-spacing: -0.01em; }
    /* Streamlit auto-adds a hover-only anchor icon beside every heading that just rewrites the URL hash —
       with no visible in-page effect, it reads as a broken/dead link. Hide it everywhere. */
    [data-testid="stHeaderActionElements"] { display: none; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { border-radius: 4px; padding: 8px 16px; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True
)

@st.cache_data(ttl=60)
def read(path: str):
    return api_client.get(path)

try:
    health = read("/api/health")
except Exception:
    st.error(
        f"Backend service unavailable at **{api_client.API_BASE_URL}**. "
        "Please ensure the backend is running with: `uvicorn app.main:app --reload`"
    )
    st.stop()

# Header & Subtitle
st.title("Geopolitical Risk Radar")
st.caption("Early-Warning & Decision Support System for India's Crude-Oil Supply Chain")
render_status_strip(health)

# Fetch key dataset
routes_data = read("/api/risk/routes")
refineries_data = read("/api/risk/refineries")
signals_data = read("/api/signals")
timeseries_data = read("/api/risk/routes/timeseries")
run_history = read("/api/ingest/history")
scenarios = read("/api/scenarios")
scenario_by_id = {s["id"]: s for s in scenarios}
loaded_scenario_id = run_history[0].get("scenario_id") if run_history else None
loaded_scenario_label = scenario_by_id.get(loaded_scenario_id, {}).get("label", "a saved scenario") if loaded_scenario_id else None

# Calculate summary KPI metrics
total_signals = len(signals_data)
high_routes = [r for r in routes_data if r.get("band") == "high"]
peak_route = max(routes_data, key=lambda x: x["composite_score"]) if routes_data else None
max_refinery = max(refineries_data, key=lambda x: x["exposure_score"]) if refineries_data else None
llm_classified = sum(1 for s in signals_data if "gemini" in s.get("extraction", {}).get("extractor", "").lower())
llm_pct = (llm_classified / total_signals * 100.0) if total_signals else 0.0

# Render Executive Summary KPI Row
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    render_kpi_card(
        "Highest Route Risk",
        f"{peak_route['composite_score']:.1f} / 100" if peak_route and total_signals > 0 else "0.0 / 100",
        peak_route['name'] if peak_route and total_signals > 0 else "No active risk",
        peak_route['band'] if peak_route and total_signals > 0 else "low",
        "The highest composite score across the four monitored supply routes. Composite score blends a "
        "noisy-OR aggregation of scored news signals for that route (75%) with Brent 24-hour price movement "
        "as corroboration (25%), applied only when the route already has news evidence."
    )

with kpi2:
    render_kpi_card(
        "Peak Refinery Exposure",
        f"{max_refinery['exposure_score']:.1f} / 100" if max_refinery and total_signals > 0 else "0.0 / 100",
        f"{max_refinery['name']} ({max_refinery['operator']})" if max_refinery and total_signals > 0 else "No exposure",
        max_refinery['band'] if max_refinery and total_signals > 0 else "low",
        "The highest exposure score across the monitored Indian refineries. Exposure is the sum, over each "
        "refinery's supplying routes, of that route's composite risk score weighted by the refinery's "
        "dependency share on that route."
    )

with kpi3:
    render_kpi_card(
        "Ingested Risk Signals",
        str(total_signals),
        f"Stored in database: {health['db_counts']['assessments']}",
        "medium" if total_signals > 0 else "low",
        "The number of news signals currently scored and stored for the active view — a live ingestion run "
        "or a replayed scenario. Each one passed the relevance prefilter and was classified by the active "
        "extractor before scoring."
    )

with kpi4:
    render_kpi_card(
        "High-risk routes",
        str(len(high_routes)) if total_signals > 0 else "0",
        f"{len(routes_data)} supply routes monitored",
        "high" if high_routes else "low",
        "Routes whose composite score has crossed the high-risk threshold. Bands are: Low below 30, "
        "Medium 30 to 65, High 65 and above."
    )

with kpi5:
    render_kpi_card(
        "AI-Classified Share",
        f"{llm_pct:.0f}%" if total_signals > 0 else "N/A",
        f"{llm_classified}/{total_signals} headlines" if total_signals > 0 else "No headlines classified yet",
        "medium" if llm_classified else "low",
        "The share of currently loaded headlines read by the AI-based classifier rather than the rule-based "
        "fallback. The system always keeps a working rule-based classifier available, so this can read 0% "
        "while the AI-based classifier is inactive, with no loss of monitoring coverage."
    )

# Persistent ingestion funnel, sourced from the run log rather than ephemeral session state
if run_history:
    latest = run_history[0]
    per_src = latest.get("per_source", {})
    fetched = sum(src.get("fetched", 0) for src in per_src.values() if isinstance(src, dict))
    deduped = latest.get("deduped", 0)
    after_dedupe = max(0, fetched - deduped)
    extracted = latest.get("extracted", 0)
    is_replay = "fixture" in per_src
    source_badge_color = "#8A5A00" if is_replay else "#0B7A46"
    source_badge_bg = "#FCEFD9" if is_replay else "#E6F4F1"
    source_badge_text = f"REPLAY: {loaded_scenario_label.upper()}" if is_replay and loaded_scenario_label else ("REPLAY SCENARIO" if is_replay else "LIVE DATA")

    with st.container(border=True):
        f_col, p_col = st.columns([5, 1])
        with f_col:
            st.markdown(
                f"<div style='padding-top:0.3rem;'>"
                f"<span style='background:{source_badge_bg};color:{source_badge_color};font-size:0.72rem;font-weight:700;"
                f"padding:2px 8px;border-radius:3px;letter-spacing:0.03em;margin-right:10px;'>{source_badge_text}</span>"
                f"<span style='color:#6B6F76;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.04em;'>Latest run funnel</span> &nbsp;&nbsp;"
                f"<b>{fetched}</b> fetched &nbsp;→&nbsp; <b>{after_dedupe}</b> after dedupe &nbsp;→&nbsp; <b>{extracted}</b> extracted &amp; scored"
                f"</div>",
                unsafe_allow_html=True
            )
        with p_col:
            with st.popover("Details", width='stretch'):
                if is_replay:
                    st.write(
                        f"**This is the replayed {loaded_scenario_label or 'saved'} scenario** — a fixed, saved set of headlines, "
                        "not current news. Every number on this page right now reflects that fixture, not today."
                    )
                else:
                    st.write(
                        "**This is a live ingestion run** — real headlines fetched just now. Every number on "
                        "this page reflects whatever is genuinely happening right now for the monitored search terms."
                    )
                st.write("**Fetched** — raw items returned by every enabled connector before any filtering.")
                st.write("**After dedupe** — remaining items once exact and near-duplicate stories (the same wire story picked up by many outlets) are collapsed.")
                st.write("**Extracted & scored** — items that passed the relevance prefilter, were classified into structured risk facts, and scored deterministically.")

# Empty state prompt when database is fresh / zero signals ingested
if total_signals == 0:
    st.warning(
        "No risk signals ingested yet. Click **Run Live Ingestion**, or pick a scenario and click "
        "**Replay Selected Scenario**, under Simulation Controls to ingest news events and calculate risk scores."
    )

st.markdown("---")

# Main Section Tab Navigation
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Route Risk & Trend",
    "Intelligence Analytics",
    "Refinery Exposure",
    "Signal Feed",
    "Ingestion History",
    "Graph & About"
])

# ---------------------------------------------------------
# TAB 1: ROUTE RISK & TREND
# ---------------------------------------------------------
with tab1:
    c_left, c_right = st.columns([2, 1])

    with c_left:
        st.subheader("Route Risk Comparison")
        st.caption("Monitored oil supply routes feeding Indian refineries via key maritime chokepoints.")
        render_route_chart(routes_data)

    with c_right:
        st.subheader("Simulation Controls")
        st.markdown("Run live news ingestion or replay historical escalation scenarios:")

        hours = st.selectbox("Live RSS Ingestion Window", [6, 12, 24, 48], index=2)
        if st.button("Run Live Ingestion", width='stretch'):
            with st.spinner("Fetching RSS feeds and reading each headline — this can take a minute or more while the AI classifier is active..."):
                try:
                    res = api_client.post("/api/ingest/run", {"window_hours": hours})
                except Exception as exc:
                    st.error(api_client.describe_error(exc))
                else:
                    st.success(f"Ingestion complete. Extracted {res.get('extracted', 0)} new signals.")
                    st.cache_data.clear()
                    st.rerun()

        st.markdown("---")
        if scenarios:
            selected_id = st.selectbox(
                "Scenario", options=list(scenario_by_id.keys()),
                format_func=lambda sid: scenario_by_id[sid]["label"]
            )
            if scenario_by_id[selected_id]["description"]:
                st.caption(scenario_by_id[selected_id]["description"])
            if selected_id != loaded_scenario_id:
                currently_shown = loaded_scenario_label if loaded_scenario_id else "live ingestion results"
                st.caption(
                    f"Selecting a scenario does not load it by itself — the page is currently showing "
                    f"**{currently_shown}**. Click Replay Selected Scenario below to load **{scenario_by_id[selected_id]['label']}**."
                )
            if st.button("Replay Selected Scenario", width='stretch'):
                with st.spinner(f"Replaying {scenario_by_id[selected_id]['label']}..."):
                    try:
                        res = api_client.post(f"/api/replay/{selected_id}")
                    except Exception as exc:
                        st.error(api_client.describe_error(exc))
                    else:
                        st.success(f"{scenario_by_id[selected_id]['label']} replayed.")
                        st.cache_data.clear()
                        st.rerun()

    st.markdown("---")
    st.subheader("Risk Trend Over Time")
    st.caption(
        "Cumulative-to-date noisy-OR of news signals per route, day by day, computed from whatever is "
        "currently loaded (a live ingestion window or a multi-day replay) — the final point matches the "
        "route's current news score above. Market corroboration is not back-applied to historical days, "
        "so this is the news-only risk signal in isolation."
    )
    render_route_timeseries_chart(timeseries_data)

    st.markdown("---")
    st.subheader("Route Details & Contributing Signal Count")
    r_cols = st.columns(len(routes_data) if routes_data else 1)
    for idx, route in enumerate(routes_data):
        with r_cols[idx % len(r_cols)]:
            st.markdown(f"### {route['name']}")
            risk_badge(route['composite_score'], route['band'])
            st.caption(f"Chokepoints: {', '.join(route['chokepoints']) or 'None'}")
            st.caption(f"Contributing Signals: **{len(route['contributing_signal_ids'])}**")
            st.caption(f"News Score: `{route['news_score']:.3f}` | Market Score: `{route['market_score']:.3f}`")

# ---------------------------------------------------------
# TAB 2: INTELLIGENCE ANALYTICS
# ---------------------------------------------------------
with tab2:
    st.subheader("What the Extraction Pipeline Actually Produced")
    st.caption(
        "Every chart below is aggregated directly from structured RiskExtraction output "
        "(event type, severity, confidence, extractor, credibility tier) — not restated headlines."
    )

    if total_signals == 0:
        st.info("No extraction data yet. Run ingestion or replay a scenario from the Route Risk tab.")
    else:
        a_col1, a_col2 = st.columns(2)
        with a_col1:
            st.markdown("#### Event Type Distribution")
            render_event_type_chart(signals_data)
        with a_col2:
            st.markdown("#### Extractor Provenance (LLM vs Heuristic)")
            render_extractor_mix_chart(signals_data)

        b_col1, b_col2 = st.columns(2)
        with b_col1:
            st.markdown("#### Severity vs Confidence")
            render_severity_confidence_scatter(signals_data)
        with b_col2:
            st.markdown("#### Source Credibility Tier Distribution")
            render_credibility_chart(signals_data)

# ---------------------------------------------------------
# TAB 3: REFINERY EXPOSURE ANALYSIS
# ---------------------------------------------------------
with tab3:
    st.subheader("Indian Refinery Exposure Ranking")
    st.caption("Downstream risk calculated by propagating route disruptions through NetworkX supply chain topology.")

    c_chart, c_table = st.columns([1, 1])

    with c_chart:
        render_refinery_chart(refineries_data)

    with c_table:
        st.subheader("Refinery Exposure Table")
        if refineries_data:
            df_ref = pd.DataFrame([
                {
                    "Refinery": r["name"],
                    "Operator": r["operator"],
                    "Port": r["port_id"],
                    "Exposure": f"{r['exposure_score']:.1f}",
                    "Band": r["band"].title(),
                    "Top Contributing Route": r["contributions"][0]["route_id"] if r.get("contributions") else "N/A"
                }
                for r in refineries_data
            ])

            operators = ["All"] + sorted(list(set(df_ref["Operator"].tolist())))
            selected_op = st.selectbox("Filter by Operator", operators)
            if selected_op != "All":
                df_ref = df_ref[df_ref["Operator"] == selected_op]

            st.dataframe(df_ref, width='stretch', hide_index=True)

# ---------------------------------------------------------
# TAB 4: SIGNAL INTELLIGENCE FEED
# ---------------------------------------------------------
with tab4:
    st.subheader("News & Event Intelligence Feed")
    st.caption("Structured risk events extracted from news reporting and scored deterministically.")

    if total_signals == 0:
        st.info("No risk signals ingested yet. Use Simulation Controls on the Route Risk tab to run live ingestion or replay scenarios.")
    else:
        f_col1, f_col2 = st.columns([2, 1])
        with f_col1:
            search_query = st.text_input("Search headlines or evidence", "")
        with f_col2:
            band_filter = st.selectbox("Filter by Risk Band", ["All", "High", "Medium", "Low"])

        filtered_signals = list(signals_data)
        if band_filter != "All":
            filtered_signals = [s for s in filtered_signals if s.get("band", "").lower() == band_filter.lower()]
        if search_query.strip():
            q = search_query.lower()
            filtered_signals = [
                s for s in filtered_signals
                if q in s.get("title", "").lower() or q in s.get("extraction", {}).get("evidence", "").lower()
            ]

        st.write(f"Showing **{len(filtered_signals)}** signals:")
        if not filtered_signals:
            st.info("No matching risk signals found.")
        else:
            for signal in filtered_signals:
                render_signal_card(signal)

# ---------------------------------------------------------
# TAB 5: INGESTION HISTORY
# ---------------------------------------------------------
with tab5:
    st.subheader("Ingestion Run History")
    st.caption(
        "Persisted server-side across every run (live or replay), unlike a browser-session banner — "
        "this is the operational trail that the pipeline has actually executed."
    )
    render_run_history_table(run_history)

# ---------------------------------------------------------
# TAB 6: SUPPLY CHAIN GRAPH & ABOUT
# ---------------------------------------------------------
with tab6:
    st.subheader("Supply Chain Network Topology")
    st.caption("NetworkX Directed Acyclic Graph connecting origins, chokepoints, ports, and Indian refineries.")

    graph = read("/api/graph")

    g_left, g_right = st.columns([1, 1])

    with g_left:
        st.markdown("#### Topology Diagram")
        dot_str = "digraph supply {\n  rankdir=LR;\n  node [style=filled, fillcolor=\"#1B3A5C\", fontcolor=white, fontname=\"sans-serif\"];\n"
        dot_str += ";\n".join(f'  "{edge["source"]}" -> "{edge["target"]}"' for edge in graph["edges"])
        dot_str += "\n}"
        st.graphviz_chart(dot_str)

    with g_right:
        st.markdown("#### Supply Network Edges & Weights")
        df_edges = pd.DataFrame(graph["edges"])
        st.dataframe(df_edges, width='stretch', hide_index=True)
        st.caption("Accessible tabular representation of graph edges and dependency nodes.")

    st.markdown("---")
    st.subheader("About This System")
    st.markdown(
        "**System scope:** RSS-primary news ingestion (GDELT optional, degrades gracefully), "
        "LLM (Gemini) or deterministic heuristic extraction into typed risk facts, pure-function "
        "scoring, NetworkX supply-chain propagation, SQLite storage, Streamlit-over-HTTP dashboard."
    )
    st.markdown(
        "**Deliberately deferred:** live AIS vessel tracking, a learned/dynamic credibility model, "
        "Neo4j, accuracy metrics (precision/recall/backtesting), authentication, maps, and a React "
        "frontend. See `docs/LIMITATIONS.md` for the reasoning behind each."
    )

    st.markdown("---")
    st.subheader("System Health")
    st.json(health)
