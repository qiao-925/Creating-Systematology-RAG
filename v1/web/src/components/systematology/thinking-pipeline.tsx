"use client";

import { useState, useEffect, useRef } from "react";
import { Brain, ChevronDown, ChevronUp, Clock } from "lucide-react";

export type StepStatus = "done" | "running" | "waiting";

export interface StepLog {
  time: string;
  message: string;
}

export interface Step {
  label: string;
  name: string;
  status: StepStatus;
  detail?: string;
  logs?: StepLog[];
}

interface Props {
  steps?: Step[];
  expanded?: boolean;
}

const defaultSteps: Step[] = [
  { label: "①", name: "检索", status: "done", detail: "12 篇文献", logs: [] },
  { label: "②", name: "建图", status: "done", detail: "18 节点 24 边", logs: [] },
  { label: "③", name: "评估", status: "done", detail: "5 杠杆点", logs: [] },
];

const statusStyles: Record<StepStatus, { icon: string; bar: string; dot: string }> = {
  done: {
    icon: "bg-positive text-white",
    bar: "bg-positive w-full",
    dot: "bg-positive",
  },
  running: {
    icon: "bg-primary text-primary-foreground animate-pulse",
    bar: "bg-primary w-[65%] animate-pulse",
    dot: "bg-primary animate-pulse",
  },
  waiting: {
    icon: "border-2 border-border text-muted-foreground",
    bar: "bg-border w-0",
    dot: "bg-border",
  },
};

export function ThinkingPipeline({ steps = defaultSteps, expanded = true }: Props) {
  const allDone = steps.every((s) => s.status === "done");
  const hasRunning = steps.some((s) => s.status === "running");
  const statusText = allDone ? "分析完成" : hasRunning ? "分析中" : "等待中";

  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest log when new logs arrive
  useEffect(() => {
    if (hasRunning && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [steps, hasRunning]);

  // Collapsible state for each completed step's logs
  const [collapsedSteps, setCollapsedSteps] = useState<Set<string>>(new Set());
  const toggleCollapse = (name: string) => {
    setCollapsedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 text-sm border-b border-border/50">
        <Brain className="h-4 w-4 text-primary" />
        <span className="font-medium text-foreground">Thinking</span>
        <span className="text-muted-foreground">— {statusText}</span>
      </div>

      {expanded && (
        <div className="px-4 py-3 flex flex-col">
          {steps.map((step) => {
            const styles = statusStyles[step.status];
            const hasLogs = step.logs && step.logs.length > 0;
            const isCollapsed = collapsedSteps.has(step.name);
            const isRunning = step.status === "running";

            return (
              <div key={step.name}>
                {/* Step header row */}
                <div className="flex items-center gap-2.5 text-sm py-1.5">
                  {/* Status icon */}
                  <div
                    className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-semibold shrink-0 ${styles.icon}`}
                  >
                    {step.status === "done" ? "✓" : step.status === "running" ? "…" : ""}
                  </div>
                  {/* Step label */}
                  <span className="text-muted-foreground w-5 text-center shrink-0">
                    {step.label}
                  </span>
                  {/* Step name */}
                  <span className="text-foreground font-medium shrink-0">{step.name}</span>
                  {/* Progress bar */}
                  <div className="flex-1 h-1 rounded-full bg-border overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-700 ${styles.bar}`} />
                  </div>
                  {/* Status text or detail */}
                  {step.status === "running" && (
                    <span className="text-xs text-muted-foreground shrink-0 animate-pulse">
                      进行中...
                    </span>
                  )}
                  {step.status === "done" && step.detail && (
                    <span className="text-xs text-muted-foreground shrink-0">
                      {step.detail}
                    </span>
                  )}
                </div>

                {/* Log entries */}
                {hasLogs && (
                  <div className="ml-[2.75rem] mb-1">
                    {/* Log entries container with max-height and scroll */}
                    <div
                      className={`overflow-hidden transition-all duration-300 ${
                        isRunning
                          ? "max-h-48"
                          : isCollapsed
                            ? "max-h-0"
                            : "max-h-48"
                      }`}
                    >
                      <div className="max-h-48 overflow-y-auto rounded-md bg-muted/30 border border-border/30 p-2 space-y-0.5 font-mono text-[11px]">
                        {step.logs!.map((entry, i) => (
                          <div
                            key={i}
                            className="flex items-start gap-2 text-muted-foreground animate-in fade-in slide-up duration-200"
                          >
                            <Clock className="h-3 w-3 mt-0.5 shrink-0 text-muted-foreground/50" />
                            <span className="text-muted-foreground/60 shrink-0 w-10 text-right">
                              {entry.time}
                            </span>
                            <span className="text-foreground/80 break-all">
                              {entry.message}
                            </span>
                          </div>
                        ))}
                        <div ref={logsEndRef} />
                      </div>
                    </div>

                    {/* Toggle collapse button (only for done steps) */}
                    {step.status === "done" && step.logs!.length > 1 && (
                      <button
                        onClick={() => toggleCollapse(step.name)}
                        className="flex items-center gap-1 text-[11px] text-muted-foreground/60 hover:text-muted-foreground transition-colors mt-1"
                      >
                        {isCollapsed ? (
                          <>
                            <ChevronDown className="h-3 w-3" />
                            展开 {step.logs!.length} 条日志
                          </>
                        ) : (
                          <>
                            <ChevronUp className="h-3 w-3" />
                            收起日志
                          </>
                        )}
                      </button>
                    )}
                  </div>
                )}

                {/* Connector line between steps (except last) */}
                {step !== steps[steps.length - 1] && (
                  <div
                    className={`ml-[2.75rem] w-px h-2 ${
                      step.status === "done" ? "bg-positive/30" : "bg-border"
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
