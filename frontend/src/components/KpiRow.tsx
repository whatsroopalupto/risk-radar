import { useEffect, useState } from "react";

import KpiCard from "./KpiCard";
import {
  getHealth,
  getRefineryExposures,
  getRouteRisks,
} from "../api/endpoints";

import type {
  RefineryExposure,
  RouteRisk,
} from "../types/risk";
import type {
  HealthResponse,
} from "../types/api";

interface KpiRowProps {
  refreshKey: number;
}

function KpiRow({ refreshKey }: KpiRowProps) {
  const [highestRoute, setHighestRoute] = useState<RouteRisk | null>(null);
  const [peakRefinery, setPeakRefinery] =
    useState<RefineryExposure | null>(null);
  const [routeCount, setRouteCount] = useState(0);
  const [storedSignals, setStoredSignals] = useState(0);
  const [latestExtracted, setLatestExtracted] = useState(0);
  const [aiShare, setAiShare] = useState(0);
  const [highRouteCount, setHighRouteCount] = useState(0);
  const [aiCount, setAiCount] = useState(0);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function loadKpis() {
      try {
        const [routes, refineries, health] =
          await Promise.all([
            getRouteRisks(),
            getRefineryExposures(),
            getHealth(),
          ]);

        const routeData = routes as RouteRisk[];
        const refineryData = refineries as RefineryExposure[];
        const healthData = health as HealthResponse;
        setError(false);

        const highest = routeData.reduce<RouteRisk | null>(
          (current, route) =>
            !current ||
            route.composite_score > current.composite_score
              ? route
              : current,
          null,
        );

        const peak = refineryData.reduce<RefineryExposure | null>(
          (current, refinery) =>
            !current ||
            refinery.exposure_score > current.exposure_score
              ? refinery
              : current,
          null,
        );

        setHighestRoute(highest);
        setPeakRefinery(peak);
        setRouteCount(routeData.length);
        setHighRouteCount(routeData.filter((route) => route.band === "high").length);

        setStoredSignals(
          healthData.db_counts?.assessments ?? 0,
        );

        setLatestExtracted(
          healthData.db_counts?.assessments ?? 0,
        );

        const extractorMix = healthData.extractor_mix ?? {};

        const totalClassified = Object.values(extractorMix).reduce<number>(
            (sum, value) =>
                sum + (typeof value === "number" ? value : 0),
            0,
        );

        const geminiCount = Object.entries(extractorMix).reduce(
          (sum, [name, count]) => sum + (name.startsWith("gemini") && typeof count === "number" ? count : 0), 0);
        setAiCount(geminiCount);

        setAiShare(
          totalClassified > 0
            ? (geminiCount / totalClassified) * 100
            : 0,
        );
      } catch (error) {
        setError(true);
        console.error("Failed to load KPI data:", error);
      }
    }

    loadKpis();
  }, [refreshKey]);

  return (
    <section className="kpi-row">
      {error && <p role="status">Unable to refresh risk indicators. Values may be stale.</p>}
      <KpiCard
        label="Highest route risk"
        value={
          highestRoute
            ? `${highestRoute.composite_score.toFixed(1)} / 100`
            : ""
        }
        description={
          highestRoute?.name ?? "No route data"
        }
        tone={
          highestRoute?.band === "high"
            ? "high"
            : highestRoute?.band === "medium"
              ? "medium"
              : undefined
        }
      />

      <KpiCard
        label="Peak refinery exposure"
        value={
          peakRefinery
            ? `${peakRefinery.exposure_score.toFixed(1)} / 100`
            : ""
        }
        description={
          peakRefinery?.name ?? "No refinery data"
        }
        tone={
          peakRefinery?.band === "high"
            ? "high"
            : peakRefinery?.band === "medium"
              ? "medium"
              : undefined
        }
      />

      <KpiCard
        label="Displayed risk signals"
        value={String(latestExtracted)}
        description={`Current dataset: ${storedSignals} stored assessments`}
      />

      <KpiCard
        label="High-risk routes"
        value={String(highRouteCount)}
        description={`${routeCount} supply routes monitored`}
        tone="high"
      />

      <KpiCard
        label="AI-classified share"
        value={`${aiShare.toFixed(0)}%`}
        description={`AI-classified signals: ${aiCount} / ${latestExtracted}`}
      />
    </section>
  );
}

export default KpiRow;
