# Historical validation protocol

Status: evaluation runner and a measured three-window provisional pilot report are implemented. Independently reviewed original-news corpus and final full-system evaluation remain pending. Existing replay fixtures are explicitly illustrative scenarios, not verified ground truth. Do not label their outputs as historical accuracy. See `VALIDATION_REPORT.md` for the pilot's missed detections and limitations.

## Unit and target

Use a route-window (a route and a dated observation window). A positive label means a documented physical/logistical disruption or a separately defined warning target for that route within the predeclared target period. Define that target before labelling: geopolitical tension alone and a completed route closure are different outcomes. Label uncertainty explicitly and exclude unresolved cases from primary metrics, documenting exclusions.

Include independently sourced disruption events and quiet/control periods. Retain event dates, source URLs, label rationale, annotator and disagreements. Include multiple routes and event types. Do not manufacture AIS history from news reports.

## Split and timing

Keep all windows for one event in a single split. Freeze development/test splits by event, preferably chronologically, before calibration. Do not tune on the held-out test split. Article publication and availability times must both precede the prediction instant. The runner enforces availability and rejects simple event/article leakage. Deduplicated/syndicated reports still require manual cross-split review.

## Runner

`backend/app/evaluation.py` accepts a JSON array of labelled cases. Required fields: `case_id`, `event_id`, `split` (`development` or `test`), `route_id`, timezone-aware `window_start` and `as_of`, boolean `disruption`, `label_sources` (URLs), `label_rationale`, `labelled_by`, and `signals` using the existing Signal schema. Generate the exact schema with `LabelledCase.model_json_schema()` if needed.

From the project root:

```powershell
.\.venv\Scripts\python.exe -m backend.app.evaluation path\to\labels.json --split development --threshold 30 --output output\evaluation\development.json
.\.venv\Scripts\python.exe -m backend.app.evaluation path\to\labels.json --split test --threshold 30 --output output\evaluation\test.json
```

This first runner measures the deterministic heuristic **news-only baseline**, not Gemini/AIS fusion. It never calls external services or writes the live database. It reports confusion counts, precision, recall, F1, class counts, event counts and per-case errors. Undefined metrics are null. Add measured Gemini and coverage-valid AIS evaluation before claiming full-system accuracy; report component ablations.

## Final report requirements

- Dataset selection, evidence sources, target definition, exclusions, split dates, class balance and independent event counts.
- Fixed scoring/configuration version, thresholds and extractor provenance.
- Precision/recall/F1 and false-positive/false-negative examples, per route/event type where sample sizes permit.
- Detection lead time only where both the first available warning and independently documented onset are known; count undetected events separately.
- Limitations: source coverage, news publication lag, AIS outages, illustrative refinery shares, correlated windows and small samples.

No numeric accuracy claim is justified until real labels and a reproducible report exist.
