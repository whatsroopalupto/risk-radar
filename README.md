# Geopolitical Risk Radar

An academic early-warning prototype for India's crude-oil import supply chain. News is converted into structured facts, scored deterministically and mapped to route/refinery exposure. FastAPI serves a React/TypeScript dashboard; SQLite retains run history, evidence snapshots, alerts and vessel observations.

**The core Project-I prototype is implemented; field validation remains incomplete.** See [verification and remaining evidence requirements](docs/PROJECT_I_STATUS.md). The system includes news/AIS collection, coverage-gated activity corroboration, official PPAC/EIA national context, cited RAG, alerts, retained history and measured historical pilot reports. Actual AIS traffic coverage, a qualified baseline and broader independently reviewed accuracy validation are still required. Refinery procurement dependencies remain explicit model assumptions. Historical replay fixtures are demonstrations, not ground-truth accuracy datasets. Scenario simulation and automated procurement rerouting are Project-II.

## Windows setup

Use Python 3.12+, Node.js 22.12+ (or a supported newer release) and Git. From the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd frontend
npm ci
cd ..
if (-not (Test-Path backend\.env)) { Copy-Item backend\.env.example backend\.env }
```

Create `backend/.env` only if it does not already exist. Keep keys there; never commit them. Blank `GEMINI_API_KEY` selects the heuristic fallback. `AISSTREAM_API_KEY` is required only for live vessel collection. Existing environment variables override `.env`.

Double-click `run.bat`, or run:

```powershell
.\.venv\Scripts\python.exe run.py
```

The launcher starts FastAPI at `http://127.0.0.1:8000` and React at `http://127.0.0.1:5173`, opens the dashboard and stops only processes it started on Ctrl+C. The database defaults to `risk_radar.db` in the repository root regardless of working directory. The historical Streamlit dashboard remains under `dashboard/`; it is not the current launcher target.

Manual startup in two terminals, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Vite proxies `/api` to FastAPI. `frontend/.env.example` documents the optional API origin for separate hosting. A production host must proxy `/api` or set that origin at build time. Restrict `CORS_ORIGINS` to intended origins when hosting. There is no authentication; the provided commands bind locally.

## Live AIS

Get a key from [AISStream](https://aisstream.io/). Put it in `backend/.env` as `AISSTREAM_API_KEY=...`. Then run a separate terminal from the project root:

```powershell
.\.venv\Scripts\python.exe -m backend.app.connectors.ais
```

Run one collector per database. It subscribes server-side to Class A position and static ship-type reports in research boxes covering Hormuz and the southern Red Sea/Bab-el-Mandeb, validates positions and timestamps, deduplicates observations, persists them and reconnects with backoff. It uses the [provider's documented subscription protocol](https://aisstream.io/documentation). Keys never reach React.

The **AIS Vessel Activity** tab shows observed vessels, reported type when available, position counts, last observations, connection/freshness state and qualified baseline hours. These are not verified crude cargoes or completed transits. Zero observations can mean missing coverage. The activity-drop rule requires a fresh, covered current hour and the configured baseline (30 days by default). It abstains on zero observations and can only corroborate existing news risk, by at most 10% of remaining score headroom. It is implemented and unit-tested, not yet validated on real labelled AIS disruptions. No vessel data or baseline is fabricated. AIS is always live-source data, independent of the selected news replay.

## Scheduled news monitoring

The scheduler is optional and separate from the dashboard. It also checks official trade reports daily:

```powershell
.\.venv\Scripts\python.exe -m backend.app.monitor --interval-seconds 900 --window-hours 24
```

Use `--once` for a single cycle. Ingestion is serial; concurrent manual/replay ingestion receives HTTP 409. Background monitoring updates the live namespace without switching a replay currently being viewed. Ctrl+C stops monitoring. Run one scheduler per database.

## Data and scoring

- RSS is the primary news source; GDELT is optional and failures are reported separately.
- Gemini extracts facts; the heuristic fallback is labelled as such. A configured Gemini key is not proof of a successful Gemini request. The dashboard counts actual extractor provenance.
- Signal score: event weight × severity × confidence × credibility × recency × speculative discount. News route risk uses noisy-OR; optional Brent corroboration contributes only when news evidence exists.
- Risk bands use 0-100: Low below 30, Medium below 65, High from 65.
- Refinery exposure is dependency-weighted route risk. Current graph dependency shares are **illustrative**, not verified refinery procurement data.
- Live runs and each replay have separate current datasets. Run logs and complete risk/evidence snapshots are append-only. The displayed namespace is a shared local setting, suitable for this single-user prototype.
- Live trends use retained daily news-risk snapshots. Replay/legacy trends reconstruct cumulative evidence; they are not measured historical daily predictions.
- Legacy stored assessments without matching run metadata are labelled unverified rather than fresh live results. New tables are created on startup; existing data is not relabelled or deleted.
- In-app alerts record evidence-backed crossings of 30/65 or an initial elevated observation. Repeated unchanged elevated runs do not create duplicate alerts. No email/SMS is sent.
- A total RSS/GDELT outage retains the previous risk instead of replacing it with zero. The risk-calculation timestamp stays separate from the failed poll time.
- Live extraction is capped by `MAX_ARTICLES_PER_RUN` (80 by default). Remaining relevant articles are retained for retrieval and explicitly counted as deferred/unscored.

## Official trade context and RAG

**Official Trade Context** ingests the public PPAC monthly PDF and EIA India country brief, preserving original units, periods, source links, PDF page references and source hashes. They are publication adapters, not claimed account-bound API integrations. A failed refresh retains the last successful snapshot with a warning. National totals and supplier shares do not establish refinery-level procurement dependencies.

**Evidence & Context** retrieves matching retained articles from the selected namespace with lexical BM25. Optional Gemini generation must attach known retrieved source IDs to every paragraph; malformed citations or unavailable generation fall back to retrieved evidence. This is RAG without an external vector database. Source-ID checks do not guarantee every generated statement is faithful; inspect original sources and dates. Answers never alter scores or recommend procurement rerouting.

**Historical Validation** shows the measured pilot reports, case errors and limitations. Both fixed-threshold news-only runs miss the two positive windows in the small provisional corpus; no accuracy claim is hidden or inflated. See [validation report](docs/VALIDATION_REPORT.md).

## Demo flow

1. Open React and check dataset, source status and timestamps.
2. Replay Hormuz or Red Sea; inspect route risk, refinery exposure, news evidence, graph and the labelled replay alerts.
3. Choose **Show saved live data** to return without deleting/replaying a live run. Use **Run Live Ingestion** when current news is needed; check source failures and actual extraction provenance.
4. Open **AIS Vessel Activity**. With no key or observations, show the truthful unavailable/baseline state. With a running collector, inspect real observed positions and timestamps.
5. Explain remaining limitations and the difference between demonstration fixtures, news-only baseline evaluation and measured full-system accuracy.

## API

Interactive endpoint documentation: `http://127.0.0.1:8000/docs`.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Selected dataset, source status, actual extractor mix, counts and latest run |
| `POST /api/ingest/run` | Manual live ingestion |
| `GET /api/ingest/history` | All recorded live/replay runs |
| `GET /api/signals` | Displayed assessments; optional band/route filters |
| `GET /api/risk/routes`, `/api/risk/refineries` | Current route and refinery results |
| `GET /api/risk/routes/timeseries` | Daily news-risk chart |
| `GET /api/risk/history` | Retained route snapshots for selected namespace |
| `GET /api/graph` | Supply-chain graph |
| `GET /api/scenarios`, `POST /api/replay/{id}` | Discover/replay demonstration fixtures |
| `POST /api/display/live` | Select saved live data |
| `GET /api/ais/activity` | Observed vessel activity and collector health |
| `GET /api/alerts` | Evidence-linked alerts for selected dataset |
| `GET /api/trade`, `POST /api/trade/refresh` | Retained official national statistics / refresh |
| `POST /api/evidence/ask` | Namespace-scoped retrieval and optional cited generation |
| `GET /api/validation` | Measured provisional pilot reports |

## Verification and historical evaluation

For the complete local demo, run `demo.bat` (includes scheduled news/trade collection
and AIS; Gemini calls use account quota). See [demo handover](docs/DEMO_COMPLETION.md)
for the walkthrough, measured limitations and remaining field validation.
Run `.venv\Scripts\python.exe -m scripts.evaluate_demo` to rebuild the offline
pilot with links to the validated historical research register.

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q
cd ..\frontend
npm run build
npm run lint
```

Backend tests use a fresh isolated temporary database and offline fixtures. AIS tests exercise binary frames, subscription, parsing, persistence and deduplication without a live key. They do not prove actual provider coverage.

The [validation protocol](docs/VALIDATION_PROTOCOL.md) defines independent labels, event-level splits and leakage controls. `backend/app/evaluation.py` supports heuristic or Gemini news-only evaluation with actual extractor provenance, availability cutoffs and dataset hashes. A checked-in, provisionally source-reviewed three-window pilot and its [written report](docs/VALIDATION_REPORT.md) expose current errors. Its paraphrases and publication-time proxies are not an original historical feed or a final held-out benchmark.

Reproduce the pilot from the repository root:

```powershell
.\.venv\Scripts\python.exe -m backend.app.evaluation backend/data/evaluation/pilot_cases.json --output output/evaluation/pilot_heuristic.json
.\.venv\Scripts\python.exe -m backend.app.evaluation backend/data/evaluation/pilot_cases.json --extractor gemini --output output/evaluation/pilot_gemini.json
```

Gemini mode makes external requests unless validated extractions are cached. It labels any heuristic fallback honestly. A larger original-news corpus, reviewed labels and coverage-valid AIS data are required before claiming reliable full-system precision/recall or warning lead time. See the [demo script](docs/DEMO_SCRIPT.md) and [current limitations](docs/LIMITATIONS.md).

This is an academic prototype. Add an appropriate licence before external reuse/distribution.
