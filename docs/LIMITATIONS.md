# Current limitations

- The AIS key/subscription and real persisted positions in the Hormuz research box have been verified. Red Sea observations remain unavailable, and early reception does not establish sustained coverage. The collector must run over time to establish a qualified baseline.
- AIS activity is observed Class A traffic. Static type can identify a reported tanker category, not crude cargo, actual loading or a completed transit. Heartbeats do not prove receiver coverage; total observation gaps are excluded from anomaly scoring.
- The activity-drop and score-fusion rules are implemented and tested on synthetic unit scenarios, not validated against labelled real AIS disruptions. The default baseline requires 30 days of qualified hours; the UI abstains while collecting.
- GDELT was unavailable in the live verification. RSS, Brent and Gemini each succeeded; Gemini also showed transient service failures, with retries/fallback. Source availability and quotas can change.
- PPAC/EIA data is ingested from official public publications. These are dated national statistics, not live refinery inventory/procurement feeds. Parsers stop rather than guess after a layout change. A failed refresh can serve the previous successful snapshot with that fact labelled.
- Supplier graph edges are possible geographic paths. Refinery route dependencies are illustrative assumptions. National import shares cannot justify substituting values for individual refinery dependencies.
- Risk scores are transparent rule-based estimates, not calibrated disruption probabilities. Noisy-OR can amplify correlated reports even after headline deduplication. Static credibility weights and heuristic confidence require independent evaluation.
- The three-window historical pilot is provisional. Both news-only runs missed its two positive windows at threshold 30. It is neither representative accuracy nor an early-warning lead-time result. See the report before presenting any metric.
- RAG may miss semantic matches because retrieval is lexical and capped at 5,000 recent articles. Source-ID validation cannot prove factual support for every generated sentence. Generation failures fall back to source excerpts.
- SQLite, cross-process file locks and shared display selection support a local single-user installation, not a distributed service. Data is retained by default; plan disk capacity before continuous high-volume AIS collection. No automated deletion policy has been applied.
- The historical `render.yaml` blueprint targets the former Streamlit deployment and is not verified for the current React application. Local execution is the supported demo path. Production hosting, authentication and multi-user operation are separate work.
- The npm audit has 12 moderate development-tool findings after compatible high-severity fixes. Forced major dependency changes were not applied.

Scenario simulation and automated procurement rerouting remain Project-II.
