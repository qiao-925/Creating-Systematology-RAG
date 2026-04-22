"use client";

import { useState, useCallback } from "react";
import { Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { useChatStore } from "@/stores/chat-store";
import { useConfigStore } from "@/stores/config-store";
import { useChatStream } from "@/hooks/use-chat-stream";
import { useHealthPoll } from "@/hooks/use-health-poll";
import { HeaderBar } from "@/components/chat/header-bar";
import { MessageList } from "@/components/chat/message-list";
import { ChatInput } from "@/components/chat/chat-input";
import { SuggestionPills } from "@/components/chat/suggestion-pills";
import { SettingsSheet } from "@/components/settings/settings-sheet";
import { ResearchResultCard } from "@/components/chat/research-result";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { ResearchResult } from "@/types";

export default function Home() {
  useHealthPoll();
  const { sendMessage, isStreaming } = useChatStream();
  const hasMessages = useChatStore((s) => s.messages.length > 0);
  const health = useConfigStore((s) => s.health);
  const isResearchMode = useConfigStore((s) => s.config.research_mode);

  const [settingsOpen, setSettingsOpen] = useState(false);
  const [researchResult, setResearchResult] = useState<ResearchResult | null>(null);
  const [researchLoading, setResearchLoading] = useState(false);

  const handleSend = useCallback(
    async (message: string) => {
      if (isResearchMode) {
        setResearchLoading(true);
        setResearchResult(null);
        try {
          const result = await api.research(message);
          setResearchResult(result);
        } catch (err) {
          console.error("Research failed:", err);
        } finally {
          setResearchLoading(false);
        }
      } else {
        sendMessage(message);
      }
    },
    [isResearchMode, sendMessage],
  );

  // Loading screen
  if (health.status === "initializing") {
    return (
      <div className="flex flex-1 items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-400 mx-auto" />
          <p className="text-sm text-muted-foreground">Initializing services...</p>
        </div>
      </div>
    );
  }

  // Error screen
  if (health.status === "error") {
    return (
      <div className="flex flex-1 items-center justify-center">
        <div className="text-center space-y-4 max-w-sm px-6">
          <AlertCircle className="h-8 w-8 text-destructive mx-auto" />
          <p className="text-sm text-destructive">{health.message}</p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.location.reload()}
            className="gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const busy = isStreaming || researchLoading;

  // Landing (no messages and no research result)
  if (!hasMessages && !researchResult) {
    return (
      <div className="flex flex-1 flex-col animate-in fade-in duration-500">
        <HeaderBar onSettingsClick={() => setSettingsOpen(true)} />
        <SettingsSheet open={settingsOpen} onOpenChange={setSettingsOpen} />
        <div className="flex flex-1 flex-col items-center justify-center pb-24">
          <div className="w-full max-w-3xl space-y-10 px-6">
            <div className="space-y-3 text-center">
              <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground via-foreground/80 to-emerald-500 bg-clip-text text-transparent">
                Creating Systematology
              </h1>
              <p className="text-muted-foreground/70 text-base">
                {isResearchMode
                  ? "研究模式 — 结构化深度研究输出"
                  : "基于 RAG 的知识研究助手 — 探索体系学的智慧"}
              </p>
            </div>
            <SuggestionPills onSelect={handleSend} />
            <ChatInput onSend={handleSend} disabled={busy} placeholder={isResearchMode ? "输入研究问题..." : "输入你的问题..."} variant="inline" autoFocus />
            {researchLoading && (
              <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Researching...
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Research result view
  if (researchResult) {
    return (
      <div className="flex flex-1 flex-col">
        <HeaderBar onSettingsClick={() => setSettingsOpen(true)} />
        <SettingsSheet open={settingsOpen} onOpenChange={setSettingsOpen} />
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-4xl px-6 py-8 space-y-6">
            <ResearchResultCard result={researchResult} />
            <div className="text-center">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setResearchResult(null)}
                className="gap-1.5"
              >
                New Research
              </Button>
            </div>
          </div>
        </div>
        <ChatInput onSend={handleSend} disabled={researchLoading} placeholder="输入新的研究问题..." />
      </div>
    );
  }

  // Chat view
  return (
    <div className="flex flex-1 flex-col">
      <HeaderBar onSettingsClick={() => setSettingsOpen(true)} />
      <SettingsSheet open={settingsOpen} onOpenChange={setSettingsOpen} />
      <MessageList />
      <ChatInput onSend={handleSend} disabled={busy} />
    </div>
  );
}
