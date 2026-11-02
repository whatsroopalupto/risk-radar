export type SignalSourceType = "news" | "price" | "vessel";

export type EventType =
  | "blockade_or_closure"
  | "attack_on_vessel"
  | "military_strike"
  | "port_or_terminal_disruption"
  | "sanctions"
  | "naval_buildup"
  | "diplomatic_escalation"
  | "policy_change"
  | "other";

export interface Signal {
  signal_id: string;
  source_type: SignalSourceType;
  source_name: string;
  title: string;
  body?: string;
  url?: string;
  published_at: string;
  fetched_at: string;
  raw: Record<string, unknown>;
}

export interface RiskExtraction {
  is_relevant: boolean;
  event_type: EventType;
  severity: number;
  affected_chokepoints: string[];
  affected_countries: string[];
  is_speculative: boolean;
  confidence: number;
  evidence: string;
  extractor: string;
}

export interface RiskAssessment {
  signal_id: string;
  extraction: RiskExtraction;
  credibility_tier: string;
  credibility_weight: number;
  recency_weight: number;
  type_weight: number;
  speculative_weight: number;
  component_scores: Record<string, number>;
  final_score: number;
  band: "low" | "medium" | "high";
  title?: string;
  source_name?: string;
  published_at?: string;
  url?: string;
}