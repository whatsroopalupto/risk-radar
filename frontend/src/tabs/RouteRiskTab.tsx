import RouteRiskChart from "../components/charts/RouteRiskChart";
import RiskTrendChart from "../components/charts/RiskTrendChart";
import SimulationControls from "../components/SimulationControls";
import RouteDetailCards from "../components/RouteDetailCards";

interface RouteRiskTabProps {
  refreshKey: number;
  onDataChanged: () => void;
}

function RouteRiskTab({
  refreshKey,
  onDataChanged,
}: RouteRiskTabProps) {
  return (
    <>
      <section className="route-risk-page">
        <h2>Route Risk &amp; Trend</h2>

        <p className="section-description">
          Monitored oil supply routes feeding Indian refineries via key
          maritime chokepoints.
        </p>

        <div className="route-risk-tab">
          <div className="route-risk-main">
            <RouteRiskChart refreshKey={refreshKey} />
            <RiskTrendChart refreshKey={refreshKey} />
          </div>

          <SimulationControls onDataChanged={onDataChanged} />
        </div>
      </section>
      <RouteDetailCards refreshKey={refreshKey} />
    </>
  );
}

export default RouteRiskTab;