"use client";

import type { ChatMessage } from "@/types";
import { MarkdownContent } from "./markdown-content";
import { SourcesPanel } from "./sources-panel";
import { ThinkingBlock } from "./thinking-block";

interface Props {
  message: ChatMessage;
  showReasoning?: boolean;
}

export function MessageBubble({ message, showReasoning = true }: Props) {
  const isUser = message.role === "user";

  const scrollToSource = (index: number) => {
    const el = document.getElementById(`source-${index}`);
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
    el?.classList.add("ring-1", "ring-primary/50");
    setTimeout(() => el?.classList.remove("ring-1", "ring-primary/50"), 2000);
  };

  return (
    <div className={`flex flex-col slide-up ${isUser ? "items-end" : "items-start"}`}>
      {/* Role label */}
      <p className="mb-1.5 text-xs font-medium text-muted-foreground">
        {isUser ? "You" : "CLDFlow"}
      </p>

      {/* Content */}
      <div className={`min-w-0 ${isUser ? "max-w-[85%]" : "max-w-full"}`}>
        {isUser ? (
          <div className="inline-block rounded-2xl bg-muted/50 px-4 py-3 text-[15px] leading-[1.65] text-foreground">
            <p>{message.content}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {/* Thinking block (reasoning) */}
            {showReasoning && message.reasoning && (
              <ThinkingBlock reasoning={message.reasoning} />
            )}

            {/* Answer content */}
            <div className="text-[15px] leading-[1.65] text-foreground">
              <MarkdownContent content={message.content} onCitationClick={scrollToSource} />
            </div>

            {/* Sources */}
            {message.sources && message.sources.length > 0 && (
              <SourcesPanel sources={message.sources} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
