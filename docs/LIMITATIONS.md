# Scoped limitations

- AIS is stubbed: useful vessel features require weeks of baseline data, which Phase 1 cannot generate.
- GDELT is optional because the development/demo network blocks it; connectors make it swappable.
- Graph shares are **ILLUSTRATIVE — replace with PPAC monthly import data in Phase 2**.
- Accuracy metrics wait until the feature set is frozen; AIS would invalidate earlier tuning.
- Credibility is static; learned weights require a scored corpus produced in Phase 1.
- SQLite is intentionally single-user and local.
- Gemini free-tier rate limits cap how much of a large live run gets true AI classification; a sleep-based throttle plus a circuit breaker (fall back to the heuristic engine after the first 429, rather than retrying into the quota) keeps every run fast and honest regardless. A paid tier removes the ceiling; that's a Phase 2/3 cost decision, not a Phase 1 defect.
- Live ingestion and the replay scenario intentionally share one display slot so both render through the same dashboard views; a LIVE DATA / REPLAY SCENARIO badge disambiguates which is currently shown. Separate namespaces for side-by-side comparison are a Phase 2 candidate.
