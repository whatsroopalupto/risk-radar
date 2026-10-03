export type RiskBand = "low" | "medium" | "high";

export type Chokepoint =
  | "hormuz"
  | "bab_el_mandeb"
  | "suez"
  | "malacca"
  | "none";

export interface RouteRisk {
  route_id: string;
  name: string;
  chokepoints: Chokepoint[];
  news_score: number;
  market_score: number;
  composite_score: number;
  band: RiskBand;
  contributing_signal_ids: string[];
  computed_at: string;
}

export interface RouteRiskTimeseriesPoint {
  route_id: string;
  name: string;
  points: {
    date: string;
    news_score: number;
    band: RiskBand;
    signal_count: number;
  }[];
}

export interface RefineryContribution {
  route_id: string;
  dependency_share: number;
  route_score: number;
}

export interface RefineryExposure {
  refinery_id: string;
  name: string;
  operator: string;
  port_id: string;
  exposure_score: number;
  band: RiskBand;
  contributions: RefineryContribution[];
}

export interface Scenario {
  id: string;
  label: string;
  description: string;
}