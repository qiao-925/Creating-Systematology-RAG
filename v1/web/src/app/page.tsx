"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle } from "lucide-react";
import { useConfigStore } from "@/stores/config-store";
import { useHealthPoll } from "@/hooks/use-health-poll";
import { ChatInput } from "@/components/chat/chat-input";
import { SuggestionPills } from "@/components/chat/suggestion-pills";

export default function Home() {
  useHealthPoll();
  const router = useRouter();
  const health = useConfigStore((s) => s.health);

  const handleSend = useCallback(
    (message: string) => {
      if (!message.trim()) return;
      router.push(`/runtime?q=${encodeURIComponent(message.trim())}`);
    },
    [router],
  );

  // Loading screen
  if (health.status === "initializing") {
    return (
      <div className="flex flex-1 items-center justify-center">
        <div className="text-center space-y-4">
          <div className="h-8 w-8 rounded-full border-2 border-emerald-400 border-t-transparent animate-spin mx-auto" />
          <p className="text-sm text-muted-foreground">Initializing services...</p>
        </div>
      </div>
    );
  }

  const apiError = health.status === "error" ? health.message : null;

  return (
    <div className="flex flex-1 flex-col animate-in fade-in duration-500">
      <div className="flex flex-1 flex-col items-center justify-center pb-24">
        <div className="w-full max-w-3xl space-y-10 px-6">
          <div className="space-y-3 text-center">
            <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground via-foreground/80 to-emerald-500 bg-clip-text text-transparent">
              Creating Systematology
            </h1>
            <p className="text-muted-foreground/70 text-base">
              基于 RAG 的知识研究助手 — 探索体系学的智慧
            </p>
          </div>
          <ChatInput
            onSend={handleSend}
            disabled={false}
            placeholder="输入你的研究问题，例如：新能源补贴如何影响碳排放？"
            variant="inline"
            autoFocus
          />
          <p className="text-xs text-center text-muted-foreground/60">
            Enter 发送 · Shift+Enter 换行 · 支持中文/英文
          </p>
          <SuggestionPills onSelect={handleSend} />
          {apiError && (
            <div className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-2.5 text-xs text-amber-600">
              <AlertCircle className="h-3.5 w-3.5 shrink-0" />
              {apiError} — 原型预览模式，后端未连接
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
