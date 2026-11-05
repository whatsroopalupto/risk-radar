import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { ChevronDown, ChevronUp } from "lucide-react";

interface RiskAlert {
  id: number;
  dataset: string;
  route_name: string;
  score: number;
  threshold: number;
  occurred_at: string;
  kind: string;
  evidence: {
    signal_id: string;
    title: string;
    url: string | null;
    explanation: string;
    source: string;
  }[];
}

export default function RiskAlerts({ refreshKey }: { refreshKey: number }) {
  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;

    apiClient<RiskAlert[]>("/api/alerts")
      .then((result) => {
        if (active) {
          setAlerts(result);
          setError(false);
        }
      })
      .catch(() => {
        if (active) setError(true);
      });

    return () => {
      active = false;
    };
  }, [refreshKey]);

  return (
    <section className="graph-panel risk-alerts-panel" aria-label="Risk alerts">
      <div className="risk-alerts-header">
        <div>
          <h2>Risk Alerts</h2>
          <p>Evidence-backed risk threshold crossings and elevated observations.</p>
        </div>
        <span className="risk-alerts-count">
          {alerts.length} {alerts.length === 1 ? "ALERT" : "ALERTS"}
        </span>
      </div>

      <p className="risk-alerts-note">
        Recorded crossings of 30 or 65 / 100, or the first elevated observation.
        Replay alerts are labelled separately.
      </p>

      {error && (
        <p className="risk-alerts-state" role="status">
          Unable to refresh alerts; previously displayed alerts may be stale.
        </p>
      )}

      {!error && alerts.length === 0 && (
        <p className="risk-alerts-state">No recorded alerts for this dataset.</p>
      )}

      <div className="risk-alerts-list">
        {alerts.map((alert) => {
          const isReplay = alert.dataset.startsWith("replay:");
          const severity = alert.threshold >= 65 ? "high" : "elevated";

          return (
            <details
              className={`risk-alert-card risk-alert-${severity}`}
              key={alert.id}
            >
              <summary className="risk-alert-summary">
                <span className="risk-alert-indicator" />

                <span className="risk-alert-main">
                  <span className="risk-alert-route">{alert.route_name}</span>
                  <span className="risk-alert-meta">
                    {alert.kind.replaceAll("_", " ")}
                  </span>
                </span>

                <span className="risk-alert-score">
                  <strong>{alert.score.toFixed(1)}</strong>
                  <span>/ 100</span>
                </span>

                <span className={`risk-alert-badge ${severity}`}>
                  {severity === "high" ? "HIGH" : "ELEVATED"}
                </span>
                <span className="risk-alert-chevron" aria-hidden="true">
                  <ChevronDown className="chevron-down" size={18} />
                  <ChevronUp className="chevron-up" size={18} />
                </span>
              </summary>

              <div className="risk-alert-expanded">
                <div className="risk-alert-details">
                  <span>Threshold: {alert.threshold}</span>
                  <span>{alert.occurred_at} UTC</span>
                </div>

                {isReplay && (
                  <span className="risk-alert-replay">
                    ILLUSTRATIVE REPLAY
                  </span>
                )}

                <div className="risk-alert-evidence">
                  <h4>Supporting Evidence</h4>

                  {alert.evidence?.length ? (
                    <ul>
                      {alert.evidence.map((evidence) => (
                        <li key={evidence.signal_id}>
                          {evidence.url &&
                            !isReplay &&
                            /^https?:\/\//i.test(evidence.url) ? (
                            <a
                              href={evidence.url}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {evidence.title}
                            </a>
                          ) : (
                            <strong>{evidence.title}</strong>
                          )}

                          <p>
                            <span>{evidence.source}</span>
                            {" · "}
                            {evidence.explanation}
                          </p>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No supporting evidence available.</p>
                  )}
                </div>
              </div>
            </details>
          );
        })}
      </div>
    </section>
  );
}     