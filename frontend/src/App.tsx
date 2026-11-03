import { useEffect, useState } from "react";
import Header from "./components/Header";
import StatusStrip from "./components/StatusStrip";
import KpiRow from "./components/KpiRow";
import IngestionFunnelBanner from "./components/IngestionFunnelBanner";
import TabNav, { type TabId } from "./components/TabNav";
import RouteRiskTab from "./tabs/RouteRiskTab";
import IntelligenceAnalyticsTab from "./tabs/IntelligenceAnalyticsTab";
import RefineryExposureTab from "./tabs/RefineryExposureTab";
import SignalFeedTab from "./tabs/SignalFeedTab";
import IngestionHistoryTab from "./tabs/IngestionHistoryTab";
import GraphAboutTab from "./tabs/GraphAboutTab";
import VesselActivityTab from "./tabs/VesselActivityTab";
import EvidenceTab from "./tabs/EvidenceTab";
import TradeDataTab from "./tabs/TradeDataTab";
import ValidationTab from "./tabs/ValidationTab";

function App() {
  const [activeTab, setActiveTab] = useState<TabId>("route-risk");
  const [refreshKey, setRefreshKey] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(() => setRefreshKey((value) => value + 1), 30000);
    return () => window.clearInterval(timer);
  }, []);

  const [theme, setTheme] = useState(
    () => localStorage.getItem("risk-radar-theme") || "light",
  );

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("risk-radar-theme", theme);
  }, [theme]);

  function handleDataChanged() {
    setRefreshKey((value) => value + 1);
  }

  return (
    <main>
      <Header
        theme={theme}
        onThemeChange={() =>
          setTheme(theme === "light" ? "dark" : "light")
        }
      />
      <StatusStrip refreshKey={refreshKey} />
      <KpiRow refreshKey={refreshKey} />
      <IngestionFunnelBanner refreshKey={refreshKey} />

      <TabNav
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      <div className="tab-content">
        {activeTab === "route-risk" && (
          <RouteRiskTab
            refreshKey={refreshKey}
            onDataChanged={handleDataChanged}
          />
        )}

        {activeTab === "analytics" && <IntelligenceAnalyticsTab refreshKey={refreshKey} />}

        {activeTab === "refinery" && <RefineryExposureTab refreshKey={refreshKey} />}

        {activeTab === "signals" && <SignalFeedTab refreshKey={refreshKey} />}

        {activeTab === "history" && <IngestionHistoryTab refreshKey={refreshKey} />}

        {activeTab === "graph" && <GraphAboutTab />}
        {activeTab === "vessels" && <VesselActivityTab refreshKey={refreshKey} />}
        {activeTab === "evidence" && <EvidenceTab />}
        {activeTab === "trade" && <TradeDataTab refreshKey={refreshKey} />}
        {activeTab === "validation" && <ValidationTab />}
      </div>
    </main>
  );
}

export default App;
