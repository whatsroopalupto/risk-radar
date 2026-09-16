export type TabId =
  | "route-risk"
  | "analytics"
  | "refinery"
  | "signals"
  | "history"
  | "graph";

interface Tab {
  id: TabId;
  label: string;
}

const tabs: Tab[] = [
  { id: "route-risk", label: "Route Risk & Trend" },
  { id: "analytics", label: "Intelligence Analytics" },
  { id: "refinery", label: "Refinery Exposure" },
  { id: "signals", label: "Signal Feed" },
  { id: "history", label: "Ingestion History" },
  { id: "graph", label: "Graph & About" },
];

interface TabNavProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

function TabNav({ activeTab, onTabChange }: TabNavProps) {
  return (
    <nav className="tab-nav">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`tab-button ${
            activeTab === tab.id ? "active" : ""
          }`}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}

export default TabNav;