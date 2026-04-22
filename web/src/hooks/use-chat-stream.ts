"use client";

import { useCallback } from "react";
import { streamChat } from "@/lib/api";
import { useChatStore } from "@/stores/chat-store";

export function useChatStream() {
  const {
    isStreaming,
    addUserMessage,
    startStreaming,
    appendToken,
    setSources,
    setReasoning,
    finishStreaming,
    setStreamError,
  } = useChatStore();

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isStreaming) return;

      addUserMessage(content);
      startStreaming();

      try {
        for await (const evt of streamChat(content)) {
          const parsed = JSON.parse(evt.data);

          switch (evt.event) {
            case "token":
              appendToken(parsed.content ?? "");
              break;
            case "sources":
              setSources(Array.isArray(parsed) ? parsed : []);
              break;
            case "reasoning":
              setReasoning(parsed.content ?? "");
              break;
            case "done":
              finishStreaming();
              return;
            case "error":
              setStreamError(parsed.message ?? "Unknown error");
              return;
          }
        }
        // stream ended without done event
        finishStreaming();
      } catch (err) {
        setStreamError(err instanceof Error ? err.message : String(err));
      }
    },
    [isStreaming, addUserMessage, startStreaming, appendToken, setSources, setReasoning, finishStreaming, setStreamError],
  );

  return { sendMessage, isStreaming };
}
