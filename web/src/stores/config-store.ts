import { create } from "zustand";
import type { AppConfig, HealthStatus, ModelInfo } from "@/types";

interface ConfigState {
  config: AppConfig;
  models: ModelInfo[];
  health: HealthStatus;
  setConfig: (partial: Partial<AppConfig>) => void;
  setModels: (models: ModelInfo[]) => void;
  setHealth: (health: HealthStatus) => void;
}

const defaultConfig: AppConfig = {
  selected_model: "deepseek-chat",
  llm_preset: "balanced",
  retrieval_strategy: "vector",
  use_agentic_rag: false,
  similarity_top_k: 5,
  similarity_threshold: 0.3,
  enable_rerank: false,
  show_reasoning: true,
  research_mode: false,
};

export const useConfigStore = create<ConfigState>((set) => ({
  config: defaultConfig,
  models: [],
  health: { status: "initializing", message: "Connecting..." },
  setConfig: (partial) =>
    set((s) => ({ config: { ...s.config, ...partial } })),
  setModels: (models) => set({ models }),
  setHealth: (health) => set({ health }),
}));
