"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, GitGraph } from "lucide-react";
import { HeaderBar } from "@/components/chat/header-bar";
import { ChatInput } from "@/components/chat/chat-input";
import { ThinkingPipeline } from "./thinking-pipeline";
import { SourceCards } from "./source-cards";
import { LeverageTable } from "./leverage-table";
import { CLDCanvasSVG } from "./cld-canvas-svg";
import { sampleCLDData } from "./cld-canvas-types";
import { adaptLeveragePoints, adaptCLDData } from "./cl-data-adapter";
import { useAnalysisPipeline } from "@/hooks/use-analysis-pipeline";
import type { SystematologyFailureReport } from "@/types";

interface EvidenceSource {
  tier: "T1" | "T2" | "T3";
  title: string;
  meta: string;
}

export function RuntimePage({ initialQuestion = "" }: { initialQuestion?: string }) {
  const router = useRouter();
  const {
    loading,
    error,
    result,
    question,
    animateCanvas,
    steps,
    successReport,
    handleSend,
    reset,
  } = useAnalysisPipeline();

  const autoRan = useRef(false);

  useEffect(() => {
    if (initialQuestion && !autoRan.current) {
      autoRan.current = true;
      handleSend(initialQuestion);
    }
  }, [initialQuestion, handleSend]);

  const report = result?.report;
  const isFailure = report ? "stage" in report && "reason" in report : false;
  const hasData = !!successReport && !!successReport.cld_visualization?.nodes;

  // Derive canvas data
  const canvasData = hasData
    ? adaptCLDData(successReport!.cld_visualization!.nodes!, successReport!.cld_visualization!.edges ?? [])
    : sampleCLDData;

  // Derive sources
  const evidenceSources = ((): EvidenceSource[] | undefined => {
    const sources = successReport?.evidence_tracing?.sources;
    if (Array.isArray(sources) && sources.length > 0) return sources as EvidenceSource[];
    return undefined;
  })();

  // Derive leverage points
  const leveragePoints = successReport?.leverage_ranking
    ? adaptLeveragePoints(successReport.leverage_ranking)
    : undefined;

  return (
    <div className="flex flex-1 flex-col h-full overflow-hidden">
      <HeaderBar
        questionTitle={question || undefined}
        status={loading ? "running" : "completed"}
        onNewConversation={reset}
        onBack={() => router.push("/")}
      />

      <div className="flex flex-1 overflow-hidden flex-col md:flex-row">
        {/* Left: Message Area */}
        <div className="w-full md:w-[45%] lg:w-[45%] flex flex-col border-b md:border-b-0 md:border-r border-border overflow-hidden order-2 md:order-1">
          <div className="flex-1 overflow-y-auto p-4 md:p-6 flex flex-col gap-4">
            {error && (
              <div className="flex items-center gap-2 rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-2.5 text-xs text-destructive">
                <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                {error}
              </div>
            )}

            {isFailure && (
              <div className="rounded-lg border border-amber-500/50 bg-amber-500/10 p-4 space-y-2">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-amber-500" />
                  <span className="text-sm font-semibold text-amber-600">分析失败</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  阶段：{(report as SystematologyFailureReport).stage}
                </p>
                <p className="text-sm">{(report as SystematologyFailureReport).reason}</p>
              </div>
            )}

            <ThinkingPipeline steps={steps} />
            <LeverageTable points={leveragePoints} />

            {successReport?.synthesized_insights && (
              <div className="rounded-lg border border-border bg-card p-4">
                <p className="text-sm font-medium text-muted-foreground mb-2">综合洞察</p>
                <p className="text-sm text-foreground whitespace-pre-wrap">
                  {successReport.synthesized_insights}
                </p>
              </div>
            )}

            <SourceCards sources={evidenceSources} />
          </div>
        </div>

        {/* Right: Canvas */}
        <div className="w-full md:w-[55%] lg:w-[55%] flex flex-col overflow-hidden order-1 md:order-2 min-h-[300px] md:min-h-0">
          {hasData || loading ? (
            <CLDCanvasSVG data={canvasData} animate={animateCanvas} />
          ) : (
            /* Placeholder before any analysis */
            <div className="flex flex-1 items-center justify-center">
              <div className="text-center space-y-3 animate-in fade-in duration-500">
                <div className="flex justify-center">
                  <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted/50 border border-border/50">
                    <GitGraph className="h-8 w-8 text-muted-foreground/40" />
                  </div>
                </div>
                <p className="text-sm text-muted-foreground max-w-[220px] leading-relaxed">
                  输入研究问题，开始因果回路分析
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="border-t border-border bg-card px-4 md:px-6 py-3 md:py-4 flex-shrink-0">
        <ChatInput
          onSend={handleSend}
          disabled={loading}
          placeholder={loading ? "分析中..." : "继续追问...（Shift+Enter 换行）"}
        />
      </div>
    </div>
  );
}
