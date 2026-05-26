"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle } from "lucide-react";
import { HeaderBar } from "@/components/chat/header-bar";
import { ChatInput } from "@/components/chat/chat-input";
import { SettingsSheet } from "@/components/settings/settings-sheet";
import { ThinkingPipeline } from "./thinking-pipeline";
import { SourceCards } from "./source-cards";
import { LeverageTable } from "./leverage-table";
import { CLDCanvasSwitcher } from "./cld-canvas-switcher";
import { sampleCLDData } from "./cld-canvas-types";
import { adaptLeveragePoints, adaptCLDData } from "./cl-data-adapter";
import { api } from "@/lib/api";
import type { SystematologyResponse, SystematologyReport, SystematologyFailureReport } from "@/types";
import type { Step } from "./thinking-pipeline";
import type { CLDData } from "./cld-canvas-types";

function isFailureReport(
  report: SystematologyReport | SystematologyFailureReport,
): report is SystematologyFailureReport {
  return "stage" in report && "reason" in report;
}

function isSystematologyReport(
  report: SystematologyReport | SystematologyFailureReport,
): report is SystematologyReport {
  return !isFailureReport(report);
}

export function RuntimePage({ initialQuestion = "" }: { initialQuestion?: string }) {
  const router = useRouter();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SystematologyResponse | null>(null);
  const [question, setQuestion] = useState(initialQuestion);
  const autoRan = useRef(false);

  // Auto-trigger analysis when initialQuestion is provided
  useEffect(() => {
    if (initialQuestion && !autoRan.current) {
      autoRan.current = true;
      handleSend(initialQuestion);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuestion]);

  const report = result?.report;
  const isFailure = report ? isFailureReport(report) : false;
  const isSuccess = report ? isSystematologyReport(report) : false;

  // Derive thinking steps from loading/result state
  const steps: Step[] = [
    { label: "①", name: "检索", status: loading ? "running" : isSuccess && (report as SystematologyReport).cld_visualization ? "done" : "waiting", detail: loading ? "检索中..." : undefined },
    { label: "②", name: "建图", status: loading ? "waiting" : isSuccess && (report as SystematologyReport).cld_visualization?.nodes ? "done" : "waiting", detail: isSuccess && (report as SystematologyReport).cld_visualization?.nodes ? `${(report as SystematologyReport).cld_visualization!.nodes!.length} 节点` : undefined },
    { label: "③", name: "评估", status: loading ? "waiting" : isSuccess && (report as SystematologyReport).leverage_ranking ? "done" : "waiting", detail: isSuccess && (report as SystematologyReport).leverage_ranking ? `${(report as SystematologyReport).leverage_ranking!.length} 杠杆点` : undefined },
  ];

  // Derive canvas data from API response
  const canvasData: CLDData = (() => {
    if (isSuccess && (report as SystematologyReport).cld_visualization?.nodes) {
      const r = report as SystematologyReport;
      return adaptCLDData(r.cld_visualization!.nodes!, r.cld_visualization!.edges ?? []);
    }
    return sampleCLDData;
  })();

  // Derive leverage points from API response
  const leveragePoints = (() => {
    if (isSuccess && (report as SystematologyReport).leverage_ranking) {
      return adaptLeveragePoints((report as SystematologyReport).leverage_ranking!);
    }
    return undefined;
  })();

  const handleSend = useCallback(async (message: string) => {
    if (!message.trim()) return;
    setQuestion(message.trim());
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.systematologyAnalyze(message.trim());
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "分析失败");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleNewConversation = useCallback(() => {
    setResult(null);
    setError(null);
    setQuestion("");
    setLoading(false);
  }, []);

  return (
    <div className="flex flex-1 flex-col h-full overflow-hidden">
      <HeaderBar
        onSettingsClick={() => setSettingsOpen(true)}
        questionTitle={question || undefined}
        status={loading ? "running" : "completed"}
        onNewConversation={handleNewConversation}
        onBack={() => router.push("/")}
      />
      <SettingsSheet open={settingsOpen} onOpenChange={setSettingsOpen} />

      {/* Main area: responsive dual-column */}
      <div className="flex flex-1 overflow-hidden flex-col md:flex-row">
        {/* Left: Message Area */}
        <div className="w-full md:w-[45%] lg:w-[45%] flex flex-col border-b md:border-b-0 md:border-r border-border overflow-hidden order-2 md:order-1">
          <div className="flex-1 overflow-y-auto p-4 md:p-6 flex flex-col gap-4">
            {/* Error banner */}
            {error && (
              <div className="flex items-center gap-2 rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-2.5 text-xs text-destructive">
                <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                {error}
              </div>
            )}

            {/* Failure report */}
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
            <SourceCards />
            <LeverageTable points={leveragePoints} />

            {/* Insights */}
            {isSuccess && (report as SystematologyReport).synthesized_insights && (
              <div className="rounded-lg border border-border bg-card p-4">
                <p className="text-sm font-medium text-muted-foreground mb-2">综合洞察</p>
                <p className="text-sm text-foreground whitespace-pre-wrap">
                  {(report as SystematologyReport).synthesized_insights}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right: CLD Canvas */}
        <div className="w-full md:w-[55%] lg:w-[55%] flex flex-col overflow-hidden order-1 md:order-2 min-h-[300px] md:min-h-0">
          <CLDCanvasSwitcher data={canvasData} />
        </div>
      </div>

      {/* Input Area */}
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
