"use client";

import { BookOpen, Brain, Network, History } from "lucide-react";
import type { ReactNode } from "react";

const SUGGESTIONS: { icon: ReactNode; label: string; question: string }[] = [
  { icon: <BookOpen className="h-4 w-4" />, label: "基础概念", question: "什么是体系学？" },
  { icon: <Brain className="h-4 w-4" />, label: "学科体系", question: "钱学森的系统科学体系是什么？" },
  { icon: <Network className="h-4 w-4" />, label: "核心特征", question: "复杂系统有哪些核心特征？" },
  { icon: <History className="h-4 w-4" />, label: "演进历程", question: "系统工程方法论的演进历程？" },
];

interface Props {
  onSelect: (question: string) => void;
}

export function SuggestionPills({ onSelect }: Props) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {SUGGESTIONS.map((s) => (
        <button
          key={s.question}
          type="button"
          onClick={() => onSelect(s.question)}
          className="group flex items-start gap-3 rounded-xl border border-border/40 bg-card/30 p-4 text-left transition-all hover:bg-card/70 hover:border-emerald-500/30 hover:shadow-md hover:shadow-emerald-500/5"
        >
          <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500 transition-colors group-hover:bg-emerald-500/20">
            {s.icon}
          </span>
          <div className="min-w-0">
            <p className="text-xs font-medium text-muted-foreground/60 mb-0.5">{s.label}</p>
            <p className="text-sm text-foreground/80 group-hover:text-foreground leading-snug">{s.question}</p>
          </div>
        </button>
      ))}
    </div>
  );
}
