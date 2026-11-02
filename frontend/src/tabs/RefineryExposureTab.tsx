import { useEffect, useState } from "react";

import { getRefineryExposures } from "../api/endpoints";
import type { RefineryExposure } from "../types/risk";

function RefineryExposureTab() {
  const [refineries, setRefineries] = useState<RefineryExposure[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadRefineries() {
      try {
        const data =
          (await getRefineryExposures()) as RefineryExposure[];

        setRefineries(data);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load refinery exposure data.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadRefineries();
  }, []);

  if (loading) {
    return (
      <section className="refinery-tab">
        <h2>Refinery Exposure</h2>
        <p>Loading refinery exposure data...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="refinery-tab">
        <h2>Refinery Exposure</h2>
        <p>Unable to load refinery exposure: {error}</p>
      </section>
    );
  }

  return (
    <section className="refinery-tab">
      <h2>Refinery Exposure</h2>

      <p className="section-description">
        Exposure of monitored Indian refineries to disruption across
        upstream maritime supply routes.
      </p>

      {refineries.length === 0 ? (
        <p>No refinery exposure data available.</p>
      ) : (
        <div className="refinery-grid">
          {refineries.map((refinery) => (
            <article
              className="refinery-card"
              key={refinery.refinery_id}
            >
              <div className="refinery-card-header">
                <div>
                  <h3>{refinery.name}</h3>
                  <p>{refinery.operator}</p>
                </div>

                <div
                  className={`refinery-risk risk-${refinery.band}`}
                >
                  {refinery.exposure_score.toFixed(1)} / 100
                </div>
              </div>

              <div className="refinery-band">
                Risk level:{" "}
                <strong className={`risk-${refinery.band}`}>
                  {refinery.band}
                </strong>
              </div>

              <div className="refinery-meta">
                Port: {refinery.port_id}
              </div>

              <div className="refinery-contributions">
                <h4>Route Contributions</h4>

                {refinery.contributions.length === 0 ? (
                  <p>No route contributions available.</p>
                ) : (
                  refinery.contributions.map((contribution) => (
                    <div
                      className="refinery-contribution"
                      key={contribution.route_id}
                    >
                      <span>{contribution.route_id}</span>

                      <span>
                        {(contribution.dependency_share * 100).toFixed(
                          0,
                        )}
                        % dependency ·{" "}
                        <span
                          className={
                            contribution.route_score >= 65
                              ? "risk-high"
                              : contribution.route_score >= 30
                                ? "risk-medium"
                                : "risk-low"
                          }
                        >
                          {contribution.route_score.toFixed(1)} risk
                        </span>
                      </span>
                    </div>
                  ))
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default RefineryExposureTab;