import { useEffect, useState } from "react";

import { getHealth } from "../api/endpoints";
import type { IngestRunStats, HealthResponse } from "../types/api";

function formatScenarioName(scenarioId: string) {
  return scenarioId
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

interface IngestionFunnelBannerProps {
  refreshKey: number;
}

function IngestionFunnelBanner({
  refreshKey,
}: IngestionFunnelBannerProps) {
  const [latestRun, setLatestRun] = useState<IngestRunStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [unverified, setUnverified] = useState(false);

  useEffect(() => {
    async function loadLatestRun() {
      try {
        const health = (await getHealth()) as HealthResponse;
        setLatestRun(health.latest_run ?? null);
        setUnverified(health.provenance === "legacy_snapshot_unverified");
      } catch (error) {
        console.error(
          "Failed to load latest ingestion run:",
          error,
        );
      } finally {
        setLoading(false);
      }
    }

    loadLatestRun();
  }, [refreshKey]);

  return (
    <section className="ingestion-banner">
      <span className="live-badge">
        {latestRun?.scenario_id
          ? `ILLUSTRATIVE REPLAY: ${formatScenarioName(latestRun.scenario_id)}`
          : unverified ? "UNVERIFIED SAVED DATA" : "LIVE RUN"}
      </span>

      <span className="funnel-label">Latest run funnel</span>

      <span className="funnel-stats">
        {loading ? (
          "Loading..."
        ) : latestRun ? (
          <>
            {latestRun.data_quality && latestRun.data_quality !== "ok" && <strong>News sources unavailable; previous risk retained. </strong>}
            <strong>
              {Object.entries(latestRun.per_source).reduce(
                (total, [name, source]) => total + (name === "prices" ? 0 : source.fetched),
                0,
              )}
            </strong>{" "}
            fetched →{" "}
            <strong>
              {Object.entries(latestRun.per_source).reduce(
                (total, [name, source]) => total + (name === "prices" ? 0 : source.fetched),
                0,
              ) - latestRun.deduped}
            </strong>{" "}
            after dedupe →{" "}
            <strong>{latestRun.extracted}</strong>{" "}
            extracted &amp; scored
            {latestRun.deferred ? ` · ${latestRun.deferred} retained for retrieval, unscored due to batch limit` : ""}
          </>
        ) : (
          "Saved assessments have no matching run metadata; freshness is unverified."
        )}
      </span>
    </section>
  );
}

export default IngestionFunnelBanner;
