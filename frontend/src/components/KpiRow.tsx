import { useEffect, useState } from "react";

import KpiCard from "./KpiCard";
import {
  getHealth,
  getIngestionHistory,
  getRefineryExposures,
  getRouteRisks,
} from "../api/endpoints";

import type {
  RefineryExposure,
  RouteRisk,
} from "../types/risk";
import type {
  HealthResponse,
  IngestRunStats,
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

  useEffect(() => {
    async function loadKpis() {
      try {
        const [routes, refineries, health, history] =
          await Promise.all([
            getRouteRisks(),
            getRefineryExposures(),
            getHealth(),
            getIngestionHistory(1),
          ]);

        const routeData = routes as RouteRisk[];
        const refineryData = refineries as RefineryExposure[];
        const healthData = health as HealthResponse;
        const historyData = history as IngestRunStats[];

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

        setStoredSignals(
          healthData.db_counts?.assessments ?? 0,
        );

        setLatestExtracted(
          historyData[0]?.extracted ?? 0,
        );

        const extractorMix = healthData.extractor_mix ?? {};

        const totalClassified = Object.values(extractorMix).reduce<number>(
            (sum, value) =>
                sum + (typeof value === "number" ? value : 0),
            0,
        );

        const geminiCount =
          typeof extractorMix["gemini"] === "number"
            ? extractorMix["gemini"]
            : typeof extractorMix["gemini-v1"] === "number"
              ? extractorMix["gemini-v1"]
              : 0;

        setAiShare(
          totalClassified > 0
            ? (geminiCount / totalClassified) * 100
            : 0,
        );
      } catch (error) {
        console.error("Failed to load KPI data:", error);
      }
    }

    loadKpis();
  }, [refreshKey]);

  return (
    <section className="kpi-row">
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
        label="Ingested risk signals"
        value={String(latestExtracted)}
        description={`Stored in database: ${storedSignals}`}
      />

      <KpiCard
        label="High-risk routes"
        value={String(
          routeDataCount(routeCount, highestRoute),
        )}
        description={`${routeCount} supply routes monitored`}
        tone="high"
      />

      <KpiCard
        label="AI-classified share"
        value={`${aiShare.toFixed(0)}%`}
        description={`AI-classified signals: ${Math.round(
          (aiShare / 100) * latestExtracted,
        )} / ${latestExtracted}`}
      />
    </section>
  );
}

function routeDataCount(
  _routeCount: number,
  highestRoute: RouteRisk | null,
) {
  return highestRoute?.band === "high" ? 1 : 0;
}

export default KpiRow;