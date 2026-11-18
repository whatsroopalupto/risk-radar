import { useEffect, useState } from "react";
import { apiClient } from "../api/client";

interface Vessel {
  mmsi: string; name: string; latitude: number; longitude: number;
  speed_knots: number | null; observed_at: string;
  vessel_class?: string;
}
interface Activity {
  score_fusion_enabled: boolean;
  health: { status: string; stale: boolean; detail: string };
  scope: string; limitation: string; computed_at: string;
  corridors: {
    id: string; unique_vessels_24h: number; observations_24h: number;
    baseline_status: string; baseline_target_days: number; latest_observation: string | null;
    vessels: Vessel[]; features?: { baseline_hours: number; required_hours: number; coverage_fraction: number; status: string; anomaly: { fraction: number } | null }
  }[];
}
const date = (value: string | null) => value ? new Date(value.endsWith("Z") || /[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`).toLocaleString("en-IN") : "No observations";

export default function VesselActivityTab({ refreshKey }: { refreshKey: number }) {
  const [data, setData] = useState<Activity | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    apiClient<Activity>("/api/ais/activity").then((result) => {
      if (active) { setData(result); setError(null); }
    }).catch(() => { if (active) setError("AIS activity is unavailable. Previously displayed data may be stale."); });
    return () => { active = false; };
  }, [refreshKey]);
  return <section className="vessel-activity-tab">
    <div className="ais-heading">
      <h2>AIS Vessel Activity</h2>
      <p className="section-description">
        Monitor vessel activity, position reports, and AIS coverage across key maritime corridors.
      </p>
      <p className="ais-live-meta">
        Live AIS observations are independent of the news replay selected elsewhere.
        {data && <> &nbsp; Updated {date(data.computed_at)}</>}
      </p>
    </div>
    {error && <p role="alert">{error}</p>}
    {!data && !error && <p>Loading vessel observations...</p>}
    {data && <>
      <div className="ais-status-strip">
        <div className="ais-status-card">
          <span className="ais-status-label">AIS Collector</span>
          <strong className={data.health.status === "connected" ? "ais-status-connected" : ""}>
            {data.health.status.replaceAll("_", " ")}
          </strong>
        </div>
        <div className="ais-status-card">
          <span className="ais-status-label">Position Data</span>
          <strong>{data.health.stale ? "Stale or unavailable" : "Recent"}</strong>
        </div>
        <div className="ais-status-card">
          <span className="ais-status-label">Score Fusion</span>
          <strong>{data.score_fusion_enabled ? "Experimental" : "Disabled"}</strong>
        </div>
      </div>
      <p className="ais-position-notice">{data.health.detail}</p>
      <div className="ais-fusion-note">
        <strong>AIS Contribution to Route Scores</strong>
        <span>
          {data.score_fusion_enabled
            ? "Experimental fusion enabled; coverage gates still apply."
            : "Disabled pending baseline validation; observations remain available."}
        </span>
      </div>
      <div className="ais-info-panel">
        <div>
          <span>DATA SCOPE</span>
          <p>{data.scope}</p>
        </div>
        <div>
          <span>IMPORTANT LIMITATION</span>
          <p>{data.limitation}</p>
        </div>
      </div>
      {data.corridors.map((corridor) => <article className="graph-panel vessel-corridor-card" key={corridor.id}>
        <h3>{corridor.id === "hormuz" ? "Hormuz region and UAE approaches (research box)" : "Southern Red Sea / Bab-el-Mandeb"}</h3>
        <div className="ais-corridor-metrics">
          <div className="ais-metric">
            <span>Observed Vessels</span>
            <strong>{corridor.unique_vessels_24h}</strong>
            <small>Last 24 hours</small>
          </div>
          <div className="ais-metric">
            <span>Position Reports</span>
            <strong>{corridor.observations_24h}</strong>
            <small>Last 24 hours</small>
          </div>
          <div className="ais-metric">
            <span>Baseline Hours</span>
            <strong>{corridor.features?.baseline_hours ?? 0}</strong>
            <small>Qualified hours</small>
          </div>
          <div className="ais-metric">
            <span>Heartbeat Coverage</span>
            <strong>{corridor.features ? `${(corridor.features.coverage_fraction * 100).toFixed(0)}%` : "N/A"}</strong>
            <small>Complete-hour coverage</small>
          </div>
        </div>
        <div className="ais-corridor-meta">
          <p>
            <span>Latest Observation</span>
            <strong>{date(corridor.latest_observation)}</strong>
          </p>
          <p>
            <span>Baseline Status</span>
            <strong>{corridor.baseline_status.replaceAll("_", " ")}</strong>
          </p>
          <p>
            <span>Baseline Target</span>
            <strong>{corridor.baseline_target_days} days + coverage validation</strong>
          </p>
        </div>
        {corridor.features && (
          <div className="ais-baseline-info">
            <span>BASELINE VALIDATION</span>
            <p>
              {corridor.features.baseline_hours} / {corridor.features.required_hours} qualified baseline hours
            </p>
            <p>
              {corridor.features.anomaly
                ? `Observed activity drop ${(corridor.features.anomaly.fraction * 100).toFixed(0)}%`
                : "No qualified anomaly available"}
            </p>
          </div>
        )}
        {corridor.vessels.length === 0 ? <p>No observed vessels. This does not establish that the corridor is empty or disrupted.</p> :
          <div className="vessel-table-scroll ais-table-scroll"><table><caption>Latest received position per vessel (up to 100 shown)</caption>
            <thead><tr><th scope="col">Vessel / MMSI</th><th scope="col">Latitude</th><th scope="col">Longitude</th><th scope="col">Speed (knots)</th><th scope="col">Observed</th></tr></thead>
            <tbody>{corridor.vessels.map((vessel) => <tr key={vessel.mmsi}>
              <td>{vessel.name || "Unnamed vessel"} / {vessel.mmsi} · {vessel.vessel_class ?? "unknown"}</td><td>{vessel.latitude.toFixed(4)}</td><td>{vessel.longitude.toFixed(4)}</td>
              <td>{vessel.speed_knots ?? "Unavailable"}</td><td>{date(vessel.observed_at)}</td>
            </tr>)}</tbody></table></div>}
      </article>)}
    </>}
  </section>;
}
