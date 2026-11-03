# Project-I status against the synopsis

Updated 3 November 2026. Implementation and field validation are separate: code presence is not proof of detection accuracy or data coverage.

| Synopsis outcome | Implementation and verification | Remaining real-world evidence |
| --- | --- | --- |
| Automated news/AIS pipeline | RSS time windows/deduplication, optional GDELT, scheduler, AISStream subscription, real persisted positions/profiles/coverage and freshness API | GDELT availability; sustained regional AIS coverage |
| LLM extraction and credible risk classification | Real Gemini extraction verified; schema handling, retry/circuit fallback, provenance, deterministic scores and bands | Wider independent extraction/scoring evaluation and calibration |
| Supplier-route-port-refinery graph | NetworkX propagation, possible supplier paths, explainable refinery contributions, equivalent graph table | Procurement-specific dependency data remains unavailable; shares are explicitly illustrative |
| Official oil trade data | Real PPAC monthly PDF and EIA national brief ingested, with units, periods, source URLs, hashes and previous-snapshot fallback | These public aggregates cannot establish refinery-level dependencies |
| Live dashboard and alerting | React charts, history, source freshness, retained snapshots, separate replay datasets, evidence-linked threshold alerts | Sustained operational monitoring; hosting is not required for the local prototype |
| Historical evidence/RAG | Persistent article corpus, BM25 retrieval, citation-constrained Gemini generation and honest retrieval fallback | Broader retrieval/answer faithfulness evaluation |
| Historical accuracy validation | Reproducible heuristic/Gemini runner; checked-in source-reviewed pilot, measured confusion counts and written error analysis | Independent original-article corpus, untouched event-level test set, calibrated thresholds, combined AIS validation and lead time |
| Final documentation/demo | Current README, architecture, limitations, validation protocol/report and professor walkthrough | Incorporate real field-validation results before calling the full project finished |

## Live verification

Local verification: 77 offline backend tests pass; React production build and ESLint pass. GitHub Actions checks are configured for Windows and Ubuntu. Local test success is not a claim that remote CI has already completed.

`output/verification/live_sources.json` records successful RSS, Brent and one valid Gemini extraction; GDELT was unavailable. `output/verification/live_cycle.json` records a complete live pipeline run: 48 RSS articles, 29 extracted assessments, all using Gemini in that run. Official trade adapters succeeded against both sources. Real AIS positions subsequently arrived and persisted in the Hormuz research box; `output/verification/ais_live.json` records counts and coverage. Red Sea observations remain unavailable. The first 40-second diagnostic had no positions; later reception is separately verified, not backdated.

The live RAG verification returned a provider HTTP 503 and correctly displayed retained evidence with valid citation links. Structured generation and citation rejection are covered by offline tests; successful live synthesis is not claimed from that failed request. See `output/verification/rag.json`.

## Implemented AIS rule

The default baseline needs 720 prior hours with at least 80% heartbeat-minute coverage and positive observed reception, followed by a fresh, sufficiently covered current hour. Zero-current-observation windows abstain. A large observed activity reduction can corroborate existing news risk by at most 10% of remaining score headroom. It does not create a risk event without news or establish a physical closure. This rule still needs real-data validation.

## Measured pilot

The source-reviewed pilot has three route-windows, two event families, two positives and one control. Both heuristic-only and Gemini-only runs miss the two positives at the existing 30-point threshold. Precision is undefined because there are no positive predictions; recall and F1 are zero. These results are shown honestly in the UI. Labels are provisional, source text is paraphrased and availability is reconstructed from publication dates; this is not a final held-out benchmark. See `VALIDATION_REPORT.md`.

## Work that requires additional data/time

1. Keep the collector running and establish whether the selected regions provide useful coverage. A real 30-day qualified baseline cannot be completed in this coding session.
2. Assemble and independently review a larger original-news historical corpus and quiet/control periods, then calibrate on development events and evaluate untouched events. The tiny pilot does not establish reliable performance.
3. Obtain refinery-specific procurement/dependency evidence if the final report intends to claim actual refinery exposure rather than modelled exposure.

No numerical accuracy, vessel traffic, procurement share or baseline history has been invented to close these gaps. Scenario simulation and automated procurement rerouting remain Project-II. Roopal owns AIS and integration; teammates can contribute labels/source review without blocking further coding.
