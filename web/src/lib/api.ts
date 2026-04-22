import type { AppConfig, HealthStatus, ModelInfo, ResearchResult } from "@/types";

const BASE = "/api";
const STREAM_BASE =
  typeof window !== "undefined"
    ? `${window.location.protocol}//${window.location.hostname}:8000/api`
    : "/api";

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => json<HealthStatus>("/health"),
  getConfig: () => json<AppConfig>("/config"),
  updateConfig: (body: Partial<AppConfig>) =>
    json<AppConfig>("/config", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  getModels: () => json<ModelInfo[]>("/config/models"),
  research: (question: string) =>
    json<ResearchResult>("/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }),
};

export type SSEEvent = {
  event: string;
  data: string;
};

export async function* streamChat(
  message: string,
  sessionId?: string,
): AsyncGenerator<SSEEvent> {
  const res = await fetch(`${STREAM_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!res.ok) throw new Error(`Chat API ${res.status}`);
  if (!res.body) throw new Error("No response body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    let currentEvent = "";
    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        const data = line.slice(6);
        yield { event: currentEvent || "message", data };
        currentEvent = "";
      }
    }
  }
}
