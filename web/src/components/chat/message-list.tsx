"use client";

import { useEffect, useRef } from "react";
import { Bot } from "lucide-react";
import { useChatStore } from "@/stores/chat-store";
import { useConfigStore } from "@/stores/config-store";
import { MessageBubble } from "./message-bubble";
import { MarkdownContent } from "./markdown-content";
import { SourcesPanel } from "./sources-panel";

export function MessageList() {
  const { messages, isStreaming, streamingContent, streamingSources } = useChatStore();
  const showReasoning = useConfigStore((s) => s.config.show_reasoning);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, streamingContent]);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-4xl px-6 py-8 space-y-8">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} showReasoning={showReasoning} />
        ))}

        {isStreaming && (
          <div className="flex gap-3.5 slide-up">
            <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-500">
              <Bot className="h-4 w-4" />
            </div>
            <div className="min-w-0 max-w-[85%] flex-1">
              <p className="mb-1 text-xs font-medium text-muted-foreground/70">Assistant</p>
              <div className="rounded-2xl rounded-tl-md border border-border/40 bg-card/60 px-4 py-3 text-[15px] leading-[1.7]">
                {streamingContent ? (
                  <span className="streaming-cursor">
                    <MarkdownContent content={streamingContent} />
                  </span>
                ) : (
                  <span className="inline-flex gap-1.5 text-muted-foreground/50">
                    <span className="h-2 w-2 rounded-full bg-emerald-500/60 animate-pulse" />
                    <span className="h-2 w-2 rounded-full bg-emerald-500/40 animate-pulse [animation-delay:200ms]" />
                    <span className="h-2 w-2 rounded-full bg-emerald-500/20 animate-pulse [animation-delay:400ms]" />
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
