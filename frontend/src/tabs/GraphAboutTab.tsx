  import { useEffect, useState } from "react";
  import { getGraph } from "../api/endpoints";
  import type { GraphResponse } from "../types/api";
  import NetworkGraph from "../components/NetworkGraph";

  function GraphAboutTab() {
    const [graph, setGraph] = useState<GraphResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
      async function loadGraph() {
        try {
          const data = (await getGraph()) as GraphResponse;
          setGraph(data);
        } catch (err) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load graph data.",
          );
        } finally {
          setLoading(false);
        }
      }

      loadGraph();
    }, []);

    if (loading) {
      return (
        <section className="graph-about-tab">
          <h2>Graph &amp; About</h2>
          <p>Loading graph data...</p>
        </section>
      );
    }

    if (error) {
      return (
        <section className="graph-about-tab">
          <h2>Graph &amp; About</h2>
          <p>Unable to load graph data: {error}</p>
        </section>
      );
    }

    return (
      <section className="graph-about-tab">
        <h2>Graph &amp; About</h2>

        <p className="section-description">
          Supply-chain relationships between monitored suppliers, maritime
          routes, chokepoints, and refinery dependencies.
        </p>

        <div className="graph-summary">
          <article className="graph-stat">
            <span>Nodes</span>
            <strong>{graph?.nodes.length ?? 0}</strong>
          </article>

          <article className="graph-stat">
            <span>Edges</span>
            <strong>{graph?.edges.length ?? 0}</strong>
          </article>
        </div>

        <div className="graph-content">
          <article className="graph-panel network-graph-panel">
            <h3>Supply Chain Network</h3>

            {graph?.nodes.length ? (
              <NetworkGraph graph={graph} />
            ) : (
              <p>No graph data available.</p>
            )}
          </article>
        </div>

        <div className="about-section">
          <h3>About the Risk Radar</h3>

          <p>
            The system combines geopolitical news and market signals to
            identify, score, and propagate maritime supply-chain risks
            across monitored routes and Indian refinery dependencies.
          </p>

          <div className="pipeline-flow">
            <span>Signal</span>
            <span>→</span>
            <span>Risk Extraction</span>
            <span>→</span>
            <span>Risk Assessment</span>
            <span>→</span>
            <span>Route Risk</span>
            <span>→</span>
            <span>Refinery Exposure</span>
          </div>
        </div>
      </section>
    );
  }

  export default GraphAboutTab;