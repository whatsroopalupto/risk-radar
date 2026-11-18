
import { useEffect, useState } from "react";
import { apiClient } from "../api/client";

interface TradeRecord {
  metric: string;
  period: string;
  value: number;
  unit: string;
  supplier?: string;
  provisional?: boolean;
}

interface TradeSnapshot {
  source_url: string;
  source_title: string;
  source_page?: number;
  source_published?: string;
  published?: string;
  retrieved_at?: string;
  sha256?: string;
  scope: string;
  records: TradeRecord[];
}

interface TradeSource {
  provider: string;
  latest_status: string;
  retrieved_at: string | null;
  serving_previous_snapshot: boolean;
  snapshot: TradeSnapshot | null;
}

interface TradeData {
  limitation: string;
  sources: TradeSource[];
}

function formatMetric(metric: string) {
  return metric.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatUnit(unit: string) {
  return unit.replaceAll("_", " ");
}

function formatDate(value: string | null | undefined) {
  if (!value) return "Not available";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export default function TradeDataTab({
  refreshKey,
}: {
  refreshKey: number;
}) {
  const [data, setData] = useState<TradeData | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const load = () =>
    apiClient<TradeData>("/api/trade").then(setData);

  useEffect(() => {
    let active = true;

    apiClient<TradeData>("/api/trade")
      .then((value) => {
        if (active) {
          setData(value);
          setError(null);
        }
      })
      .catch(() => {
        if (active) setError("Trade data could not be loaded.");
      });

    return () => {
      active = false;
    };
  }, [refreshKey]);

  const handleRefresh = async () => {
    setBusy(true);
    setError(null);
    setSuccess(false);

    try {
      await apiClient("/api/trade/refresh", { method: "POST" });
      await load();
      setSuccess(true);
    } catch {
      setError("Refresh failed. Previously saved snapshots may still be available.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="trade-tab">
      <div className="trade-header">
        <div>
          <h2>Official Trade Context</h2>
          <p className="section-description">
            Official national-level crude oil import statistics from PPAC and EIA.
          </p>
        </div>

        <button
          className="trade-refresh-button"
          onClick={handleRefresh}
          disabled={busy}
        >
          {busy ? (
            <>
              <span className="button-spinner" />
              Fetching sources...
            </>
          ) : (
            "Refresh official sources"
          )}
        </button>
      </div>

      {error && <p className="trade-message trade-error" role="alert">{error}</p>}
      {success && <p className="trade-message trade-success">Sources refreshed successfully.</p>}

      {data && (
        <>
          <div className="trade-limitation">
            <strong>Data limitation</strong>
            <p>{data.limitation}</p>
          </div>

          <div className="trade-source-grid">
            {data.sources.map((source) => {
              const snapshot = source.snapshot;

              return (
                <article className="trade-source-card" key={source.provider}>
                  <div className="trade-source-header">
                    <div>
                      <span className="trade-source-label">OFFICIAL DATA SOURCE</span>
                      <h3>{source.provider.toUpperCase()}</h3>
                    </div>

                    <span
                      className={`trade-status ${
                        source.latest_status === "ok"
                          ? "trade-status-ok"
                          : "trade-status-warning"
                      }`}
                    >
                      {source.latest_status}
                    </span>
                  </div>

                  {source.serving_previous_snapshot && (
                    <p className="trade-message trade-warning">
                      Showing the last successful snapshot. The latest refresh was unsuccessful.
                    </p>
                  )}

                  {snapshot ? (
                    <>
                      <a
                        className="trade-source-link"
                        href={snapshot.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {snapshot.source_title} ↗
                      </a>

                      <p className="trade-scope">{snapshot.scope}</p>

                      <div className="trade-metadata">
                        <div>
                          <span>Publication date</span>
                          <strong>{snapshot.published || snapshot.source_published || "Not specified"}</strong>
                        </div>
                        <div>
                          <span>Retrieved (UTC)</span>
                          <strong>{formatDate(source.retrieved_at)}</strong>
                        </div>
                        {snapshot.source_page && (
                          <div>
                            <span>PDF page</span>
                            <strong>{snapshot.source_page}</strong>
                          </div>
                        )}
                      </div>

                      <div className="trade-table-heading">
                        <h4>Extracted observations</h4>
                        <span>{snapshot.records.length} records</span>
                      </div>

                      <div className="trade-table-scroll">
                        <table className="trade-table">
                          <thead>
                            <tr>
                              <th>Metric</th>
                              <th>Period</th>
                              <th>Value</th>
                              <th>Unit</th>
                              <th>Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {snapshot.records.map((record, index) => (
                              <tr key={`${record.metric}-${record.period}-${index}`}>
                                <td>
                                  {formatMetric(record.metric)}
                                  {record.supplier && ` · ${record.supplier}`}
                                </td>
                                <td>{record.period}</td>
                                <td className="trade-value">{record.value}</td>
                                <td>{formatUnit(record.unit)}</td>
                                <td>
                                  <span className={`trade-record-status ${
                                    record.provisional
                                      ? "trade-provisional"
                                      : "trade-published"
                                  }`}>
                                    {record.provisional ? "Provisional" : "Published"}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {snapshot.sha256 && (
                        <div className="trade-hash">
                          <span>SHA-256 source fingerprint</span>
                          <code>{snapshot.sha256}</code>
                        </div>
                      )}
                    </>
                  ) : (
                    <p className="trade-empty">No successful snapshot available yet.</p>
                  )}
                </article>
              );
            })}
          </div>
        </>
      )}

      {!data && !error && (
        <p className="trade-empty">Loading official trade data...</p>
      )}
    </section>
  );
}
