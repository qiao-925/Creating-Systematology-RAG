export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  reasoning?: string;
  timestamp: number;
}

export interface Source {
  title?: string;
  file_path?: string;
  content?: string;
  score?: number;
  metadata?: Record<string, unknown>;
}

export type AppMode = "chat" | "research" | "systematology";

export interface AppConfig {
  selected_model: string;
  llm_preset: string;
  retrieval_strategy: string;
  use_agentic_rag: boolean;
  similarity_top_k: number;
  similarity_threshold: number;
  enable_rerank: boolean;
  show_reasoning: boolean;
  research_mode: boolean;
}

export interface ModelInfo {
  id: string;
  name: string;
  supports_reasoning: boolean;
}

export interface HealthStatus {
  status: "ready" | "initializing" | "error";
  message: string;
  progress?: Record<string, unknown> | null;
}

export interface EvidenceItem {
  query: string;
  text: string;
  source_ref: string;
  score: number;
}

export interface ResearchResult {
  judgment: string;
  evidence: EvidenceItem[];
  confidence: "high" | "medium" | "low";
  tensions: string[];
  next_questions: string[];
}

// Systematology types
export interface SystematologyRequest {
  question: string;
  documents?: string[];
}

export interface SystematologyNode {
  id: string;
  label: string;
  description?: string;
}

export interface SystematologyEdge {
  source: string;
  target: string;
  relation: string;
  weight?: number;
}

export interface SystematologyLeveragePoint {
  node_id: string;
  node_label: string;
  impact_score: number;
  confidence: number;
  rank: number;
}

export interface SystematologyReport {
  cld_visualization?: {
    nodes?: SystematologyNode[];
    edges?: SystematologyEdge[];
    raw_response?: string;
  };
  scenario_comparison?: Record<string, unknown>;
  leverage_ranking?: SystematologyLeveragePoint[];
  synthesized_insights?: string;
  evidence_tracing?: Record<string, unknown>;
}

export interface SystematologyFailureReport {
  run_id: string;
  stage: string;
  reason: string;
  details?: Record<string, unknown>;
}

export interface SystematologyResponse {
  success: boolean;
  report: SystematologyReport | SystematologyFailureReport;
}
