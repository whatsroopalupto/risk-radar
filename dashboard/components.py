"""Accessible text-plus-colour renderers and visual charts for Streamlit dashboard."""
import html
import altair as alt
import pandas as pd
import streamlit as st

# Risk-band colours are Okabe-Ito (colour-blind safe) and are never used for anything but risk state.
PALETTE = {"low": "#0072B2", "medium": "#E69F00", "high": "#D55E00"}
SYMBOLS = {"low": "▲", "medium": "▲▲", "high": "▲▲▲"}
INK = "#1C1E21"
MUTED = "#6B6F76"

EVENT_LABELS = {
    "blockade_or_closure": "Blockade / Closure",
    "attack_on_vessel": "Attack on Vessel",
    "military_strike": "Military Strike",
    "port_or_terminal_disruption": "Port / Terminal Disruption",
    "sanctions": "Sanctions",
    "naval_buildup": "Naval Buildup",
    "diplomatic_escalation": "Diplomatic Escalation",
    "policy_change": "Policy Change",
    "other": "Other Risk Event"
}
CREDIBILITY_LABELS = {1: "Tier 1 — Wire/Major", 2: "Tier 2 — National/Trade", 3: "Tier 3 — Other Resolvable", 4: "Tier 4 — Unknown"}
STATUS_LABELS = {
    "ok": "Active",
    "unavailable": "Temporarily unavailable",
    "not_yet_run": "Awaiting first update",
    "not_polled_last_run": "Not checked in the latest update",
    "not_implemented_phase_2": "Planned for a future release",
}
STATUS_COLORS = {
    "ok": "#0B7A46",
    "unavailable": "#B8860B",
    "not_yet_run": "#8A8D93",
    "not_polled_last_run": "#8A8D93",
    "not_implemented_phase_2": "#8A8D93",
}
SOURCE_LABELS = {"rss": "RSS News", "gdelt": "GDELT", "prices": "Brent Prices", "fixture": "Replay Fixture", "ais": "AIS Vessel Tracking"}
SOURCE_DESCRIPTIONS = {
    "rss": "Continuously scans major news wires and outlets for reports of tanker attacks, blockades, sanctions and naval activity relevant to India's crude oil imports.",
    "gdelt": "A secondary, free public global news index that corroborates the primary news feed — it needs no subscription or key. If it is temporarily unreachable, or simply has nothing new for these search terms, monitoring continues uninterrupted on the primary feed.",
    "prices": "Tracks day-over-day movement in the price of Brent crude oil. A sharp price swing alongside a news event adds confidence that markets are reacting to the same risk.",
    "fixture": "A saved set of real headlines from a past crisis — the June 2025 Strait of Hormuz escalation — used to demonstrate how the system responds to a fast-developing situation.",
    "ais": "Will track tanker movement and congestion through key maritime chokepoints directly. This capability is planned for a future release.",
}
# Route identity encodes as colour AND point shape together, never colour alone.
ROUTE_COLORS = ["#1B3A5C", "#D55E00", "#009E73", "#CC79A7"]
ROUTE_SHAPES = ["circle", "square", "triangle-up", "diamond"]


def extractor_label(name: str) -> str:
    """Distinguish LLM-produced extractions from the deterministic fallback wherever an extractor name is shown."""
    return f"LLM · {name}" if not name.startswith("heuristic") else f"Heuristic · {name}"


def risk_badge(score: float, band: str) -> None:
    """Present every risk state with number, word, symbol, and safe colour."""
    st.markdown(
        f"<span style='color:{PALETTE.get(band, '#0072B2')};font-weight:bold;font-size:1.05rem;'>"
        f"Risk {score:.1f} / 100 — {band.title()} {SYMBOLS.get(band, '▲')}</span>",
        unsafe_allow_html=True
    )


def render_kpi_card(title: str, value: str, caption: str, band: str, explanation: str) -> None:
    """Render a KPI card whose number is always visible, with a click-through explanation of how it is computed."""
    color = PALETTE.get(band, "#0072B2")
    with st.container(border=True):
        st.markdown(
            f"<div style='font-size:0.78rem;color:{MUTED};text-transform:uppercase;letter-spacing:0.04em;'>{html.escape(title)}</div>"
            f"<div style='font-size:1.7rem;font-weight:700;color:{color};margin:2px 0;'>{html.escape(value)}</div>"
            f"<div style='font-size:0.8rem;color:{MUTED};margin-bottom:2px;'>{html.escape(caption)}</div>",
            unsafe_allow_html=True
        )
        with st.popover("Details", width='stretch'):
            st.write(explanation)


def render_status_strip(health: dict) -> None:
    """Show the pipeline's real, current state as clickable cards, in plain analyst-facing language."""
    extractor = health.get("extractor", {})
    active = extractor.get("active", "unknown")
    is_llm = "gemini" in active.lower()
    engine_word = "AI" if is_llm else "Rule-based"
    engine_color = STATUS_COLORS["ok"] if is_llm else STATUS_COLORS["unavailable"]
    mix = health.get("extractor_mix", {})
    total = sum(mix.values())
    llm_count = sum(count for name, count in mix.items() if "gemini" in name.lower())

    sources = health.get("sources", {})
    last_run = health.get("last_run_time")
    last_run_str = str(last_run)[:19].replace("T", " ") if last_run else "no update yet"

    cols = st.columns(len(sources) + 2)

    with cols[0]:
        with st.container(border=True):
            st.markdown(
                f"<div style='font-size:0.72rem;color:{MUTED};text-transform:uppercase;letter-spacing:0.03em;'>Classification Engine</div>"
                f"<div style='font-size:0.92rem;font-weight:700;color:{engine_color};margin:2px 0 6px 0;'>{engine_word} · {html.escape(active)}</div>",
                unsafe_allow_html=True
            )
            with st.popover("Details", width='stretch'):
                if is_llm:
                    st.write(
                        "Incoming headlines are currently being read by the AI-based classifier, which extracts "
                        "event type, severity and other structured details directly from each article's text."
                    )
                else:
                    st.write(
                        "Incoming headlines are currently being read by the rule-based classifier. It applies a "
                        "fixed set of proven keyword and phrase rules, so it is fast and always available — "
                        "monitoring never stops even if the AI-based classifier is temporarily unavailable."
                    )
                if total:
                    st.write(f"In the current view, {llm_count} of {total} headlines were read by the AI-based classifier; the rest used the rule-based classifier.")

    for i, (name, info) in enumerate(sources.items(), start=1):
        status = info.get("status", "unknown")
        fetched = info.get("fetched", 0)
        if status == "ok" and fetched == 0 and name in ("rss", "gdelt"):
            # "Reachable" and "actually returned something new" are different claims — never conflate them into one green "Active".
            label, color = "Reached, no new results", STATUS_COLORS["not_polled_last_run"]
        else:
            label = STATUS_LABELS.get(status, status.replace("_", " ").title())
            color = STATUS_COLORS.get(status, MUTED)
        with cols[i]:
            with st.container(border=True):
                st.markdown(
                    f"<div style='font-size:0.72rem;color:{MUTED};text-transform:uppercase;letter-spacing:0.03em;'>{SOURCE_LABELS.get(name, name.title())}</div>"
                    f"<div style='font-size:0.92rem;font-weight:700;color:{color};margin:2px 0 6px 0;'>{html.escape(label)}</div>",
                    unsafe_allow_html=True
                )
                with st.popover("Details", width='stretch'):
                    st.write(SOURCE_DESCRIPTIONS.get(name, ""))
                    if status == "ok":
                        st.write(f"Picked up {fetched} new item(s) in the latest update.")
                    elif status == "unavailable":
                        st.write("This source did not respond during the latest update. Monitoring continued on the other sources.")

    with cols[-1]:
        st.markdown(
            f"<div style='padding-top:1.6rem;color:{MUTED};font-size:0.82rem;'>Last updated<br><b style='color:{INK};'>{html.escape(last_run_str)}</b></div>",
            unsafe_allow_html=True
        )


def render_route_chart(routes: list[dict]) -> None:
    """Render an interactive Altair horizontal bar chart comparing route risk scores."""
    if not routes:
        st.info("No route data available.")
        return

    df = pd.DataFrame(routes)
    df["display_score"] = df["composite_score"].round(1)
    df["bar_label"] = df.apply(lambda r: f"{r['composite_score']:.1f} · {r['band'].title()} {SYMBOLS.get(r['band'], '')}", axis=1)

    base = alt.Chart(df).encode(
        y=alt.Y("name:N", title="Supply Route", sort="-x"),
        x=alt.X("composite_score:Q", title="Composite Risk Score (0-100)", scale=alt.Scale(domain=[0, 100]))
    )

    bars = base.mark_bar(cornerRadiusTopRight=2, cornerRadiusBottomRight=2).encode(
        color=alt.Color(
            "band:N",
            scale=alt.Scale(domain=["low", "medium", "high"], range=["#0072B2", "#E69F00", "#D55E00"]),
            legend=alt.Legend(title="Risk Band")
        ),
        tooltip=["name", "composite_score", "news_score", "market_score", "band"]
    )

    text = base.mark_text(align="left", baseline="middle", dx=6, color=INK, fontSize=11).encode(text="bar_label:N")

    chart = (bars + text).properties(height=240)
    st.altair_chart(chart, width='stretch')


def render_refinery_chart(refineries: list[dict]) -> None:
    """Render an Altair bar chart ranking Indian refineries by supply exposure."""
    if not refineries:
        st.info("No refinery exposure data available.")
        return

    df = pd.DataFrame(refineries)
    df["display_score"] = df["exposure_score"].round(1)
    df["bar_label"] = df.apply(lambda r: f"{r['exposure_score']:.1f} · {r['band'].title()} {SYMBOLS.get(r['band'], '')}", axis=1)

    base = alt.Chart(df).encode(
        y=alt.Y("name:N", title="Refinery", sort="-x"),
        x=alt.X("exposure_score:Q", title="Refinery Exposure Score (0-100)", scale=alt.Scale(domain=[0, 100]))
    )

    bars = base.mark_bar(cornerRadiusTopRight=2, cornerRadiusBottomRight=2).encode(
        color=alt.Color(
            "band:N",
            scale=alt.Scale(domain=["low", "medium", "high"], range=["#0072B2", "#E69F00", "#D55E00"]),
            legend=alt.Legend(title="Risk Band")
        ),
        tooltip=["name", "operator", "port_id", "exposure_score", "band"]
    )

    text = base.mark_text(align="left", baseline="middle", dx=6, color=INK, fontSize=11).encode(text="bar_label:N")

    chart = (bars + text).properties(height=320)
    st.altair_chart(chart, width='stretch')


def render_signal_card(signal: dict) -> None:
    """Render a clean headline-first news card with rich metadata & score inspector."""
    ext = signal.get("extraction", {})
    raw_headline = signal.get("title") or ext.get("evidence") or f"Signal Event {signal.get('signal_id', '')[:8]}"
    raw_source = signal.get("source_name") or "RSS Feed"
    raw_evidence = ext.get("evidence", "No detailed evidence recorded")
    published = signal.get("published_at")
    raw_pub_str = published[:10] if isinstance(published, str) else "Recent"
    raw_event_type = EVENT_LABELS.get(ext.get("event_type"), ext.get("event_type", "Event"))
    raw_chokepoints = ", ".join(ext.get("affected_chokepoints", [])) or "None"
    raw_extractor = extractor_label(ext.get("extractor", "heuristic-v1"))
    is_llm = not ext.get("extractor", "heuristic-v1").startswith("heuristic")

    headline = html.escape(str(raw_headline))
    source = html.escape(str(raw_source))
    evidence = html.escape(str(raw_evidence))
    event_type = html.escape(str(raw_event_type))
    pub_str = html.escape(str(raw_pub_str))
    chokepoints = html.escape(str(raw_chokepoints))
    extractor_badge = html.escape(str(raw_extractor))
    ref_id = html.escape(str(signal.get("signal_id", "")[:8]))

    final_score = signal.get("final_score", 0.0) * 100.0
    band = signal.get("band", "low")
    color = PALETTE.get(band, "#0072B2")
    llm_bg, llm_fg = ("#E6F4F1", "#00695C") if is_llm else ("#FCEFD9", "#8A5A00")

    with st.container(border=True):
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <span style="background: #F1EEE6; color: #55524A; font-size: 0.75rem;
                                 padding: 2px 8px; border-radius: 3px; font-weight: 600; margin-right: 8px;">
                        {source}
                    </span>
                    <span style="background: #EEF2F5; color: #33475B; font-size: 0.75rem;
                                 padding: 2px 8px; border-radius: 3px; font-weight: 600; margin-right: 8px;">
                        {event_type}
                    </span>
                    <span style="background: {llm_bg}; color: {llm_fg}; font-size: 0.75rem;
                                 padding: 2px 8px; border-radius: 3px; font-weight: 600; margin-right: 8px;">
                        {extractor_badge}
                    </span>
                    <span style="color: {MUTED}; font-size: 0.75rem;">{pub_str}</span>
                </div>
                <div>
                    <span style="color:{color}; font-weight:bold; font-size: 0.95rem;">
                        Score: {final_score:.1f} / 100 ({band.title()})
                    </span>
                </div>
            </div>
            <h4 style="margin: 8px 0 6px 0; color: {INK}; font-size: 1.05rem; line-height: 1.35;">{headline}</h4>
            <p style="font-size: 0.88rem; color: #3E4148; margin: 4px 0 8px 0;">
                <b>Evidence:</b> {evidence}
            </p>
            <div style="font-size: 0.78rem; color: {MUTED};">
                <b>Chokepoints:</b> {chokepoints} &nbsp;|&nbsp;
                <b>Confidence:</b> {int(ext.get('confidence', 0)*100)}% &nbsp;|&nbsp;
                <b>Severity:</b> {ext.get('severity', 0):.2f} &nbsp;|&nbsp;
                <span style="font-family: monospace;">ref: {ref_id}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.expander("Deterministic score breakdown"):
            comps = signal.get("component_scores", {})
            type_w = comps.get("type_weight", 0.0)
            sev = comps.get("severity", 0.0)
            conf = comps.get("confidence", 0.0)
            cred = comps.get("credibility_weight", 0.0)
            rec = comps.get("recency_weight", 0.0)
            spec = comps.get("speculative_weight", 0.0)

            df_factors = pd.DataFrame([
                {"Factor": "Event Type Weight", "Value": f"{type_w:.3f}"},
                {"Factor": "Severity", "Value": f"{sev:.3f}"},
                {"Factor": "Confidence", "Value": f"{conf:.3f}"},
                {"Factor": "Source Credibility", "Value": f"{cred:.3f}"},
                {"Factor": "Recency Decay", "Value": f"{rec:.3f}"},
                {"Factor": "Speculative Discount", "Value": f"{spec:.3f}"}
            ])
            st.dataframe(df_factors, width='stretch', hide_index=True)

            product = type_w * sev * conf * cred * rec * spec
            eq_str = f"`{type_w:.3f}` × `{sev:.3f}` × `{conf:.3f}` × `{cred:.3f}` × `{rec:.3f}` × `{spec:.3f}` = **`{product:.3f}`**"
            st.markdown(f"**Equation:** {eq_str}")
            st.markdown(f"**Presentation Scale:** `{product * 100.0:.1f} / 100`")

            stored_final = signal.get("final_score", 0.0)
            if abs(product - stored_final) > 0.001:
                st.error(f"Discrepancy detected: computed product ({product:.4f}) does not match stored final_score ({stored_final:.4f})")

            st.caption(f"Extractor engine: {ext.get('extractor', 'heuristic-v1')} | Credibility tier: {signal.get('credibility_tier', 1)}")


def render_event_type_chart(signals: list[dict]) -> None:
    """Aggregate what the extractor actually classified — proof the LLM/heuristic output is substantive, not decorative."""
    if not signals:
        st.info("No extraction data yet.")
        return
    df = pd.DataFrame([{"event_type": EVENT_LABELS.get(s.get("extraction", {}).get("event_type"), "Other")} for s in signals])
    counts = df["event_type"].value_counts().reset_index()
    counts.columns = ["Event Type", "Count"]
    chart = alt.Chart(counts).mark_bar(color="#1B3A5C", cornerRadiusTopRight=2, cornerRadiusBottomRight=2).encode(
        y=alt.Y("Event Type:N", sort="-x", title=None),
        x=alt.X("Count:Q", title="Signals classified", axis=alt.Axis(format="d", tickMinStep=1)),
        tooltip=["Event Type", "Count"]
    ).properties(height=220)
    st.altair_chart(chart, width='stretch')


def render_extractor_mix_chart(signals: list[dict]) -> None:
    """Show exactly how many signals the LLM classified versus the deterministic fallback — the single clearest proof of LLM usage."""
    if not signals:
        st.info("No extraction data yet.")
        return
    df = pd.DataFrame([{"extractor": s.get("extraction", {}).get("extractor", "unknown")} for s in signals])
    counts = df["extractor"].value_counts().reset_index()
    counts.columns = ["Extractor", "Count"]
    counts["Engine"] = counts["Extractor"].apply(lambda x: "LLM (Gemini)" if "gemini" in x.lower() else "Heuristic Fallback")
    chart = alt.Chart(counts).mark_bar(cornerRadiusTopRight=2, cornerRadiusBottomRight=2).encode(
        x=alt.X("Extractor:N", title=None),
        y=alt.Y("Count:Q", title="Signals extracted", axis=alt.Axis(format="d", tickMinStep=1)),
        color=alt.Color("Engine:N", scale=alt.Scale(domain=["LLM (Gemini)", "Heuristic Fallback"], range=["#009E73", "#E69F00"]), legend=alt.Legend(title="Engine")),
        tooltip=["Extractor", "Engine", "Count"]
    ).properties(height=220)
    st.altair_chart(chart, width='stretch')


def render_severity_confidence_scatter(signals: list[dict]) -> None:
    """Plot the extractor's continuous severity/confidence output — shows nuanced structured facts, not a binary flag."""
    if not signals:
        st.info("No extraction data yet.")
        return
    rows = []
    for s in signals:
        ext = s.get("extraction", {})
        rows.append({
            "Severity": ext.get("severity", 0.0),
            "Confidence": ext.get("confidence", 0.0),
            "Band": s.get("band", "low").title(),
            "Headline": (s.get("title") or "")[:80],
            "Extractor": ext.get("extractor", "heuristic-v1"),
        })
    df = pd.DataFrame(rows)
    chart = alt.Chart(df).mark_circle(size=90, opacity=0.75).encode(
        x=alt.X("Severity:Q", scale=alt.Scale(domain=[0, 1])),
        y=alt.Y("Confidence:Q", scale=alt.Scale(domain=[0, 1])),
        color=alt.Color("Band:N", scale=alt.Scale(domain=["Low", "Medium", "High"], range=["#0072B2", "#E69F00", "#D55E00"]), legend=alt.Legend(title="Risk Band")),
        tooltip=["Headline", "Severity", "Confidence", "Band", "Extractor"]
    ).properties(height=260)
    st.altair_chart(chart, width='stretch')


def render_credibility_chart(signals: list[dict]) -> None:
    """Show the static source-credibility weighting the scorer actually applied."""
    if not signals:
        st.info("No extraction data yet.")
        return
    df = pd.DataFrame([{"tier": CREDIBILITY_LABELS.get(s.get("credibility_tier"), "Unknown")} for s in signals])
    counts = df["tier"].value_counts().reset_index()
    counts.columns = ["Credibility Tier", "Count"]
    chart = alt.Chart(counts).mark_bar(color="#4C7EA8", cornerRadiusTopRight=2, cornerRadiusBottomRight=2).encode(
        y=alt.Y("Credibility Tier:N", sort=list(CREDIBILITY_LABELS.values()), title=None),
        x=alt.X("Count:Q", title="Signals", axis=alt.Axis(format="d", tickMinStep=1)),
        tooltip=["Credibility Tier", "Count"]
    ).properties(height=180)
    st.altair_chart(chart, width='stretch')


def render_route_timeseries_chart(timeseries: list[dict]) -> None:
    """Cumulative-to-date route risk trend — the one chart that shows escalation over time instead of a single snapshot."""
    rows = []
    for route in timeseries:
        for point in route.get("points", []):
            rows.append({
                "Date": point["date"],
                "News Risk Score": point["news_score"],
                "Route": route["name"],
                "Band": point["band"].title(),
                "Signals that day": point["signal_count"],
            })
    if not rows:
        st.info("No dated signals yet — run ingestion or replay a scenario to see the trend.")
        return
    df = pd.DataFrame(rows)
    routes_sorted = sorted(df["Route"].unique())
    color_range = [ROUTE_COLORS[i % len(ROUTE_COLORS)] for i in range(len(routes_sorted))]
    shape_range = [ROUTE_SHAPES[i % len(ROUTE_SHAPES)] for i in range(len(routes_sorted))]
    base = alt.Chart(df).encode(
        # timeUnit="yearmonthdate" tells Vega-Lite this field is day-granularity only — without it, the
        # default temporal axis inserts hour-level sub-ticks (e.g. "12 PM") between the date labels.
        x=alt.X("Date:T", title="Date", timeUnit="yearmonthdate", axis=alt.Axis(format="%d %b %Y", labelAngle=-30)),
        y=alt.Y("News Risk Score:Q", title="News Risk Score (noisy-OR, 0-100)", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color("Route:N", scale=alt.Scale(domain=routes_sorted, range=color_range)),
    )
    lines = base.mark_line(strokeWidth=2.5)
    points = base.mark_point(size=90, filled=True).encode(
        shape=alt.Shape("Route:N", scale=alt.Scale(domain=routes_sorted, range=shape_range)),
        tooltip=["Route", alt.Tooltip("Date:T", timeUnit="yearmonthdate", title="Date", format="%d %b %Y"), "News Risk Score", "Band", "Signals that day"],
    )
    st.altair_chart((lines + points).properties(height=300), width='stretch')


def render_run_history_table(history: list[dict]) -> None:
    """Persisted operational log of past ingestion cycles — proves this is a running system, not a one-off script."""
    if not history:
        st.info("No ingestion runs recorded yet.")
        return
    rows = []
    for run in history:
        per_source = run.get("per_source", {})
        source_summary = ", ".join(f"{name}:{info.get('status')}({info.get('fetched', 0)})" for name, info in per_source.items())
        rows.append({
            "Finished": str(run.get("finished_at", ""))[:19].replace("T", " "),
            "Extractor": run.get("extractor_used", ""),
            "Deduped": run.get("deduped", 0),
            "Filtered Out": run.get("filtered_out", 0),
            "Extracted": run.get("extracted", 0),
            "Sources": source_summary,
        })
    st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)
