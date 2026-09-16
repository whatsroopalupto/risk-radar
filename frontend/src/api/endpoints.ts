import { apiClient } from "./client";
import type { IngestRunStats } from "../types/api";

export const getHealth = () =>
  apiClient("/api/health");

export const getRouteRisks = () =>
  apiClient("/api/risk/routes");

export const getRouteRiskTimeseries = () =>
  apiClient("/api/risk/routes/timeseries");

export const getRefineryExposures = () =>
  apiClient("/api/risk/refineries");

export const getGraph = () =>
  apiClient("/api/graph");

export const getScenarios = () =>
  apiClient("/api/scenarios");

export const getSignals = (limit = 100, band?: string) => {
  const params = new URLSearchParams();

  params.set("limit", String(limit));

  if (band) {
    params.set("band", band);
  }

  return apiClient(`/api/signals?${params.toString()}`);
};

export const getIngestionHistory = (limit = 20) =>
  apiClient(`/api/ingest/history?limit=${limit}`);

export const runIngestion = (windowHours = 24) =>
  apiClient<IngestRunStats>(
    `/api/ingest/run?window_hours=${windowHours}`,
    {
      method: "POST",
    },
  );

export const replayScenario = (scenarioId: string) =>
  apiClient<IngestRunStats>(
    `/api/replay/${encodeURIComponent(scenarioId)}`,
    {
      method: "POST",
    },
  );