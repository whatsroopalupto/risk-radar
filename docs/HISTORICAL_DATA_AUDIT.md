# Historical Data Audit

## Scope

This audit reviewed the Historical Event Labelling and Source Collection module without modifying the live ingestion pipeline, the live scoring rules, or unrelated project files. The review covered:

- all seven historical event rows in the processed dataset
- all source IDs and URLs in the source register
- the GDELT article collection script and validation logic
- the historical CSV integrity rules
- runtime test and validator evidence

## 1. Second-stage evidence corrections

The first pass used an explicit research label, but the evidence confidence was still too strong for several rows because the underlying sources were generic landing pages, partial-support context pages, or blocked/unverified URLs. The second-stage refinement makes evidence confidence conservative and explicitly separates publisher credibility from claim-level support.

### Evidence-confidence updates by event

- Gulf of Oman tanker attacks: HIGH -> MEDIUM
  - Reason: the source register contains one generic Reuters page and two partial-support institutional sources. The evidence supports route risk and market context, not a directly verified Indian crude-delivery effect.
- Abqaiq–Khurais oil facility attacks: HIGH -> MEDIUM
  - Reason: the source trail is institutionally credible but not direct article-level support proving the India-specific impact.
- Ever Given Suez Canal obstruction: HIGH -> MEDIUM
  - Reason: route disruption is well known, but the India-specific impact remains indirect and the source register still includes non-direct support pages.
- Russia–Ukraine invasion shock: HIGH -> MEDIUM
  - Reason: the initial invasion shock is stronger than the later conflict-wide assertions, but the source set is still not direct enough to justify a HIGH evidence-confidence rating for the route and India-impact claims.
- Red Sea shipping attacks and rerouting: HIGH -> MEDIUM
  - Reason: the row is materially relevant and sustained, but the cited sources were generic or blocked and do not directly verify the exact India-specific impact.
- MSC Aries seizure: MEDIUM -> LOW
  - Reason: the source register is weak and largely generic or blocked for this event, so the evidence confidence should not exceed LOW.
- Israel–Iran escalation: MEDIUM -> LOW
  - Reason: the event is current and relevant, but the current source set is mostly contextual, generic, or blocked and does not directly confirm the direct route impact or India-specific claim.

## 2. Severity and route-risk definitions

The historical dataset uses two different labels that should not be conflated.

### Severity
The `severity` field describes the intensity of the event or disruption itself. Allowed values match the validation code exactly:

- LOW
- MEDIUM
- HIGH
- CRITICAL

This reflects the event’s geopolitical or operational severity, not whether the route was actually impacted in a verified way.

### Route-risk label
The `route_risk_label` is a separate operational label and is limited to:

- LOW
- MEDIUM
- HIGH

It describes the route-risk consequence for shipping, freight, or corridor exposure. A route-risk label is not a claim that Indian crude deliveries were directly interrupted or that the event was fully verified.

## 3. Red Sea event date handling

The Red Sea event is recorded as follows:

- event_date: 2023-11-19
- event_end_date: 2025-06-30

This `event_end_date` is a research cutoff for the observation period, not a statement that the Red Sea crisis ended on that date. The record is kept as a historical observation window for analytical use, but the audit explicitly distinguishes:

- the actual event start date (2023-11-19)
- the research cutoff used for this dataset (2025-06-30)
- the fact that the underlying disruption may have continued beyond that cutoff

This is a dataset-design choice to keep a bounded historical window without pretending the route threat ended on the chosen date.

## 4. Russia-Ukraine event clarification

The Russia–Ukraine row is defined as the initial invasion shock, not the full 2022–present conflict. The dataset therefore keeps:

- event_date: 2022-02-24
- event_end_date: 2022-02-24
- event_name: Russia-Ukraine invasion shock

This distinguishes the initial shock window from the broader, ongoing war. The row is not intended to represent the complete conflict timeline.

## 5. Source register and source confidence

The source register deliberately separates two ideas:

- publisher credibility (`credibility_level`): how trustworthy the publisher or institutional source is
- claim-level evidence confidence (`evidence_confidence` in the event file): how strongly the source trail supports the specific historical claim

This separation matters because a credible publisher can still have no direct article-level proof for the exact claim being made. The stage-2 update retains `credibility_level` where it is high, but lowers the event-level evidence confidence where the source trail is generic, partial, or blocked.

## 6. India-specific impact controls

The event file now uses qualified wording such as:

- possible route exposure
- possible market and procurement pressure
- no direct evidence of confirmed crude-delivery disruption

This avoids over-claiming that Indian crude deliveries, freight costs, insurance, or procurement were directly affected unless the source trail specifically establishes those claims. Several earlier rows asserted stronger Indian-impact language than the source register supported.

## 7. Source replacement policy

Generic publisher homepages and section pages were not upgraded to verified evidence without direct citation. The source register keeps these records only when they are relevant to the event, but they remain clearly marked as requiring verification. No exact URLs, publication dates, or article titles were invented.

## 8. Issues found and corrected

### Issues found

1. Generic landing-page URLs were used as if they were direct evidence pages.
2. Reuters, IEA, and MARAD pages returned 401/403 or were otherwise blocked during automated validation.
3. Some event records overstated the Indian impact by implying direct crude-delivery disruption without direct support.
4. Evidence confidence was too high for rows whose sources were partial support or generic context pages.
5. The Red Sea end date was not clearly distinguished from a research cutoff and could be mistaken for the actual end of the conflict.
6. The Russia–Ukraine record did not clearly state whether it represented the initial invasion shock or the longer war.
7. Severity and route-risk labels were not clearly separated in the audit language.

### Corrections made

- Reduced all event evidence confidence values from HIGH to MEDIUM or LOW where the source trail did not support a stronger claim.
- Kept the source register URLs conservative and did not upgrade generic homepages to direct article URLs without verification.
- Clarified the Red Sea observation period as 2023-11-19 to 2025-06-30 and explicitly identified the 2025-06-30 end as a research cutoff, not an end-of-event claim.
- Renamed the Russia–Ukraine record to “Russia-Ukraine invasion shock” and clarified that it represents the initial shock window rather than the whole conflict.
- Reworded the India-impact fields so they describe route and market risk as possible or indirect unless directly evidenced.
- Updated this audit to describe the severity scale and route-risk scale separately and explicitly.
- Left the live ingestion pipeline, live GDELT connector, and risk-scoring engine unchanged.

## 9. Remaining unresolved issues

- The project still does not contain a curated set of direct article-level URLs for all historical claims.
- Reuters, IEA, and MARAD pages remain partially blocked or unusable in this environment for automated verification.
- Several source rows still need direct article substitutions before they can be promoted beyond a research or “requires review” status.
- A future stage should add a manual source-approval workflow so that only direct, dated article URLs are accepted as “verified” evidence.
- The historical module remains a conservative research layer, not a final verified archive or operational fact base.

## 10. Final assessment

The data set is now more conservative, better explained, and more defensible as a historical research layer. It still does not meet the standard of a final verified archive, and it should remain explicitly flagged as proposed and review-required until the source register is upgraded with exact article-level citations.

This is a suitable research dataset for structured analysis and future backtesting preparation, but not for publication as a fully verified factual record of all events or impacts.
