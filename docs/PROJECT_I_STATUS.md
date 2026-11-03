# Project-I completion status

Updated 3 November 2026. This tracks the synopsis outcomes, not just code presence. Roopal owns AIS and integration; contributions from other team members can be incorporated, but they are not assumed.

## Implemented in this increment

- React launcher, Vite API proxy, explicit development CORS, graph ref fix/keyboard access and equivalent connection table.
- Correct 0-100 signal scale, exact high-route count, extractor-prefix counting, current-namespace counts and honest legacy-data provenance.
- Automatic dashboard polling, refreshable tabs, live/replay display switching and error notices.
- Separate replay namespaces, append-only risk/evidence/market snapshots and daily live monitoring history.
- Optional serial news/price scheduler and cross-process ingestion locks; background polling preserves a selected replay.
- AISStream backend collector, compressed subscription, bounded research regions, validated timestamped positions, deduplication, reconnect/backoff and health reporting.
- AIS activity API and React tab with explicit no-key, stale-data and baseline-collection states. No fabricated vessel or anomaly results.
- Persisted route threshold alerts with evidence and separate replay labelling.
- Offline heuristic news-only backtesting runner and a validation protocol that requires independent labels and guards against simple future/event/article leakage.
- Verification covers offline AIS frames/timestamp variants, namespace isolation, retained history, alert deduplication, ingestion locks and evaluation leakage. Production React build and ESLint pass. Compatible dependency updates removed all high-severity npm audit findings; 12 moderate findings remain in development lint dependencies. No forced major dependency changes were applied.

## Still required for full synopsis completion

1. **Live AIS verification:** create an AISStream key locally, run the collector, verify actual provider frames, geographic coverage and persistence across restart. User confirmed no AIS key is available yet.
2. **AIS risk features:** capture coverage/uptime, establish a defensible baseline, validate ship/cargo classification and crossing definitions, implement coverage-aware anomalies and evaluated score fusion. Current activity counts are all observed Class A positions, not tanker passage counts.
3. **Live-source verification:** verify a successful current RSS/GDELT/Brent run and actual Gemini extraction rather than key configuration alone. Inspect quotas and fallback provenance.
4. **PPAC/EIA data and graph grounding:** import real dated official data with provenance, distinguish national/country-level statistics from refinery-specific dependencies, replace only assumptions actually supported by evidence. Graph dependencies remain illustrative.
5. **RAG:** persistent article retrieval and cited contextual answers/evidence linking. This increment retains evidence but does not claim to implement RAG.
6. **Measured validation:** independently label real historical and quiet/control periods, freeze event-level splits, evaluate heuristic/Gemini/AIS components and the combined system, report precision/recall/F1 and lead time where supported. The runner alone is not a validation report.
7. **Operational QA:** exercise the scheduler and live collector over time, retention policy, outage recovery, data freshness and broader UI responsiveness; dependency audit and final deployment decision.
8. **Final report/demo:** update remaining historical ADR/demo documents to current architecture and prepare the professor walkthrough from verified results.

Scenario simulation and automated procurement rerouting remain Project-II. NetworkX satisfies the synopsis; a Neo4j migration is not required.

## Immediate next step

Get the AIS key using the provider's account flow; do not put it in chat or Git. Add `AISSTREAM_API_KEY` only in `backend/.env`. Until then offline AIS integration can be verified, but no claim of live vessel ingestion is justified. Continue the official trade-data and historical corpus work independently.
