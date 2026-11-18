import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
interface ValidationData {
  historical_dataset: { valid: boolean; event_count: number; source_count: number; errors: string[]; warnings: string[] };
  notice: string; reports: {
    method: string; validation_status: string; sample_size: number; distinct_events: number;
    metrics: { precision: number | null; recall: number | null; f1: number | null; true_positive: number; false_positive: number; false_negative: number; true_negative: number };
    limitations: string[]; cases: { case_id: string; label: boolean; predicted: boolean; score: number; label_sources: string[] }[]
  }[];
}
const percentage = (value: number | null) => value === null ? "Undefined" : `${(value * 100).toFixed(1)}%`;
export default function ValidationTab() {
  const [data, setData] = useState<ValidationData | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => { let active = true; apiClient<ValidationData>("/api/validation").then((value) => { if (active) setData(value); }).catch(() => { if (active) setError(true); }); return () => { active = false; }; }, []);
  return <section className="historical-validation-tab"><h2>Historical Validation</h2>
    {error && <p role="alert">Validation reports could not be loaded.</p>}
    {data && <><p>{data.notice}</p>
      <article className="validation-panel"><h3>Historical research register</h3>
        <p className="validation-register-meta">
          {data.historical_dataset.event_count} events · {data.historical_dataset.source_count} sources · Structure {data.historical_dataset.valid ? "passes" : "needs correction"}
        </p>
        <p>Research labels remain separate from measured evaluation cases. A valid CSV does not establish independently verified labels or model accuracy.</p>
        <details><summary>Review requirements ({data.historical_dataset.warnings.length})</summary><ul>{[...data.historical_dataset.errors, ...data.historical_dataset.warnings].map((item) => <li key={item}>{item}</li>)}</ul></details>
      </article>{data.reports.length === 0 && <p>No measured report is available yet.</p>}
      {data.reports.map((report, index) => <article key={index} className="graph-panel">
        <div className="validation-report-header">
          <h3 className="validation-report-title">
            {report.method.split(" news-only;")[0].replaceAll("-", " ")}
          </h3>
          <span className="validation-status">
            {report.validation_status.replaceAll("_", " ")}
          </span>
        </div>

        <p className="validation-report-description">
          This validation uses news data only. AIS observations and historical
          market data are not included as corroborating evidence.
        </p>

        <p className="validation-report-meta">
          {report.sample_size} route-windows across {report.distinct_events} event families
        </p>

        <div className="validation-metrics">
          <div className="validation-metric-card">
            <span>Precision</span>
            <strong>{percentage(report.metrics.precision)}</strong>
          </div>
          <div className="validation-metric-card">
            <span>Recall</span>
            <strong>{percentage(report.metrics.recall)}</strong>
          </div>
          <div className="validation-metric-card">
            <span>F1 Score</span>
            <strong>{percentage(report.metrics.f1)}</strong>
          </div>
        </div>

        <div className="ais-corridor-metrics validation-confusion">
          <div className="ais-metric">
            <span>TRUE POSITIVES</span>
            <strong>{report.metrics.true_positive}</strong>
            <small>Correctly flagged</small>
          </div>
          <div className="ais-metric">
            <span>FALSE POSITIVES</span>
            <strong>{report.metrics.false_positive}</strong>
            <small>Incorrectly flagged</small>
          </div>
          <div className="ais-metric">
            <span>FALSE NEGATIVES</span>
            <strong>{report.metrics.false_negative}</strong>
            <small>Missed cases</small>
          </div>
          <div className="ais-metric">
            <span>TRUE NEGATIVES</span>
            <strong>{report.metrics.true_negative}</strong>
            <small>Correctly not flagged</small>
          </div>
        </div>
        <div className="vessel-table-scroll"><table><caption>Case-level errors and evidence</caption><thead><tr><th>Case</th><th>Documented disruption</th><th>Flagged ≥30</th><th>Score</th><th>Sources</th></tr></thead>
          <tbody>{report.cases.map((item) => <tr key={item.case_id}><td>{item.case_id.replaceAll("_", " ")}</td><td>{item.label ? "Yes" : "No"}</td><td>{item.predicted ? "Yes" : "No"}</td><td>{item.score.toFixed(1)}</td><td>{item.label_sources.map((url, sourceIndex) => <a key={url} href={url} target="_blank" rel="noopener noreferrer">Source {sourceIndex + 1} </a>)}</td></tr>)}</tbody></table></div>
        <details><summary>Interpretation and limitations</summary><ul>{report.limitations.map((item) => <li key={item}>{item}</li>)}</ul></details>
      </article>)}</>}
  </section>;
}
