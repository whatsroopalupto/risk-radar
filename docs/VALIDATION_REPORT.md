# Historical validation pilot and error analysis

## Scope

This is a small retrospective diagnostic, not final validation of the deployed system. The checked-in corpus `backend/data/evaluation/pilot_cases.json` contains three provisionally labelled route-windows across two event families. Source text is an analyst paraphrase of official reporting, not a captured historical news feed. `fetched_at` is explicitly a publication-date availability proxy, not a claimed actual historical fetch. Later revisions to source pages cannot be ruled out.

Labels describe documented physical/logistical disruption, not merely geopolitical tension. The two Red Sea windows are positive because official reporting documents diversion and disrupted petroleum transport. The Hormuz control is negative for blockage as of the cited report, while still acknowledging geopolitical risk. The two Red Sea windows are correlated observations of one crisis.

## Sources and cases

- Red Sea, 11 June 2024: [EIA report on cargo diversion around Africa](https://www.eia.gov/todayinenergy/detail.php?id=62263).
- Red Sea, 11 October 2024: [EIA report on reduced Bab el-Mandeb petroleum flows](https://www.eia.gov/TodayinEnergy/detail.php?id=63446).
- Hormuz, 16 June 2025: [EIA report distinguishing regional tensions from a blocked passage](https://www.eia.gov/todayinenergy/detail.php?id=65504).

Labels were provisionally reviewed against those sources by Codex. Independent human annotation and review are still required. Saved demonstration fixtures were not used as ground truth.

## Method and measured results

The existing 30/100 flag threshold was kept unchanged. Each case uses only the article available within its declared window and computes news-only route risk. No historical AIS or market data was fabricated. Availability cutoffs, dataset hashes, extraction provenance and per-case outputs are recorded by the runner. The Gemini run uses actual validated Gemini outputs after handling overlong evidence fields; the heuristic run uses the deterministic fallback.

| Method | TP | FP | FN | TN | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Heuristic news-only | 0 | 0 | 2 | 1 | Undefined | 0% | 0% |
| Gemini news-only | 0 | 0 | 2 | 1 | Undefined | 0% | 0% |

Machine-readable results: `output/evaluation/pilot_heuristic.json` and `output/evaluation/pilot_gemini.json`. The dashboard presents the same reports. Undefined precision is not perfect precision and is not replaced by 100%.

## Interpretation

Both methods miss the positive single-document windows at the existing threshold. The scoring product reduces evidence through confidence, static source credibility and recency, while production route aggregation normally combines multiple articles. This pilot therefore exposes a threshold/evidence-support weakness rather than establishing good detection accuracy. Its narrow input construction and retrospective availability proxy also limit what can be inferred. The threshold was not changed to fit these three cases.

The non-blockage control is not flagged, which is useful but insufficient evidence of low false-positive rates. No detection lead time is reported: actual contemporaneous feed availability and independently established first-warning times are unavailable.

## Required next validation

Collect original historical reporting and independent documented event outcomes, include quiet periods and multiple routes/event types, resolve uncertain labels, freeze event-level development/test splits, and tune only on development events. Evaluate heuristic, Gemini, news+market and coverage-valid AIS fusion separately. Report errors, class/event counts, confidence intervals appropriate to the sample and lead time only when timestamps support it.

Until then, the defensible claim is a working explainable prototype with measured pilot limitations, not a high-accuracy validated early-warning system.
