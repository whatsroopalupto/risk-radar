import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
interface TradeData {
  limitation: string;
  sources: { provider: string; latest_status: string; retrieved_at: string | null; serving_previous_snapshot: boolean;
    snapshot: { source_url: string; source_title: string; source_page?: number; scope: string;
      records: { metric: string; period: string; value: number; unit: string; supplier?: string; provisional?: boolean }[] } | null }[];
}
export default function TradeDataTab({ refreshKey }: { refreshKey: number }) {
  const [data, setData] = useState<TradeData | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const load = () => apiClient<TradeData>("/api/trade").then(setData);
  useEffect(() => { let active = true; apiClient<TradeData>("/api/trade").then((value) => { if (active) setData(value); }).catch(() => { if (active) setError("Trade data could not be loaded."); }); return () => { active = false; }; }, [refreshKey]);
  return <section><h2>Official Trade Context</h2>
    <p>PPAC and EIA observations retain their source, units and reporting periods. A recent retrieval does not make historical statistics current.</p>
    <button disabled={busy} onClick={async () => { setBusy(true); setError(null); try { await apiClient("/api/trade/refresh", { method: "POST" }); await load(); } catch { setError("Refresh failed; retained snapshots may still be available."); } finally { setBusy(false); } }}>{busy ? "Fetching official reports..." : "Refresh official sources"}</button>
    {error && <p role="alert">{error}</p>}
    {data && <><p>{data.limitation}</p>{data.sources.map((source) => <article key={source.provider} className="graph-panel">
      <h3>{source.provider.toUpperCase()}</h3><p>Latest fetch: {source.latest_status} {source.serving_previous_snapshot ? "· showing an older successful snapshot" : ""}</p>
      {source.snapshot ? <><a href={source.snapshot.source_url} target="_blank" rel="noopener noreferrer">{source.snapshot.source_title}</a>
        <p>{source.snapshot.scope} {source.snapshot.source_page ? `· PDF page ${source.snapshot.source_page}` : ""}</p><p>Retrieved: {source.retrieved_at} UTC</p>
        <div className="vessel-table-scroll"><table><caption>National statistics, with original units</caption><thead><tr><th>Metric</th><th>Period</th><th>Value</th><th>Unit</th><th>Status</th></tr></thead>
          <tbody>{source.snapshot.records.map((record, index) => <tr key={index}><td>{record.metric.replaceAll("_", " ")}{record.supplier ? ` · ${record.supplier}` : ""}</td><td>{record.period}</td><td>{record.value}</td><td>{record.unit.replaceAll("_", " ")}</td><td>{record.provisional ? "Provisional" : "Published"}</td></tr>)}</tbody></table></div></> : <p>No successful snapshot yet.</p>}
    </article>)}</>}
  </section>;
}
