import { useEffect, useState } from "react";
import { getRouteRisks } from "../api/endpoints";
import type { RouteRisk as ApiRouteRisk } from "../types/risk";

interface RouteDetail {
  name: string;
  risk: number;
  level: "High" | "Medium" | "Low";
  chokepoints: string;
  signals: number;
}

interface RouteDetailCardsProps {
  refreshKey: number;
}

function RouteDetailCards({ refreshKey }: RouteDetailCardsProps) {
  const [routes, setRoutes] = useState<RouteDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadRoutes() {
      try {
        const data = (await getRouteRisks()) as ApiRouteRisk[];

        const mappedRoutes: RouteDetail[] = data.map((route) => ({
          name: route.name,
          risk: route.composite_score,
          level:
            route.band === "high"
              ? "High"
              : route.band === "medium"
                ? "Medium"
                : "Low",
          chokepoints:
            route.chokepoints.length > 0
              ? route.chokepoints.join(", ")
              : "none",
          signals: route.contributing_signal_ids.length,
        }));

        setRoutes(mappedRoutes);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load route details.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadRoutes();
  }, [refreshKey]);

  return (
    <section className="route-details">
      <h2>Route Details &amp; Contributing Signal Count</h2>

      {loading && <p>Loading route details...</p>}

      {error && <p>Unable to load route details: {error}</p>}

      {!loading && !error && (
        <div className="route-detail-grid">
          {routes.map((route) => (
            <article className="route-detail-card" key={route.name}>
              <h3>{route.name}</h3>

              <div
                className={`route-detail-risk risk-${route.level.toLowerCase()}`}
              >
                Risk {route.risk.toFixed(1)} / 100 — {route.level} ▲
              </div>

              <div className="route-detail-meta">
                Chokepoints: {route.chokepoints}
              </div>

              <div className="route-detail-meta">
                Contributing signals: {route.signals}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default RouteDetailCards;