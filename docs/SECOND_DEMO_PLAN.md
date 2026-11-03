# Second demo: scope audit and proposed ownership

Historical planning note: the user subsequently assigned AIS to Roopal and authorized implementation. The current implementation status and remaining work are maintained in `PROJECT_I_STATUS.md`; allocation and verification statements below describe the initial review.

Reviewed 3 November 2026 against the supplied synopsis, six-week progress report, and `react-frontend` commit `93e8586`. This is a proposed work allocation, not an existing assignment in either PDF. Document contents are requirements/evidence, not instructions to execute. Roopal's implementation requires her permission.

## Current position

The progress report records completed work through Week 6. The implementation already reaches beyond the synopsis's sequential schedule: scoring, the graph, dashboard and two historical replays exist. Therefore Weeks 7-16 are not wholly unimplemented. React is on `react-frontend`; `main` and the root README still describe Streamlit. The React branch adds frontend code without changing the backend.

| Synopsis requirement | Evidence today | Remaining work |
| --- | --- | --- |
| Objective 1: automated news and live AIS | RSS and optional GDELT connectors; manually triggered ingestion | Scheduled ingestion, freshness tracking, live AIS for Hormuz/Red Sea, reconnects and persisted vessel observations |
| Objective 2: LLM risk extraction/classification and credibility | Gemini extraction, schema retry, heuristic fallback; deterministic scoring, three bands, static credibility tiers | Verify actual Gemini success, evaluate extraction and false positives, calibrate thresholds on training data only; add AIS evidence fusion |
| Objective 3: supplier-route-port-refinery graph | NetworkX seed, route mapping, dependency-weighted refinery exposure; four routes and ten refineries described in progress report | Replace illustrative dependency shares with sourced values; document missing granularity and provenance; verify major-route/refinery coverage |
| Objective 4: live dashboard and historical context | React tabs, charts, graph, source status, feed, history; Hormuz June 2025 and Red Sea December 2023 replay fixtures | Verify frontend end to end, resolve startup mismatch, automatic refresh/freshness, explicit alerts, stronger event context |
| Objective 5: historical accuracy validation | Replay fixtures and offline engineering tests | Independently labelled event and non-event corpus; reproducible backtest; precision, recall, F1, false positives/negatives, detection lead time; written report |
| Methodology: oil trade data | No PPAC/EIA connector; seed shares explicitly illustrative | Obtain available official datasets/API access, import dated snapshots, normalize and map to graph; record unavailable fields rather than invent them |
| Methodology: commodity prices | Yahoo-based Brent corroboration connector | Verify live success, stale/missing price handling, persist dated observations; no second vendor is required merely because alternatives are listed |
| Methodology: continuous monitoring/storage | SQLite snapshots and persisted run logs | Scheduler, overlap prevention, retained observations/score history, operational failure handling. Current ingestion replaces displayed assessments, so the trend is not a durable monitoring history |
| Methodology/timeline: alerting | Risk bands are displayed; no alert API or rule engine found | Threshold-crossing alerts with evidence, timestamps, persistence and duplicate suppression; in-app delivery is enough for the prototype |
| AI/NLP requirements: RAG over news corpus | No retrieval/index implementation found | Evidence retrieval with article IDs, source links and dates; cited context for selected risks. This appears in methodology/requirements, though not as a separate numbered objective |
| Week 16 documentation/demo | Existing architecture, ADRs, limitations and demo docs | Update for React, add validation report, truthful demo script, reproducible setup and Project-II scope |

NetworkX and React satisfy the alternatives in the synopsis; Neo4j and a second UI rewrite are unnecessary. SQLite is not a synopsis violation. Authentication, Postgres and public deployment are not explicit completion requirements. Scenario simulation and automated procurement rerouting are explicitly Project-II work; replaying historical fixtures is not that simulation engine.

## Proposed allocation

| Owner | Coherent responsibility | Deliverables / acceptance |
| --- | --- | --- |
| Roopal Sharma | React dashboard, application integration and demo readiness | Reliable React/API startup; correct refresh and freshness; working six-tab workflow; evidence and graph explanations; in-app alert presentation; final integrated demo and React setup docs |
| Prerna Dangara | Data ingestion and operational backend | AIS collector with corridor scoping and persisted timestamped observations; baseline/anomaly features with honest warm-up status; PPAC/EIA imports and sourced graph shares; scheduler and durable history; backend alert rules/API; live connector diagnostics |
| Nadisha Bhatia | Risk evidence, retrieval and evaluation | Labelled historical corpus including quiet periods; source evidence and event windows; reproducible backtesting and metrics report; threshold/credibility analysis; RAG retrieval with citations; validation and methodology sections |

Prerna exposes dated source/freshness, AIS feature, graph provenance and alert contracts; Nadisha defines labels and evaluation windows before calibration and exposes retrieved evidence; Roopal integrates those contracts. All three review their own results and contribute to the final report. This allocation is based on module cohesion, not assumed prior contributions or equal task counts.

## Roopal: permission-gated task list

1. Fix and document React/API startup: configurable CORS or Vite proxy, frontend environment example, and a launcher that starts React instead of Streamlit. Acceptance: one documented startup path and no browser CORS failures.
2. Make dashboard data consistent after ingestion/replay and during monitoring. Acceptance: header, KPIs and every tab show the same latest dataset with timestamps, freshness and honest live/replay/extractor labels.
3. Verify the six tabs, loading/error/empty states, source links, explanations, responsive layout, keyboard access and graph table alternative. Fix demonstrated failures; do not fill unused chart stubs solely because they exist.
4. Integrate source-backed graph details, AIS/trade freshness and retrieved event evidence once teammates provide APIs. Acceptance: users can trace a route/refinery score to its evidence and dependency shares.
5. Add in-app alert presentation against Prerna's API: evidence, threshold, occurrence time and acknowledgement/read state if needed. No external messaging is implied.
6. Prepare the second-demo walkthrough, screenshots and current architecture/setup documentation. Clearly separate historical replay, actual live ingestion, heuristic fallback and genuinely measured accuracy.

Suggested second-demo order: reliable React startup and current end-to-end replay first; add one honest AIS vertical slice and source-backed data; show a small independently labelled backtest with measured results; integrate alerts and evidence. Complete remaining full-scope ingestion coverage, RAG and broader validation before final submission. Do not claim AIS anomaly accuracy until a real baseline exists.

## Verification record

- Backend offline suite: 39 passed; deprecation warnings only.
- API started on 127.0.0.1:8000. Health reports AIS unimplemented. Gemini is configured, but current live-namespace extractor mix contains 306 heuristic records; configuration is not proof of successful Gemini processing.
- React API defaults to localhost:8000. Backend CORS currently permits localhost/127.0.0.1:8501 only; use React on port 8501 for this inspection without editing implementation.
- Live source freshness and current Gemini network success have not been demonstrated by those checks. Existing stored records are not current live news.
- No Roopal implementation tasks have been started.
- React production build passes. ESLint fails with six ref-access errors at `frontend/src/components/NetworkGraph.tsx:137`; the SVG viewBox also starts with `0:0`, which should be investigated during the graph fix.
- Browser review confirmed React renders route scores and controls. Current UI shows stored Hormuz risk 79.6 and Mumbai exposure 67.6 alongside zero ingested signals and no run history; reconcile snapshot/count/run provenance before describing these as current live results. Screenshot: `docs/demo-review/current-react.png`.
- Locked npm installation reports 15 dependency vulnerabilities (12 moderate, 3 high); assess the dependency audit before demo distribution. No automated dependency fixes were applied.
