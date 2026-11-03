# Project-I demo handover

Start from the repository root with `demo.bat`. It starts the API, React dashboard,
15-minute news/trade monitor and optional AIS stream. Gemini calls consume the
configured account quota. `run.bat` starts only the web application. Ctrl+C stops
processes owned by that launcher; existing services are reused. Collector and
monitor locks prevent duplicate workers. Open http://127.0.0.1:5173/.

## Demonstration sequence

1. Show live source status, observation timestamps and extractor provenance.
2. Show route risk, contributing articles, supplier/route/refinery graph and alerts.
3. Show AIS vessel observations and receiver coverage. These are regional sightings,
   not confirmed crude cargoes or measured strait transits. AIS score fusion is off
   by default (`AIS_SCORE_FUSION_ENABLED=false`) pending baseline validation.
4. Show dated PPAC/EIA national trade context; refinery weights remain illustrative.
5. Ask an evidence question. Inspect citations. Provider outages retain retrieval
   results; a fallback answer must not be presented as successful LLM synthesis.
6. Show a synthetic replay, explicitly identifying it as a demonstration fixture.
   Switch back to Live afterwards; monitoring does not override a selected replay.
7. Show Validation: seven historical research events and 21 registered sources,
   separate from the three provisionally reviewed evaluation windows. Inspect
   review warnings and false negatives rather than claiming high accuracy.

## Reproduce checks

From the root: `.venv\Scripts\python.exe -m scripts.evaluate_demo` rebuilds the
offline heuristic pilot, validates research joins/dates and records input hashes.
The original Gemini pilot remains a separately measured report. The three-window
pilot misses both positive windows at the fixed threshold of 30; no threshold has
been fitted to these already inspected examples. Broad publisher landing pages
and proposed labels remain explicitly flagged for review, not accepted as final
benchmark evidence. Research event links do not infer India delivery losses.

Backend: from `backend`, run `..\.venv\Scripts\python.exe -m pytest -q`.
Frontend: from `frontend`, run `npm ci`, `npm run build`, `npm run lint`.

## Remaining field validation and deployment

- Replace research landing-page references with direct claim citations; independently
  review labels and add event-separated development/test windows, including controls.
- Increase the benchmark with original dated articles; measure precision, recall,
  false alarms and lead time using actual availability records. Calibrate only on
  development data. Current metrics are a small diagnostic, not production accuracy.
- Accumulate qualified AIS baseline coverage and evaluate outages, vessel classes and
  anomalies before enabling experimental score fusion. Broader regional reception
  and real refinery procurement weights require additional data.
- Verify RAG synthesis when the external provider is healthy; keep citation rejection
  and retrieval fallback active. Deploy with persistent storage, secrets and workers.

Scenario simulation and automated procurement rerouting belong to Project-II.
