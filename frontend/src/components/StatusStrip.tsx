import { useEffect, useState } from "react";

import { getHealth } from "../api/endpoints";
import type { HealthResponse } from "../types/api";

interface StatusItem {
  label: string;
  value: string;
  tone?: "success" | "warning" | "muted" | "default";
}

interface StatusStripProps {
  refreshKey: number;
}

function StatusStrip({ refreshKey }: StatusStripProps) {
  const [statusItems, setStatusItems] = useState<StatusItem[]>([
    {
      label: "Classification engine",
      value: "Not yet available",
      tone: "muted",
    },
    {
      label: "RSS news",
      value: "Not yet run",
      tone: "muted",
    },
    {
      label: "GDELT",
      value: "Not yet run",
      tone: "muted",
    },
    {
      label: "AIS vessel tracking",
      value: "Planned for future release",
      tone: "muted",
    },
    {
      label: "Last updated",
      value: "Not yet run",
      tone: "default",
    },
  ]);

  useEffect(() => {
    async function loadHealth() {
      try {
        const health = (await getHealth()) as HealthResponse;

        const engine = health.extractor.active;

        const rssStatus = health.sources?.rss as
          | { status?: string; fetched?: number }
          | undefined;

        const gdeltStatus = health.sources?.gdelt as
          | { status?: string; fetched?: number }
          | undefined;

        const aisStatus = health.sources?.ais as
          | { status?: string; fetched?: number }
          | undefined;

        setStatusItems([
          {
            label: "Classification engine",
            value:
              engine === "heuristic-v1"
                ? "Rule-based · heuristic-v1"
                : engine,
            tone: engine === "heuristic-v1" ? "warning" : "success",
          },
          {
            label: "RSS news",
            value:
              rssStatus?.status === "ok"
                ? `Active · ${rssStatus.fetched ?? 0} fetched`
                : "Not yet run",
            tone:
              rssStatus?.status === "ok"
                ? "success"
                : "muted",
          },
          {
            label: "GDELT",
            value:
              gdeltStatus?.status === "ok"
                ? gdeltStatus.fetched
                  ? `${gdeltStatus.fetched} results`
                  : "No new results"
                : "Not yet run",
            tone:
              gdeltStatus?.fetched
                ? "success"
                : "muted",
          },
          {
            label: "AIS vessel tracking",
            value:
              aisStatus?.status === "not_implemented_phase_2"
                ? "Planned for future release"
                : aisStatus?.status ?? "Unknown",
            tone: "muted",
          },
          {
            label: "Last updated",
            value: health.last_run_time
              ? new Date(health.last_run_time).toLocaleString("en-IN", {
                dateStyle: "short",
                timeStyle: "short",
              })
              : "Not yet run",
            tone: "default",
          },
        ]);
      } catch {
        // Keep the last successful status visible while refreshing.
      }
    }

    loadHealth();
  }, [refreshKey]);

  return (
    <section className="status-strip">
      {statusItems.map((item) => (
        <div className="status-card" key={item.label}>
          <div className="status-label">{item.label}</div>

          <div
            className={`status-value status-${item.tone ?? "default"}`}
          >
            {item.value}
          </div>
        </div>
      ))}
    </section>
  );
}

export default StatusStrip;