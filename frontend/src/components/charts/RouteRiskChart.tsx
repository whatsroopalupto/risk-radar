import { useEffect, useState } from "react";

import { getRouteRisks } from "../../api/endpoints";
import type { RouteRisk as ApiRouteRisk } from "../../types/risk";

interface RouteRisk {
  name: string;
  score: number;
  level: "High" | "Medium" | "Low";
}

interface RouteRiskChartProps {
  refreshKey: number;
}

function RouteRiskChart({ refreshKey }: RouteRiskChartProps) {
  const [routeRisks, setRouteRisks] = useState<RouteRisk[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadRouteRisks() {
      try {
        const data = await getRouteRisks();

        const mappedData: RouteRisk[] = (data as ApiRouteRisk[]).map(
          (route) => ({
            name: route.name,
            score: route.composite_score,
            level:
              route.band === "high"
                ? "High"
                : route.band === "medium"
                  ? "Medium"
                  : "Low",
          }),
        );

        setRouteRisks(mappedData);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load route risk data.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadRouteRisks();
  }, [refreshKey]);

  return (
    <section className="route-risk-section">
        <h3>Route Risk Comparison</h3>

      {loading && <p>Loading route risk data...</p>}

      {error && <p>Unable to load route risk data: {error}</p>}

      {!loading && !error && (
        <div className="route-risk-list">
          {routeRisks.map((route) => (
            <div className="route-risk-row" key={route.name}>
              <div className="route-name">{route.name}</div>

              <div className="risk-bar-background">
                <div
                  className={`risk-bar risk-${route.level.toLowerCase()}`}
                  style={{ width: `${route.score}%` }}
                />
              </div>

              <div className={`risk-score risk-${route.level.toLowerCase()}`}>
                {route.score.toFixed(1)} · {route.level}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="chart-axis">
        <div className="chart-axis-spacer" />

        <div className="chart-axis-scale">
          <span>0</span>
          <span>30</span>
          <span>65</span>
          <span>100</span>
        </div>

        <div className="chart-axis-spacer" />
      </div>

      <div className="chart-axis-label">
        Composite Risk Score (0–100)
      </div>
    </section>
  );
}

export default RouteRiskChart;