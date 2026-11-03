# Historical Event Labelling and Source Collection

## 1. Purpose

This module supports a separate historical research layer for geopolitical events that matter to India’s crude oil import routes. It is not a replacement for the live RSS and GDELT connectors used in the operational risk engine. Instead, it creates a transparent archive of historically significant geopolitical events, their route impacts, and the supporting evidence used to label them.

The aim is to make route-level historical analysis auditable. Analysts can review event dates, affected corridors, evidence confidence, and route-risk labels without mixing historical labels with live scoring logic.

## 2. GDELT API usage

The project’s operational GDELT connector is intentionally optional and resilient; it returns empty results when the API is unavailable, returns non-JSON data, or times out. The historical GDELT collection script follows the same principle.

The collection script uses the GDELT DOC API to discover recent articles with a list of geopolitical queries, including:

- Strait of Hormuz
- Gulf of Oman
- Red Sea
- Bab el-Mandeb
- Suez Canal
- crude oil supply disruption
- tanker attacks
- oil infrastructure attacks

Article metadata saved to the raw archive includes:

- title
- url
- domain
- seendate
- language
- source_country
- search_query
- collection_timestamp

The script deduplicates on URL and writes CSV output to `data/historical/raw/gdelt_articles.csv` without crashing when GDELT is unavailable.

### Important limitation

The GDELT DOC API is not a complete historical archive. It is useful for recent article discovery, not for proving that all historical events between 2019 and the present were fully captured. For older historical events, the project relies on institutional archives, original source statements, and corroborating reporting from Reuters, AP, and other established outlets. GDELT `seendate` is not the original publication date and is not the same thing as the actual event date.

## 3. Historical archive limits

Several important constraints apply:

- GDELT is a discovery layer for recent articles; it should not be described as a complete event archive.
- Historical event labelling uses research, not model predictions.
- The historical dataset is designed for auditability, not live scoring.
- A route-risk label is not automatically equivalent to the event severity or to a claim that India was directly disrupted.

## 4. Article collection method

The collection workflow is deliberately lightweight:

1. A list of queries is configured in the script.
2. Each query is submitted to the GDELT DOC API.
3. Responses are parsed carefully for required fields.
4. Records with missing title or URL are dropped.
5. Records with duplicate URLs are removed.
6. CSV output is generated in the raw history folder.

This keeps the process independent from the main ingestion path while still allowing historical discovery research to be captured later.

## 5. Event verification method

Each historical event in the processed dataset is documented using a research-first process:

- verify the date and event chronology
- identify the affected route or infrastructure
- separate the route event from the market effect
- assess India-specific impact only when supported by evidence
- assign a route-risk label that reflects the actual route exposure at the time
- record evidence confidence in a transparent way

The labels are not copied from the project’s real-time scoring model. They are assigned by documented human research and preserved as historical labels.

## 6. Severity and route-risk definitions

The dataset keeps severity and route risk distinct:

### Severity scale
The `severity` field describes the intensity of the event itself. Allowed values are exactly:

- LOW
- MEDIUM
- HIGH
- CRITICAL

This corresponds to the validation code used in the project. Severity is not the same as route-risk exposure.

### Route-risk labels
The `route_risk_label` describes the operational consequence for the route. Allowed values are:

- LOW
- MEDIUM
- HIGH

A route-risk label is a research label about corridor exposure, rerouting, or shipping consequences. It is not an assertion that the event was fully verified and it is not automatically equivalent to the event’s severity.

## 7. Evidence-confidence definitions

The `evidence_confidence` field is intended to communicate how strong the evidence base is for the specific claim being made:

- HIGH: strong official or institutional evidence and a direct, specific source trail for the claim
- MEDIUM: credible evidence exists, but some corroboration or direct article linking is still desirable
- LOW: significant uncertainty remains and the claim should be treated carefully

These categories are separate from publisher credibility and should not be treated as a numeric score in the live production pipeline.

## 8. Source confidence and publisher credibility

The source register keeps publisher credibility separate from claim-level evidence:

- `credibility_level` = publisher or institutional credibility
- `evidence_confidence` = claim-level confidence for the historical event

This distinction matters because a well-known institution can still be a weak direct source for a specific claim if the record is only a homepage or a general contextual page.

## 9. Dataset schema

The processed event dataset stores the following fields:

- event_id
- event_name
- event_date
- event_end_date
- region
- affected_route
- event_type
- severity
- route_risk_label
- india_impact
- india_impact_evidence
- evidence_confidence
- label_rationale
- source_ids
- review_status

The source register stores:

- source_id
- event_id
- source_name
- source_type
- publisher
- publication_date
- URL
- claim_supported
- credibility_level
- verification_notes

These relationships are intentionally explicit so that every historical label can be traced back to a documented evidence trail.

## 10. Source verification process

The source register is used to keep event claims traceable. Sources are reviewed for:

- institutional credibility
- date consistency
- original claim relevance
- whether the source is corroborating a route claim rather than mixing it with unrelated market commentary
- whether the URL is valid and the source is genuinely connected to the claim being made

When evidence is unclear or incomplete, the dataset keeps the relevant note explicit instead of guessing a stronger claim.

## 11. Data validation procedure

The script at `scripts/validate_historical_data.py` validates the dataset by checking:

- required columns exist
- event IDs are unique
- dates are valid ISO dates
- route-risk labels are within LOW, MEDIUM, HIGH
- severity values follow the documented scale
- required text fields are not empty
- source IDs referenced by historical events exist in the register
- URLs are validly formatted
- duplicate records are identified
- invalid rows are reported clearly without silently deleting them

This validation is a quality gate, not a data-cleaning step. Invalid data remains visible and must be corrected manually.

## 12. Historical backtesting preparation

This dataset is designed to support future analytical backtesting where the project evaluates whether route-risk signals, market context, or extraction logic would have provided usable early warnings. A backtesting pipeline should only use information that would have been available at the time a historical period is evaluated.

This means future work should avoid:

- using hindsight to label events after the fact
- mixing in later research that was not available to decision-makers at the time
- treating historical scenario replay as if it were accuracy backtesting

Historical scenario replay and forecast evaluation are different tasks:

- scenario replay tests whether a pipeline can reproduce a known historical storyline using saved data
- accuracy backtesting tests whether the pipeline’s output would have been useful at the time, which requires careful date-aware evaluation and often a benchmark set of non-event periods

Normal or low-risk control periods should be included in future evaluation planning so the model is tested against both disruption scenarios and quiet periods.

## 13. Data limitations and future improvements

The present dataset is intentionally conservative. It does not claim to be a full, complete historical archive of all geopolitical events affecting Indian crude import routes. It is a structured research subset designed for auditability and future early-warning work.

Future improvements could include:

- more granular source-level evidence tracking
- a versioned event review workflow
- explicit route impact scoring thresholds
- integration with a stories-based historical backtesting notebook or report
- expanded source coverage for minor but relevant incidents

The dataset should be considered a careful starting point for future validation work, not a final, complete economic archive.
