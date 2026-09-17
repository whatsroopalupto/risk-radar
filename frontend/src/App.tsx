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

function App() {
  const [activeTab, setActiveTab] = useState<TabId>("route-risk");
  const [refreshKey, setRefreshKey] = useState(0);

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

        {activeTab === "analytics" && <IntelligenceAnalyticsTab />}

        {activeTab === "refinery" && <RefineryExposureTab />}

        {activeTab === "signals" && <SignalFeedTab />}

        {activeTab === "history" && <IngestionHistoryTab />}

        {activeTab === "graph" && <GraphAboutTab />}
      </div>
    </main>
  );
}

export default App;