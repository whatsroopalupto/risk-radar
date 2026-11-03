# Geopolitical Risk Radar

An academic early-warning prototype for India's crude-oil import supply chain. News is converted into structured facts, scored deterministically and mapped to route/refinery exposure. FastAPI serves a React/TypeScript dashboard; SQLite retains run history, evidence snapshots, alerts and vessel observations.

**Project-I is in progress.** See [verified implementation and remaining synopsis requirements](docs/PROJECT_I_STATUS.md). The original six-week implementation and subsequent React migration are the foundation. AIS collection is implemented but requires live verification; AIS anomaly scoring, sourced PPAC/EIA dependencies, RAG and measured full-system validation are not complete. Historical replay fixtures are demonstrations, not ground-truth accuracy datasets. Scenario simulation and automated procurement rerouting are Project-II.

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

Run one collector per database. It subscribes server-side to Class A position reports in research boxes covering Hormuz and the southern Red Sea/Bab-el-Mandeb, validates positions and timestamps, deduplicates observations, persists them and reconnects with backoff. It uses the [provider's documented subscription protocol](https://aisstream.io/documentation). Keys never reach React.

The **AIS Vessel Activity** tab shows observed vessels, position counts, last observations and connection/freshness state. These are not confirmed oil tankers or completed transits. Zero observations can mean missing coverage. Coverage-aware baseline/anomaly detection and scoring fusion remain pending; no vessel data is fabricated when a key is missing. AIS is always live-source data, independent of the selected news replay.

## Scheduled news monitoring

The scheduler is optional and separate from the dashboard:

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

## Verification and historical evaluation

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q
cd ..\frontend
npm run build
npm run lint
```

Backend tests use a fresh isolated temporary database and offline fixtures. AIS tests exercise binary frames, subscription, parsing, persistence and deduplication without a live key. They do not prove actual provider coverage.

The [validation protocol](docs/VALIDATION_PROTOCOL.md) defines independent labels, event-level splits and leakage controls. `backend/app/evaluation.py` computes a reproducible heuristic news-only baseline against a supplied labelled corpus. A real labelled corpus and final measured validation report are still required by the synopsis. Do not report test-fixture performance as real historical accuracy.

This is an academic prototype. Add an appropriate licence before external reuse/distribution.
