import { useEffect, useState } from "react";

import {
  getScenarios,
  replayScenario,
  runIngestion,
} from "../api/endpoints";
import type { Scenario } from "../types/risk";

interface SimulationControlsProps {
  onDataChanged: () => void;
}

function SimulationControls({
  onDataChanged,
}: SimulationControlsProps) {
  const [ingestionWindow, setIngestionWindow] = useState("24");
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState("");
  const [loadingScenarios, setLoadingScenarios] = useState(true);

  const [ingestionLoading, setIngestionLoading] = useState(false);
  const [replayLoading, setReplayLoading] = useState(false);

  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadScenarios() {
      try {
        const data = (await getScenarios()) as Scenario[];

        setScenarios(data);

        if (data.length > 0) {
          setSelectedScenario(data[0].id);
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load scenarios.",
        );
      } finally {
        setLoadingScenarios(false);
      }
    }

    loadScenarios();
  }, []);

  async function handleRunIngestion() {
    setIngestionLoading(true);
    setMessage(null);
    setError(null);

    try {
      const result = await runIngestion(Number(ingestionWindow));
      onDataChanged();

      setMessage(
        `Live ingestion complete — ${result.extracted ?? 0} signals extracted. Dashboard updated.`,
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to run live ingestion.",
      );
    } finally {
      setIngestionLoading(false);
    }
  }

  async function handleReplayScenario() {
    if (!selectedScenario) {
      return;
    }

    setReplayLoading(true);
    setMessage(null);
    setError(null);

    try {
      const result = await replayScenario(selectedScenario);
      onDataChanged();

      setMessage(
        `Replay complete: ${selectedScenarioData?.label ?? "Selected scenario"} — ${
          result.extracted ?? 0
        } signals extracted. Dashboard updated.`,
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to replay scenario.",
      );
    } finally {
      setReplayLoading(false);
    }
  }

  const selectedScenarioData = scenarios.find(
    (scenario) => scenario.id === selectedScenario,
  );

  return (
    <section className="simulation-controls">
      <h2>Simulation Controls</h2>

      <p className="section-description">
        Run live news ingestion or replay historical escalation scenarios.
      </p>

      <div className="control-group">
        <label htmlFor="ingestion-window">
          Live RSS Ingestion Window
        </label>

        <select
          id="ingestion-window"
          value={ingestionWindow}
          onChange={(event) => setIngestionWindow(event.target.value)}
          disabled={ingestionLoading}
        >
          <option value="24">24 hours</option>
          <option value="48">48 hours</option>
          <option value="72">72 hours</option>
        </select>

        <button
          type="button"
          onClick={handleRunIngestion}
          disabled={ingestionLoading}
        >
          {ingestionLoading ? (
            <>
              <span className="button-spinner" aria-hidden="true" />
              Running Ingestion...
            </>
          ) : (
            "Run Live Ingestion"
          )}
        </button>
      </div>

      <div className="control-divider" />

      <div className="control-group">
        <label htmlFor="scenario">Scenario</label>

        <select
          id="scenario"
          value={selectedScenario}
          onChange={(event) => setSelectedScenario(event.target.value)}
          disabled={loadingScenarios || replayLoading}
        >
          {loadingScenarios && (
            <option value="">Loading scenarios...</option>
          )}

          {!loadingScenarios && scenarios.length === 0 && (
            <option value="">No scenarios available</option>
          )}

          {scenarios.map((scenario) => (
            <option key={scenario.id} value={scenario.id}>
              {scenario.label}
            </option>
          ))}
        </select>

        {selectedScenarioData && (
          <p className="scenario-description">
            {selectedScenarioData.description}
          </p>
        )}

        <button
          type="button"
          onClick={handleReplayScenario}
          disabled={
            replayLoading ||
            loadingScenarios ||
            !selectedScenario
          }
        >
          {replayLoading
            ? "Replaying Scenario..."
            : "Replay Selected Scenario"}
        </button>
      </div>

      {message && <p className="simulation-message">{message}</p>}

      {error && <p>Unable to complete action: {error}</p>}
    </section>
  );
}

export default SimulationControls;