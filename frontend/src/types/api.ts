export interface SourceRun {
  status: string;
  fetched: number;
  error?: string;
}

export interface IngestRunStats {
  run_id: string;
  started_at: string;
  finished_at: string;
  per_source: Record<string, SourceRun>;
  deduped: number;
  filtered_out: number;
  extracted: number;
  extractor_used: string;
  errors: string[];
  scenario_id?: string;
}

export interface HealthResponse {
  sources: Record<string, unknown>;
  extractor: {
    active: string;
    reason?: string;
};
  extractor_mix: Record<string, unknown>;
  db_counts: Record<string, number>;
  version: string;
  last_run_time?: string;
}

export interface GraphNode {
  id: string;
  [key: string]: unknown;
}

export interface GraphEdge {
  source: string;
  target: string;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}