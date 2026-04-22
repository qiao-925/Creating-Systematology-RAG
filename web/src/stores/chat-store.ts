import { create } from "zustand";
import type { ChatMessage, Source } from "@/types";

interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
  streamingContent: string;
  streamingSources: Source[];
  streamingReasoning: string;

  addUserMessage: (content: string) => string;
  startStreaming: () => void;
  appendToken: (token: string) => void;
  setSources: (sources: Source[]) => void;
  setReasoning: (reasoning: string) => void;
  finishStreaming: () => void;
  setStreamError: (error: string) => void;
  resetChat: () => void;
}

let nextId = 0;
const genId = () => `msg-${Date.now()}-${++nextId}`;

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isStreaming: false,
  streamingContent: "",
  streamingSources: [],
  streamingReasoning: "",

  addUserMessage: (content) => {
    const id = genId();
    set((s) => ({
      messages: [
        ...s.messages,
        { id, role: "user", content, timestamp: Date.now() },
      ],
    }));
    return id;
  },

  startStreaming: () =>
    set({ isStreaming: true, streamingContent: "", streamingSources: [], streamingReasoning: "" }),

  appendToken: (token) =>
    set((s) => ({ streamingContent: s.streamingContent + token })),

  setSources: (sources) => set({ streamingSources: sources }),

  setReasoning: (reasoning) => set({ streamingReasoning: reasoning }),

  finishStreaming: () => {
    const { streamingContent, streamingSources, streamingReasoning, messages } = get();
    if (!streamingContent && streamingSources.length === 0) {
      set({ isStreaming: false });
      return;
    }
    const msg: ChatMessage = {
      id: genId(),
      role: "assistant",
      content: streamingContent,
      sources: streamingSources.length > 0 ? streamingSources : undefined,
      reasoning: streamingReasoning || undefined,
      timestamp: Date.now(),
    };
    set({
      messages: [...messages, msg],
      isStreaming: false,
      streamingContent: "",
      streamingSources: [],
      streamingReasoning: "",
    });
  },

  setStreamError: (error) => {
    const { messages } = get();
    set({
      messages: [
        ...messages,
        { id: genId(), role: "assistant", content: `Error: ${error}`, timestamp: Date.now() },
      ],
      isStreaming: false,
      streamingContent: "",
    });
  },

  resetChat: () =>
    set({
      messages: [],
      isStreaming: false,
      streamingContent: "",
      streamingSources: [],
      streamingReasoning: "",
    }),
}));
