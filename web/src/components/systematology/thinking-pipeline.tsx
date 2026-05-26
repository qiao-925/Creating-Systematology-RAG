"use client";

import { Settings } from "lucide-react";

export type StepStatus = "done" | "running" | "waiting";

export interface Step {
  label: string;
  name: string;
  status: StepStatus;
  detail?: string;
}

interface Props {
  steps?: Step[];
  expanded?: boolean;
}

const defaultSteps: Step[] = [
  { label: "①", name: "检索", status: "done", detail: "12 篇文献" },
  { label: "②", name: "建图", status: "done", detail: "18 节点 24 边" },
  { label: "③", name: "评估", status: "done", detail: "5 杠杆点" },
];

const statusStyles: Record<StepStatus, { icon: string; bar: string }> = {
  done: {
    icon: "bg-positive text-white",
    bar: "bg-positive w-full",
  },
  running: {
    icon: "bg-primary text-primary-foreground animate-pulse",
    bar: "bg-primary w-[65%] animate-pulse",
  },
  waiting: {
    icon: "border-2 border-border text-muted-foreground",
    bar: "bg-border w-0",
  },
};

export function ThinkingPipeline({ steps = defaultSteps, expanded = true }: Props) {
  const allDone = steps.every((s) => s.status === "done");
  const statusText = allDone ? "分析完成" : "分析中";

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3 text-sm text-muted-foreground">
        <Settings className="h-4 w-4" />
        <span className="font-medium">Thinking — {statusText}</span>
      </div>
      {expanded && (
        <div className="px-4 pb-3 flex flex-col gap-2">
          {steps.map((step) => {
            const styles = statusStyles[step.status];
            return (
              <div key={step.name} className="flex items-center gap-2.5 text-sm">
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-semibold shrink-0 ${styles.icon}`}
                >
                  {step.status === "done" ? "✓" : step.status === "running" ? "…" : ""}
                </div>
                <span className="text-muted-foreground w-5 text-center shrink-0">
                  {step.label}
                </span>
                <span className="text-foreground shrink-0">{step.name}</span>
                <div className="flex-1 h-1 rounded-full bg-border overflow-hidden">
                  <div className={`h-full rounded-full transition-all ${styles.bar}`} />
                </div>
                {step.detail && (
                  <span className="text-xs text-muted-foreground shrink-0">
                    {step.detail}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
