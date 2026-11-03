import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
interface RiskAlert {
  id: number; dataset: string; route_name: string; score: number; threshold: number;
  occurred_at: string; kind: string;
  evidence: { signal_id: string; title: string; url: string | null; explanation: string; source: string }[];
}
export default function RiskAlerts({ refreshKey }: { refreshKey: number }) {
  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
  const [error, setError] = useState(false);
  useEffect(() => {
    let active = true;
    apiClient<RiskAlert[]>("/api/alerts").then((result) => {
      if (active) { setAlerts(result); setError(false); }
    }).catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [refreshKey]);
  return <section className="graph-panel" aria-label="Risk alerts">
    <h2>Risk Alerts</h2>
    <p>Recorded evidence-backed crossings of 30 or 65 / 100, or the first elevated observation. Replay alerts are labelled separately.</p>
    {error && <p role="status">Unable to refresh alerts; previously displayed alerts may be stale.</p>}
    {!error && alerts.length === 0 && <p>No recorded alerts for this dataset.</p>}
    {alerts.map((alert) => <details key={alert.id}>
      <summary>{alert.dataset.startsWith("replay:") ? "ILLUSTRATIVE REPLAY · " : ""}{alert.route_name}: {alert.score.toFixed(1)} / 100 · threshold {alert.threshold}</summary>
      <p>{alert.kind.replaceAll("_", " ")} · {alert.occurred_at} UTC (historical event clock for replay)</p>
      <ul>{(alert.evidence ?? []).map((evidence) => <li key={evidence.signal_id}>
        {evidence.url && !alert.dataset.startsWith("replay:") && /^https?:\/\//i.test(evidence.url) ? <a href={evidence.url} target="_blank" rel="noopener noreferrer">{evidence.title}</a> : evidence.title}
        <p>{evidence.source}: {evidence.explanation}</p>
      </li>)}</ul>
    </details>)}
  </section>;
}
