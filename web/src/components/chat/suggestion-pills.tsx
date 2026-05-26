"use client";

import { Globe, Zap, HeartPulse, TrendingUp, ArrowRight } from "lucide-react";
import type { ReactNode } from "react";

const SUGGESTIONS: {
  icon: ReactNode;
  label: string;
  question: string;
  stats: string;
  color: string;
}[] = [
  {
    icon: <Globe className="h-4 w-4" />,
    label: "气候变化",
    question: "气候变化对粮食安全的因果影响路径？",
    stats: "8 变量 · 3 回路",
    color: "text-primary",
  },
  {
    icon: <Zap className="h-4 w-4" />,
    label: "能源政策",
    question: "新能源补贴如何通过市场结构影响碳排放？",
    stats: "10 变量 · 5 杠杆点",
    color: "text-yellow-500",
  },
  {
    icon: <HeartPulse className="h-4 w-4" />,
    label: "公共卫生",
    question: "老龄化对医疗系统支出的因果传导机制？",
    stats: "6 变量 · 2 回路",
    color: "text-negative",
  },
  {
    icon: <TrendingUp className="h-4 w-4" />,
    label: "经济系统",
    question: "利率变动对房地产市场的反馈循环分析？",
    stats: "7 变量 · 4 回路",
    color: "text-primary",
  },
];

interface Props {
  onSelect: (question: string) => void;
}

export function SuggestionPills({ onSelect }: Props) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">或者从这些问题开始</p>
      <div className="grid grid-cols-2 gap-3">
        {SUGGESTIONS.map((s) => (
          <button
            key={s.question}
            type="button"
            onClick={() => onSelect(s.question)}
            className="group flex items-start gap-3 rounded-xl border border-border/40 bg-card/30 p-4 text-left transition-all hover:bg-card/70 hover:border-border hover:shadow-md"
          >
            <span
              className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted/50 transition-colors ${s.color}`}
            >
              {s.icon}
            </span>
            <div className="min-w-0 flex-1">
              <p className={`text-xs font-medium mb-0.5 ${s.color}`}>{s.label}</p>
              <p className="text-sm text-foreground/80 group-hover:text-foreground leading-snug">
                {s.question}
              </p>
              <p className="text-xs text-muted-foreground/60 mt-1">{s.stats}</p>
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground/40 group-hover:text-foreground/60 mt-1 shrink-0 transition-colors" />
          </button>
        ))}
      </div>
    </div>
  );
}
