"use client";

import { useEffect, useRef } from "react";
import { useChatStore } from "@/stores/chat-store";
import { useConfigStore } from "@/stores/config-store";
import { MessageBubble } from "./message-bubble";
import { MarkdownContent } from "./markdown-content";
import { SourcesPanel } from "./sources-panel";
import { ThinkingBlock } from "./thinking-block";

export function MessageList() {
  const { messages, isStreaming, streamingContent, streamingSources, streamingReasoning } = useChatStore();
  const showReasoning = useConfigStore((s) => s.config.show_reasoning);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, streamingContent]);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-2xl px-6 py-8 space-y-8">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} showReasoning={showReasoning} />
        ))}

        {isStreaming && (
          <div className="flex flex-col items-start slide-up">
            <p className="mb-1.5 text-xs font-medium text-muted-foreground">Systematology</p>
            <div className="w-full space-y-3">
              {streamingReasoning && (
                <ThinkingBlock reasoning={streamingReasoning} />
              )}

              <div className="text-[15px] leading-[1.65] text-foreground">
                {streamingContent ? (
                  <span className="streaming-cursor">
                    <MarkdownContent content={streamingContent} />
                  </span>
                ) : (
                  <span className="inline-flex gap-1 text-muted-foreground/50">
                    <span className="h-1.5 w-1.5 rounded-full bg-foreground/30 animate-pulse" />
                    <span className="h-1.5 w-1.5 rounded-full bg-foreground/20 animate-pulse [animation-delay:200ms]" />
                    <span className="h-1.5 w-1.5 rounded-full bg-foreground/10 animate-pulse [animation-delay:400ms]" />
                  </span>
                )}
              </div>

              {streamingSources.length > 0 && <SourcesPanel sources={streamingSources} />}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
