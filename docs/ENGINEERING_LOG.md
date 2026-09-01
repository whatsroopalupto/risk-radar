# Engineering Log — Hardening the Risk Radar

What the system does, everything built and fixed to get it demo-ready, and
how to frame what's left when a professor asks. Companion documents:
`ARCHITECTURE.md`, `LIMITATIONS.md`, `DEMO_SCRIPT.md`.

---

## 1. What it is

An early-warning system for India's crude-oil supply chain. News about the
Strait of Hormuz, the Red Sea, and related chokepoints is turned into
structured facts by an AI classifier — or a deterministic rule-based
fallback when the AI is unavailable — scored by a fixed, auditable formula
(never by the AI itself), propagated across a supplier → route → port →
refinery network, and shown on a dashboard built for a procurement analyst,
not a developer.

```
News feeds → Relevance filter → AI / rule-based extraction →
Deterministic scoring → Route & refinery propagation → Dashboard
```

The scoring formula is `type_weight × severity × confidence × credibility
× recency_decay × speculative_discount` — six numbers multiplied together,
visible per-signal on the dashboard down to the arithmetic. Nothing about
risk severity is ever decided by the LLM; it only extracts facts.

## 2. What it does today

- **Ingests** real news via RSS (primary) and GDELT (optional, degrades
  gracefully), plus Brent crude price moves as corroboration.
- **Classifies** each headline — event type, severity, chokepoints,
  confidence — with Gemini, falling back automatically and honestly to a
  rule-based engine whenever the AI is rate-limited or unavailable.
- **Scores** every signal deterministically, aggregates per shipping route
  (noisy-OR), and propagates that into per-refinery exposure across a
  10-refinery, 4-route network.
- **Replays** two independently built historical scenarios — Hormuz, June
  2025, and the Red Sea / Bab-el-Mandeb disruption, December 2023 — for a
  demo that never depends on live news existing.
- **Dashboard:** a live status strip, five KPI cards, an Intelligence
  Analytics tab (event types, AI-vs-rule-based mix, severity/confidence,
  credibility), a cumulative risk-trend chart, a signal feed with full
  score breakdowns, a persisted ingestion history, and a supply-chain
  graph — every number opens a plain-language explanation on click.

## 3. How we got here

1. **Started** from a working Phase 1 skeleton that was functionally
   complete but visually generic, and gave no visible proof the AI
   classifier was doing real work.
2. **Rebuilt the dashboard:** truthful backend health reporting, a light
   analyst-report theme with no emoji or internal build jargon, clickable
   plain-language explanations everywhere, a dedicated analytics tab, and
   a real day-by-day risk trend instead of a snapshot.
3. **Wired in a real Gemini key**, which immediately surfaced two real
   correctness bugs — a schema-retry step that was specified but never
   implemented, and no rate-limit throttling at all — both fixed with the
   actual graceful-degradation pattern the design always called for.
4. **Added a second replay scenario**, which surfaced and fixed a
   chokepoint name-matching bug in the fallback classifier (real headlines
   spell "Bab-el-Mandeb" several ways; the code only matched one).
5. **Hardened the rest:** the one-click launcher, RSS timeouts,
   test-database isolation, and half a dozen smaller data-honesty bugs —
   the full list is next.

## 4. Problems hit, and the actual fix

Not just the symptom — what was actually wrong, and what changed.

| Symptom | Root cause | Fix |
|---|---|---|
| Dashboard crashed on "Run Live Ingestion" | No error handling around the button; a live AI-classified run can legitimately run long | Try/except with a friendly message; realistic client timeout |
| Live ingestion used 0% AI classification | 302 signals → 38 Gemini calls fired with no delay → instant rate-limiting on nearly every one | Sleep-based throttle plus a circuit breaker: first rate-limit stops further attempts, falls to the rule-based engine |
| A slow RSS feed could hang far longer than expected | The feed parser enforces no request timeout at all | Fetch with a client that has a real 20s timeout; hand the parser raw bytes |
| Running tests overwrote the live demo database | Tests were never isolated to their own database, despite that being required | Test setup now forces an isolated database and the offline classifier first |
| The one-click launcher hung forever on first run | A fresh machine blocks on a one-time interactive setup prompt no subprocess can answer | Pre-seeded the config; launcher now runs headless with input closed |
| Every signal showed "Recent" instead of a real date | A dict default-setter silently refuses to overwrite an existing null value | Overwrite directly from the database column instead of defaulting |
| Most real news domains scored at the weakest credibility tier | One tier was specified but unreachable — a dead code branch | Fixed the fallthrough so it's actually reachable |
| Chokepoint mentions of "Bab-el-Mandeb" went undetected | Fallback classifier matched one exact spelling; real headlines use several | Match every common spelling instead of one string |
| Status chips read "Active" for a source that found nothing | "Reachable" and "found something new" were shown as the same green label | A reachable-but-empty source gets a distinct neutral label |
| Small icons beside every heading did nothing when clicked | Framework auto-adds a hover anchor link that only rewrites the URL, invisibly | Hidden globally via a style rule |
| Large empty gap above the page title | The framework's own toolbar stacked with extra custom padding | Removed the toolbar, trimmed the padding |

## 5. Framing what's left for review

**How to say it:** each item below is a scoped engineering decision, the
same way the project's own limitations document frames the Phase 1/2/3
split — not an unfinished corner. The fix that exists today is itself the
assessable artifact.

- **Gemini free-tier rate limits** cap how much of a large live run gets
  true AI classification — a quota limit of the free tier, not a pipeline
  flaw. A paid tier or a queued worker removes the ceiling; neither belongs
  in a two-day Phase 1 skeleton.
- **Live and replay share one display slot**, deliberately, so both render
  through the same dashboard views. A "Live Data" / "Replay Scenario" badge
  makes it unambiguous which is currently shown; separate namespaces for
  side-by-side comparison are a natural Phase 2 addition.

Everything else from the original build — the AIS stub, static credibility
tiers, no accuracy metrics yet, single-user SQLite, illustrative graph
shares — is already covered in `LIMITATIONS.md` with the same framing.

## 6. Running it live

1. Double-click `run.bat` at the project root — it starts both services and
   opens the browser automatically.
2. For a guaranteed, instant walkthrough, pick a scenario and click
   **Replay Selected Scenario**.
3. To show it reading whatever is genuinely happening right now, click
   **Run Live Ingestion** and watch the "Live Data" badge and AI-Classified
   Share update honestly.
