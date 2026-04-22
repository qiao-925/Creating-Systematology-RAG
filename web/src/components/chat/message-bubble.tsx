"use client";

import { Bot, User } from "lucide-react";
import type { ChatMessage } from "@/types";
import { MarkdownContent } from "./markdown-content";
import { SourcesPanel } from "./sources-panel";
import { ReasoningBlock } from "./reasoning-block";

interface Props {
  message: ChatMessage;
  showReasoning?: boolean;
}

export function MessageBubble({ message, showReasoning = true }: Props) {
  const isUser = message.role === "user";

  const scrollToSource = (index: number) => {
    const el = document.getElementById(`source-${index}`);
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
    el?.classList.add("ring-1", "ring-emerald-500/50");
    setTimeout(() => el?.classList.remove("ring-1", "ring-emerald-500/50"), 2000);
  };

  return (
    <div className={`flex gap-3.5 slide-up ${isUser ? "justify-end" : ""}`}>
      {!isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-500">
          <Bot className="h-4 w-4" />
        </div>
      )}

      <div className={`min-w-0 ${isUser ? "max-w-[75%]" : "max-w-[85%] flex-1"}`}>
        {/* Role label */}
        <p className={`mb-1 text-xs font-medium text-muted-foreground/70 ${isUser ? "text-right" : ""}`}>
          {isUser ? "You" : "Assistant"}
        </p>

        <div
          className={`rounded-2xl px-4 py-3 text-[15px] leading-[1.7] ${
            isUser
              ? "bg-primary text-primary-foreground ml-auto rounded-tr-md w-fit"
              : "bg-card/60 border border-border/40 rounded-tl-md"
          }`}
        >
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <MarkdownContent content={message.content} onCitationClick={scrollToSource} />
          )}
        </div>

        {!isUser && showReasoning && message.reasoning && (
          <ReasoningBlock reasoning={message.reasoning} />
        )}

        {!isUser && message.sources && (
          <SourcesPanel sources={message.sources} />
        )}
      </div>

      {isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  );
}
