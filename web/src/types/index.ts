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
