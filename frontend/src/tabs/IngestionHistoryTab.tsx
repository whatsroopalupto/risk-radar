import { useEffect, useState } from "react";

import { getIngestionHistory } from "../api/endpoints";
import type { IngestRunStats } from "../types/api";

function IngestionHistoryTab() {
  const [runs, setRuns] = useState<IngestRunStats[]>([]);
  const [historyLimit, setHistoryLimit] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadHistory() {
      try {
        const data =
          (await getIngestionHistory(historyLimit)) as IngestRunStats[];

        setRuns(data);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load ingestion history.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadHistory();
  }, [historyLimit]);

  if (loading) {
    return (
      <section className="history-tab">
        <h2>Ingestion History</h2>
        <p>Loading ingestion history...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="history-tab">
        <h2>Ingestion History</h2>
        <p>Unable to load ingestion history: {error}</p>
      </section>
    );
  }

  return (
    <section className="history-tab">
      <h2>Ingestion History</h2>

      <p className="section-description">
        Historical ingestion runs and their processing results.
      </p>

      {runs.length === 0 ? (
        <p>No ingestion runs recorded yet.</p>
      ) : (
        <>
          <div className="history-list">
            {runs.map((run) => {
              const fetched = Object.values(run.per_source).reduce(
                (total, source) => total + source.fetched,
                0,
              );

              const afterDedupe = fetched - run.deduped;

              return (
                <article
                  className="history-card"
                  key={run.run_id}
                >
                  <div className="history-card-header">
                    <div>
                      <h3>
                        {run.scenario_id
                          ? `Scenario: ${run.scenario_id}`
                          : "Live ingestion"}
                      </h3>

                      <p>
                        {new Date(
                          run.started_at,
                        ).toLocaleString("en-IN")}
                      </p>
                    </div>

                    <span
                      className={`history-status history-${run.errors.length === 0 ? "success" : "warning"}`}
                    >
                      {run.errors.length === 0
                        ? "Completed"
                        : "Completed with errors"}
                    </span>
                  </div>

                  <div className="history-stats">
                    <div>
                      <span>Fetched</span>
                      <strong>{fetched}</strong>
                    </div>

                    <div>
                      <span>After dedupe</span>
                      <strong>{afterDedupe}</strong>
                    </div>

                    <div>
                      <span>Filtered out</span>
                      <strong>{run.filtered_out}</strong>
                    </div>

                    <div>
                      <span>Extracted</span>
                      <strong>{run.extracted}</strong>
                    </div>

                    <div>
                      <span>Deduped</span>
                      <strong>{run.deduped}</strong>
                    </div>
                  </div>

                  <div className="history-sources">
                    {Object.entries(run.per_source).map(
                      ([sourceName, source]) => (
                        <div
                          className="history-source"
                          key={sourceName}
                        >
                          <span>{sourceName}</span>
                          <span>
                            {source.status} · {source.fetched} fetched
                          </span>
                        </div>
                      ),
                    )}
                  </div>

                  <div className="history-footer">
                    <span>
                      Extractor:{" "}
                      <strong>{run.extractor_used}</strong>
                    </span>

                    <span>
                      Run ID:{" "}
                      <code>{run.run_id}</code>
                    </span>
                  </div>
                </article>
              );
            })}
          </div>
          {runs.length >= historyLimit && (
            <button
              className="history-load-more"
              onClick={() => setHistoryLimit((limit) => limit + 20)}
            >
              Load more
            </button>
          )}
        </>
      )}
    </section>
  );
}

export default IngestionHistoryTab;