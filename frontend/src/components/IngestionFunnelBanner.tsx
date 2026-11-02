import { useEffect, useState } from "react";

import { getIngestionHistory } from "../api/endpoints";
import type { IngestRunStats } from "../types/api";

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

  useEffect(() => {
    async function loadLatestRun() {
      try {
        const history =
          (await getIngestionHistory(1)) as IngestRunStats[];

        setLatestRun(history[0] ?? null);
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
          ? `REPLAY: ${formatScenarioName(latestRun.scenario_id)}`
          : "LIVE DATA"}
      </span>

      <span className="funnel-label">Latest run funnel</span>

      <span className="funnel-stats">
        {loading ? (
          "Loading..."
        ) : latestRun ? (
          <>
            <strong>
              {Object.values(latestRun.per_source).reduce(
                (total, source) => total + source.fetched,
                0,
              )}
            </strong>{" "}
            fetched →{" "}
            <strong>
              {Object.values(latestRun.per_source).reduce(
                (total, source) => total + source.fetched,
                0,
              ) - latestRun.deduped}
            </strong>{" "}
            after dedupe →{" "}
            <strong>{latestRun.extracted}</strong>{" "}
            extracted &amp; scored
          </>
        ) : (
          "No ingestion runs yet"
        )}
      </span>
    </section>
  );
}

export default IngestionFunnelBanner;