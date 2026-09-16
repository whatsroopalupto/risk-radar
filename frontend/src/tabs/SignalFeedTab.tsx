import { useEffect, useState } from "react";

import { getSignals } from "../api/endpoints";
import type { RiskAssessment } from "../types/signals";

function SignalFeedTab() {
  const [signals, setSignals] = useState<RiskAssessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadSignals() {
      try {
        const data = (await getSignals(100)) as RiskAssessment[];
        setSignals(data);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load signal feed.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadSignals();
  }, []);

  if (loading) {
    return (
      <section className="signal-feed-tab">
        <h2>Signal Feed</h2>
        <p>Loading risk signals...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="signal-feed-tab">
        <h2>Signal Feed</h2>
        <p>Unable to load signals: {error}</p>
      </section>
    );
  }

  return (
    <section className="signal-feed-tab">
      <h2>Signal Feed</h2>

      <p className="section-description">
        Recent signals processed by the geopolitical risk classification
        pipeline.
      </p>

      {signals.length === 0 ? (
        <p>No risk signals available.</p>
      ) : (
        <div className="signal-list">
          {signals.map((signal) => (
            <article className="signal-card" key={signal.signal_id}>
              <div className="signal-card-header">
                <div>
                  <h3>
                    {signal.title ?? "Untitled signal"}
                  </h3>

                  <div className="signal-source">
                    {signal.source_name ?? "Unknown source"}
                  </div>
                </div>

                <div
                  className={`signal-risk risk-${signal.band}`}
                >
                  {signal.final_score.toFixed(1)} / 100
                </div>
              </div>

              <div className="signal-meta">
                <span>
                  Risk:{" "}
                  <strong className={`risk-${signal.band}`}>
                    {signal.band}
                  </strong>
                </span>

                <span>
                  Event:{" "}
                  <strong>
                    {signal.extraction.event_type.replaceAll(
                      "_",
                      " ",
                    )}
                  </strong>
                </span>

                <span>
                  Severity:{" "}
                  <strong>
                    {(signal.extraction.severity * 100).toFixed(0)}
                  </strong>
                </span>

                <span>
                  Confidence:{" "}
                  <strong>
                    {(signal.extraction.confidence * 100).toFixed(0)}%
                  </strong>
                </span>
              </div>

              {signal.extraction.evidence && (
                <p className="signal-evidence">
                  {signal.extraction.evidence}
                </p>
              )}

              <div className="signal-footer">
                <span>
                  {signal.published_at
                    ? new Date(
                      signal.published_at,
                    ).toLocaleString("en-IN")
                    : "Publication time unavailable"}
                </span>

                {signal.url && (
                  <a
                    href={signal.url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    View source
                  </a>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default SignalFeedTab;