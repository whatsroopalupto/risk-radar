import { useEffect, useState } from "react";

import { getRouteRiskTimeseries } from "../../api/endpoints";
import type { RouteRiskTimeseriesPoint } from "../../types/risk";

interface TrendPoint {
  x: number;
  y: number;
  date: string;
  score: number;
  band: RouteRiskTimeseriesPoint["points"][number]["band"];
  signalCount: number;
}

interface TrendSeries {
  name: string;
  className: string;
  points: TrendPoint[];
}

interface RiskTrendChartProps {
  refreshKey: number;
}

function RiskTrendChart({ refreshKey }: RiskTrendChartProps) {
  const [series, setSeries] = useState<TrendSeries[]>([]);
  const [dateRange, setDateRange] = useState({
    start: "",
    end: "",
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadTrendData() {
      try {
        const data =
          (await getRouteRiskTimeseries()) as RouteRiskTimeseriesPoint[];

        if (!data.length) {
          setSeries([]);
          return;
        }

        const width = 500;
        const height = 100;

        const allDates = data[0].points.map((point) => point.date);

        if (allDates.length > 0) {
          const firstDate = new Date(allDates[0]);
          const lastDate = new Date(allDates[allDates.length - 1]);

          setDateRange({
            start: firstDate.toLocaleDateString("en-GB", {
              day: "2-digit",
              month: "short",
            }),
            end: lastDate.toLocaleDateString("en-GB", {
              day: "2-digit",
              month: "short",
            }),
          });
        }

        const routeStyles = [
          {
            routeId: "hormuz_west_coast",
            className: "trend-hormuz",
          },
          {
            routeId: "red_sea_suez",
            className: "trend-red-sea",
          },
          {
            routeId: "cape_of_good_hope",
            className: "trend-cape",
          },
          {
            routeId: "west_africa_atlantic",
            className: "trend-west-africa",
          },
        ];

        const mappedSeries = routeStyles
          .map((route) => {
            const routeData = data.find(
              (item) => item.route_id === route.routeId,
            );

            if (!routeData) {
              return null;
            }

            const points = routeData.points.map((point, index) => {
              const x =
                routeData.points.length === 1
                  ? 0
                  : (index / (routeData.points.length - 1)) * width;

              const score = Math.min(
                100,
                Math.max(0, point.news_score),
              );

              const y = height - (score / 100) * height;

              return {
                x,
                y: y + 10,
                date: point.date,
                score,
                band: point.band,
                signalCount: point.signal_count,
              };
            });

            return {
              name: routeData.name,
              className: route.className,
              points,
            };
          })
          .filter((item): item is TrendSeries => item !== null);

        setSeries(mappedSeries);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load risk trend data.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadTrendData();
  }, [refreshKey]);

  return (
    <section className="risk-trend-section">
      <h2>Risk Trend Over Time</h2>

      <p className="section-description">
        Cumulative-to-date noisy-OR of news signals per route, day by day.
      </p>

      {loading && <p>Loading risk trend data...</p>}

      {error && <p>Unable to load risk trend data: {error}</p>}

      {!loading && !error && series.length > 0 && (
        <>
          <div className="trend-chart">
            <svg
              viewBox="0 0 520 130"
              role="img"
              aria-label="Risk trend over time"
            >
              <line
                x1="0"
                y1="10"
                x2="0"
                y2="110"
                className="chart-axis"
              />

              <line
                x1="0"
                y1="110"
                x2="500"
                y2="110"
                className="chart-axis"
              />

              <text x="-6" y="14" className="chart-label" textAnchor="end">
                100
              </text>

              <text x="-6" y="112" className="chart-label" textAnchor="end">
                0
              </text>

              {series.map((route) => (
                <g key={route.name}>
                  <polyline
                    points={route.points
                      .map((point) => `${point.x},${point.y}`)
                      .join(" ")}
                    className={`trend-line ${route.className}`}
                  />

                  {route.points.map((point) => (
                    <circle
                      key={`${route.name}-${point.date}`}
                      cx={point.x}
                      cy={point.y}
                      r="3"
                      className={`trend-point ${route.className}`}
                    >
                      <title>
                        {`${route.name} — ${point.date} · Risk Score: ${point.score.toFixed(
                          1,
                        )} · ${point.band} · ${point.signalCount} signal${point.signalCount === 1 ? "" : "s"
                          }`}
                      </title>
                    </circle>
                  ))}
                </g>
              ))}

              <text x="0" y="124" className="chart-label">
                {dateRange.start}
              </text>

              <text x="460" y="124" className="chart-label">
                {dateRange.end}
              </text>
            </svg>
          </div>

          <div className="trend-legend">
            <span>
              <span className="legend-dot legend-hormuz" />
              Persian Gulf via Hormuz
            </span>

            <span>
              <span className="legend-square legend-red-sea" />
              Red Sea / Suez
            </span>

            <span>
              <span className="legend-square legend-cape" />
              Cape of Good Hope
            </span>

            <span>
              <span className="legend-square legend-west-africa" />
              West Africa / Atlantic
            </span>
          </div>
        </>
      )}
    </section>
  );
}

export default RiskTrendChart;