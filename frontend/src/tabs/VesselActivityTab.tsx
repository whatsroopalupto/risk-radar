import { useEffect, useState } from "react";
import { apiClient } from "../api/client";

interface Vessel {
  mmsi: string; name: string; latitude: number; longitude: number;
  speed_knots: number | null; observed_at: string;
  vessel_class?: string;
}
interface Activity {
  health: { status: string; stale: boolean; detail: string };
  scope: string; limitation: string; computed_at: string;
  corridors: { id: string; unique_vessels_24h: number; observations_24h: number;
    baseline_status: string; baseline_target_days: number; latest_observation: string | null;
    vessels: Vessel[]; features?: { baseline_hours: number; required_hours: number; coverage_fraction: number; status: string; anomaly: { fraction: number } | null } }[];
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
    <h2>AIS Vessel Activity</h2>
    {error && <p role="alert">{error}</p>}
    {!data && !error && <p>Loading vessel observations...</p>}
    {data && <>
      <p>Collector: <strong>{data.health.status.replaceAll("_", " ")}</strong> · Position data: <strong>{data.health.stale ? "stale or unavailable" : "recent"}</strong></p>
      <p>{data.health.detail}</p>
      <p>{data.scope}</p>
      <p>{data.limitation}</p>
      <p>Live AIS observations are independent of the news replay selected elsewhere. Updated {date(data.computed_at)}.</p>
      {data.corridors.map((corridor) => <article className="graph-panel" key={corridor.id}>
        <h3>{corridor.id === "hormuz" ? "Hormuz region and UAE approaches (research box)" : "Southern Red Sea / Bab-el-Mandeb"}</h3>
        <p>{corridor.unique_vessels_24h} observed vessels · {corridor.observations_24h} positions in the last 24 hours</p>
        <p>Latest observation: {date(corridor.latest_observation)}</p>
        <p>Baseline: {corridor.baseline_status.replaceAll("_", " ")} · target {corridor.baseline_target_days} days plus coverage validation</p>
        {corridor.features && <p>{corridor.features.baseline_hours} / {corridor.features.required_hours} qualified baseline hours · latest complete-hour heartbeat coverage {(corridor.features.coverage_fraction * 100).toFixed(0)}% · {corridor.features.anomaly ? `Observed activity drop ${(corridor.features.anomaly.fraction * 100).toFixed(0)}%` : "No qualified anomaly available"}</p>}
        {corridor.vessels.length === 0 ? <p>No observed vessels. This does not establish that the corridor is empty or disrupted.</p> :
          <div className="vessel-table-scroll"><table><caption>Latest received position per vessel (up to 100 shown)</caption>
            <thead><tr><th scope="col">Vessel / MMSI</th><th scope="col">Latitude</th><th scope="col">Longitude</th><th scope="col">Speed (knots)</th><th scope="col">Observed</th></tr></thead>
            <tbody>{corridor.vessels.map((vessel) => <tr key={vessel.mmsi}>
              <td>{vessel.name || "Unnamed vessel"} / {vessel.mmsi} · {vessel.vessel_class ?? "unknown"}</td><td>{vessel.latitude.toFixed(4)}</td><td>{vessel.longitude.toFixed(4)}</td>
              <td>{vessel.speed_knots ?? "Unavailable"}</td><td>{date(vessel.observed_at)}</td>
            </tr>)}</tbody></table></div>}
      </article>)}
    </>}
  </section>;
}
