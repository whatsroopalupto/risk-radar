import { useEffect, useState } from "react";

import { getHealth, getSignals } from "../api/endpoints";
import type { HealthResponse } from "../types/api";
import type { EventType, RiskAssessment } from "../types/signals";

interface EventCount {
  type: EventType;
  count: number;
}

function IntelligenceAnalyticsTab() {
  const [signals, setSignals] = useState<RiskAssessment[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAnalytics() {
      try {
        const [signalData, healthData] = await Promise.all([
          getSignals(100),
          getHealth(),
        ]);

        setSignals(signalData as RiskAssessment[]);
        setHealth(healthData as HealthResponse);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load intelligence analytics.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadAnalytics();
  }, []);

  if (loading) {
    return (
      <section className="analytics-tab">
        <h2>Intelligence Analytics</h2>
        <p>Loading intelligence analytics...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="analytics-tab">
        <h2>Intelligence Analytics</h2>
        <p>Unable to load analytics: {error}</p>
      </section>
    );
  }

  const eventCounts: EventCount[] = signals.reduce<EventCount[]>(
    (counts, signal) => {
      const eventType = signal.extraction.event_type;
      const existing = counts.find((item) => item.type === eventType);

      if (existing) {
        existing.count += 1;
      } else {
        counts.push({
          type: eventType,
          count: 1,
        });
      }

      return counts;
    },
    [],
  );

  eventCounts.sort((a, b) => b.count - a.count);

  const highRiskSignals = signals.filter(
    (signal) => signal.band === "high",
  ).length;

  const mediumRiskSignals = signals.filter(
    (signal) => signal.band === "medium",
  ).length;

  const lowRiskSignals = signals.filter(
    (signal) => signal.band === "low",
  ).length;

  const speculativeSignals = signals.filter(
    (signal) => signal.extraction.is_speculative,
  ).length;

  const averageSeverity =
    signals.length > 0
      ? signals.reduce(
        (sum, signal) => sum + signal.extraction.severity,
        0,
      ) / signals.length
      : 0;

  const averageConfidence =
    signals.length > 0
      ? signals.reduce(
        (sum, signal) => sum + signal.extraction.confidence,
        0,
      ) / signals.length
      : 0;

  return (
    <section className="analytics-tab">
      <h2>Intelligence Analytics</h2>

      <p className="section-description">
        Analytical breakdown of the latest risk signals processed by the
        classification pipeline.
      </p>

      <div className="analytics-summary-grid">
        <article className="analytics-card">
          <div className="analytics-label">Signals analyzed</div>
          <div className="analytics-value">{signals.length}</div>
          <div className="analytics-description">
            Latest signals returned by the API
          </div>
        </article>

        <article className="analytics-card">
          <div className="analytics-label">High-risk signals</div>
          <div
            className={`analytics-value ${highRiskSignals === 0 ? "risk-clear" : "risk-alert"
              }`}
          >
            {highRiskSignals}
          </div>
          <div className="analytics-description">
            Classified as high risk
          </div>
        </article>

        <article className="analytics-card">
          <div className="analytics-label">Average severity</div>
          <div
            className={`analytics-value ${averageSeverity * 100 >= 65
              ? "severity-high"
              : averageSeverity * 100 >= 30
                ? "severity-medium"
                : "severity-low"
              }`}
          >
            {(averageSeverity * 100).toFixed(1)}
          </div>
          <div className="analytics-description">
            Across analyzed signals
          </div>
        </article>

        <article className="analytics-card">
          <div className="analytics-label">Average confidence</div>
          <div className="analytics-value">
            {(averageConfidence * 100).toFixed(1)}%
          </div>
          <div className="analytics-description">
            Extraction confidence
          </div>
        </article>
      </div>

      <div className="analytics-sections">
        <article className="analytics-panel">
          <h3>Risk Band Distribution</h3>

          <div className="analytics-bars">
            <div className="analytics-bar-row">
              <span>High</span>
              <div className="analytics-bar-background">
                <div
                  className="analytics-bar risk-high"
                  style={{
                    width: `${signals.length
                      ? (highRiskSignals / signals.length) * 100
                      : 0
                      }%`,
                  }}
                />
              </div>
              <strong>{highRiskSignals}</strong>
            </div>

            <div className="analytics-bar-row">
              <span>Medium</span>
              <div className="analytics-bar-background">
                <div
                  className="analytics-bar risk-medium"
                  style={{
                    width: `${signals.length
                      ? (mediumRiskSignals / signals.length) * 100
                      : 0
                      }%`,
                  }}
                />
              </div>
              <strong>{mediumRiskSignals}</strong>
            </div>

            <div className="analytics-bar-row">
              <span>Low</span>
              <div className="analytics-bar-background">
                <div
                  className="analytics-bar risk-low"
                  style={{
                    width: `${signals.length
                      ? (lowRiskSignals / signals.length) * 100
                      : 0
                      }%`,
                  }}
                />
              </div>
              <strong>{lowRiskSignals}</strong>
            </div>
          </div>
        </article>

        <article className="analytics-panel">
          <h3>Event Type Distribution</h3>

          {eventCounts.length === 0 ? (
            <p>No event-type data available.</p>
          ) : (
            <div className="event-type-list">
              {eventCounts.map((item) => (
                <div className="event-type-row" key={item.type}>
                  <span>{item.type.replaceAll("_", " ")}</span>
                  <strong>{item.count}</strong>
                </div>
              ))}
            </div>
          )}
        </article>

        <article className="analytics-panel">
          <h3>Extractor Information</h3>

          <div className="analytics-detail-row">
            <span>Active extractor</span>
            <strong>
              {health?.extractor?.active ?? "Unknown"}
            </strong>
          </div>

          <div className="analytics-detail-row">
            <span>Speculative signals</span>
            <strong>{speculativeSignals}</strong>
          </div>

          <div className="analytics-detail-row">
            <span>Stored assessments</span>
            <strong>
              {health?.db_counts?.assessments ?? 0}
            </strong>
          </div>
        </article>
      </div>
    </section>
  );
}

export default IntelligenceAnalyticsTab;