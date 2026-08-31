# Scoped limitations

- AIS is stubbed: useful vessel features require weeks of baseline data, which Phase 1 cannot generate.
- GDELT is optional because the development/demo network blocks it; connectors make it swappable.
- Graph shares are **ILLUSTRATIVE — replace with PPAC monthly import data in Phase 2**.
- Accuracy metrics wait until the feature set is frozen; AIS would invalidate earlier tuning.
- Credibility is static; learned weights require a scored corpus produced in Phase 1.
- SQLite is intentionally single-user and local.
