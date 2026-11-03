import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
interface ValidationData {
  notice: string; reports: { method: string; validation_status: string; sample_size: number; distinct_events: number;
    metrics: { precision: number | null; recall: number | null; f1: number | null; true_positive: number; false_positive: number; false_negative: number; true_negative: number };
    limitations: string[]; cases: { case_id: string; label: boolean; predicted: boolean; score: number; label_sources: string[] }[] }[];
}
const percentage = (value: number | null) => value === null ? "Undefined" : `${(value * 100).toFixed(1)}%`;
export default function ValidationTab() {
  const [data, setData] = useState<ValidationData | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => { let active = true; apiClient<ValidationData>("/api/validation").then((value) => { if (active) setData(value); }).catch(() => { if (active) setError(true); }); return () => { active = false; }; }, []);
  return <section><h2>Historical Validation</h2>
    {error && <p role="alert">Validation reports could not be loaded.</p>}
    {data && <><p>{data.notice}</p>{data.reports.length === 0 && <p>No measured report is available yet.</p>}
      {data.reports.map((report, index) => <article key={index} className="graph-panel">
        <h3>{report.method}</h3><p>{report.sample_size} route-windows across {report.distinct_events} event families · {report.validation_status.replaceAll("_", " ")}</p>
        <p>Precision: {percentage(report.metrics.precision)} · Recall: {percentage(report.metrics.recall)} · F1: {percentage(report.metrics.f1)}</p>
        <p>True positives {report.metrics.true_positive} · False positives {report.metrics.false_positive} · False negatives {report.metrics.false_negative} · True negatives {report.metrics.true_negative}</p>
        <div className="vessel-table-scroll"><table><caption>Case-level errors and evidence</caption><thead><tr><th>Case</th><th>Documented disruption</th><th>Flagged ≥30</th><th>Score</th><th>Sources</th></tr></thead>
          <tbody>{report.cases.map((item) => <tr key={item.case_id}><td>{item.case_id.replaceAll("_", " ")}</td><td>{item.label ? "Yes" : "No"}</td><td>{item.predicted ? "Yes" : "No"}</td><td>{item.score.toFixed(1)}</td><td>{item.label_sources.map((url, sourceIndex) => <a key={url} href={url} target="_blank" rel="noopener noreferrer">Source {sourceIndex + 1} </a>)}</td></tr>)}</tbody></table></div>
        <details><summary>Interpretation and limitations</summary><ul>{report.limitations.map((item) => <li key={item}>{item}</li>)}</ul></details>
      </article>)}</>}
  </section>;
}
