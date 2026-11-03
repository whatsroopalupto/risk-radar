"""Reproducible news-only backtest against independently supplied event labels.

Run from the repository root:
  .venv/Scripts/python -m backend.app.evaluation labels.json --output results.json
This does not call external APIs, use the live database, or invent event labels.
"""
import argparse
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field, model_validator
from .graph.builder import load_seed
from .pipeline.extractors.heuristic import HeuristicExtractor
from .pipeline.normalize import dedupe
from .pipeline.relevance import is_relevant
from .pipeline.scorer import noisy_or, score_extraction
from .schemas import Signal


class LabelledCase(BaseModel):
    case_id: str
    event_id: str
    split: Literal["development", "test"]
    route_id: str
    window_start: datetime
    as_of: datetime
    disruption: bool
    label_sources: list[str] = Field(min_length=1)
    label_rationale: str = Field(min_length=10)
    labelled_by: str = Field(min_length=1)
    signals: list[Signal]
    label_review_status: Literal["unreviewed","provisional_source_review","independent_review"] = "unreviewed"
    text_basis: str = "original_reporting"
    availability_basis: str = "recorded_fetch_time"

    @model_validator(mode="after")
    def validate_window(self):
        if self.as_of.tzinfo is None or self.window_start.tzinfo is None:
            raise ValueError("Evaluation dates must include timezones")
        if self.window_start >= self.as_of:
            raise ValueError("window_start must precede as_of")
        if any(not url.startswith(("https://", "http://")) for url in self.label_sources):
            raise ValueError("Labels need source URLs")
        return self


def metrics(labels, predictions):
    tp = sum(a and p for a,p in zip(labels,predictions))
    fp = sum(not a and p for a,p in zip(labels,predictions))
    fn = sum(a and not p for a,p in zip(labels,predictions))
    tn = sum(not a and not p for a,p in zip(labels,predictions))
    precision = tp/(tp+fp) if tp+fp else None
    recall = tp/(tp+fn) if tp+fn else None
    return {"true_positive":tp,"false_positive":fp,"false_negative":fn,"true_negative":tn,
            "precision":precision,"recall":recall,
            "f1":2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}


def evaluate(cases: list[LabelledCase], split="test", threshold=30.0, extractor=None):
    if not 0 <= threshold <= 100:
        raise ValueError("threshold must be between 0 and 100")
    if len({case.case_id for case in cases}) != len(cases):
        raise ValueError("case_id must be unique")
    events = {}
    articles = {}
    for case in cases:
        if case.event_id in events and events[case.event_id] != case.split:
            raise ValueError("An event cannot appear in both development and test splits")
        events[case.event_id] = case.split
        for signal in case.signals:
            # Stable connector IDs and exact content both guard simple leakage.
            for identity in (signal.signal_id, signal.title.strip().casefold()):
                if identity in articles and articles[identity] != case.split:
                    raise ValueError("An article cannot appear in both development and test splits")
                articles[identity] = case.split
    routes = {route["id"]:route for route in load_seed()["routes"]}
    results = []
    extractor=extractor or HeuristicExtractor()
    provenance=set()
    for case in cases:
        if case.route_id not in routes:
            raise ValueError(f"Unknown route: {case.route_id}")
        if case.split != split:
            continue
        # Availability is determined by fetched_at as well as publication time.
        available = [signal for signal in case.signals
            if case.window_start <= signal.published_at <= case.as_of and signal.fetched_at <= case.as_of]
        unique, _ = dedupe(available)
        relevant = [signal for signal in unique if is_relevant(signal)]
        extractions = extractor.extract(relevant)
        provenance.update(extraction.extractor for extraction in extractions)
        scores = [score_extraction(s.signal_id,e,s.source_name,s.published_at,case.as_of).final_score
                  for s,e in zip(relevant,extractions)
                  if set(e.affected_chokepoints) & set(routes[case.route_id]["chokepoints"])]
        score = noisy_or(scores)*100
        results.append({"case_id":case.case_id,"event_id":case.event_id,"route_id":case.route_id,
            "label":case.disruption,"predicted":score>=threshold,"score":score,
            "available_articles":len(available),"excluded_unavailable_articles":len(case.signals)-len(available),
            "label_sources":case.label_sources,"label_rationale":case.label_rationale,
            "label_review_status":case.label_review_status,"text_basis":case.text_basis,
            "availability_basis":case.availability_basis,
            "extractions":[extraction.model_dump(mode="json") for extraction in extractions]})
    if not results:
        raise ValueError("No cases in selected split")
    return {"method":", ".join(sorted(provenance))+" news-only; no AIS or historical market corroboration",
        "validation_status":"independently_reviewed_labels" if all(row["label_review_status"]=="independent_review" for row in results) else "provisional_pilot_not_final_validation",
        "unit":"route-window", "split":split,"threshold":threshold,"sample_size":len(results),
        "positive_windows":sum(row["label"] for row in results),
        "negative_windows":sum(not row["label"] for row in results),
        "metrics":metrics([r["label"] for r in results],[r["predicted"] for r in results]),
        "limitations":["Label validity requires human review of the cited sources.",
            "Windows within an event are correlated; report event counts as well as window counts.",
            "These are news-only metrics, not measured performance of the combined AIS system.",
            "Publication-date proxies and paraphrased source text do not establish real historical ingestion or warning lead time.",
            "Undefined metrics are null, not evidence of perfect performance."],
        "distinct_events":len({r["event_id"] for r in results}),"cases":results}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--split",choices=("development","test"),default="test")
    parser.add_argument("--threshold",type=float,default=30)
    parser.add_argument("--extractor",choices=("heuristic","gemini"),default="heuristic")
    args=parser.parse_args()
    cases=[LabelledCase.model_validate(case) for case in json.loads(args.dataset.read_text(encoding="utf-8"))]
    extractor=None
    if args.extractor=="gemini":
        from .pipeline.extractors.gemini import GeminiExtractor
        extractor=GeminiExtractor()
    report=evaluate(cases,args.split,args.threshold,extractor)
    report["dataset_sha256"]=hashlib.sha256(args.dataset.read_bytes()).hexdigest()
    from .db import utcnow
    report["evaluated_at"]=utcnow().isoformat()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(f"Evaluated {report['sample_size']} labelled route-windows; results: {args.output}")


if __name__ == "__main__":
    main()
