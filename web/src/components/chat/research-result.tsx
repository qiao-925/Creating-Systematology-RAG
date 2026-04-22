"use client";

import {
  Scale,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  FileText,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { ResearchResult } from "@/types";
import { MarkdownContent } from "./markdown-content";

const CONFIDENCE_MAP = {
  high: { color: "bg-emerald-500/15 text-emerald-500 border-emerald-500/30", label: "High" },
  medium: { color: "bg-amber-500/15 text-amber-500 border-amber-500/30", label: "Medium" },
  low: { color: "bg-red-500/15 text-red-500 border-red-500/30", label: "Low" },
} as const;

interface Props {
  result: ResearchResult;
}

export function ResearchResultCard({ result }: Props) {
  const conf = CONFIDENCE_MAP[result.confidence] ?? CONFIDENCE_MAP.low;

  return (
    <div className="space-y-4 rounded-2xl border border-border/40 bg-card/60 p-5">
      {/* Judgment */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-sm font-medium text-foreground/80">
          <Scale className="h-4 w-4 text-emerald-500" />
          Judgment
          <Badge variant="outline" className={`ml-auto text-[10px] ${conf.color}`}>
            {conf.label} confidence
          </Badge>
        </div>
        <div className="text-[15px] leading-[1.7]">
          <MarkdownContent content={result.judgment} />
        </div>
      </div>

      {/* Evidence */}
      {result.evidence.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-foreground/80">
            <ShieldCheck className="h-4 w-4 text-blue-400" />
            Evidence ({result.evidence.length})
          </div>
          <div className="space-y-2">
            {result.evidence.map((e, i) => (
              <div
                key={i}
                className="rounded-lg border border-border/30 bg-muted/20 p-3 text-sm"
              >
                <p className="leading-relaxed text-foreground/80">{e.text}</p>
                {e.source_ref && (
                  <p className="mt-1.5 flex items-center gap-1 text-xs text-muted-foreground">
                    <FileText className="h-3 w-3" />
                    {e.source_ref}
                    {e.score > 0 && (
                      <span className="ml-auto font-mono">{(e.score * 100).toFixed(0)}%</span>
                    )}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tensions */}
      {result.tensions.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-foreground/80">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            Unresolved Tensions
          </div>
          <ul className="space-y-1 pl-5 text-sm text-foreground/70 list-disc">
            {result.tensions.map((t, i) => (
              <li key={i} className="leading-relaxed">{t}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Next questions */}
      {result.next_questions.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-foreground/80">
            <HelpCircle className="h-4 w-4 text-purple-400" />
            Next Questions
          </div>
          <ul className="space-y-1 pl-5 text-sm text-foreground/70 list-disc">
            {result.next_questions.map((q, i) => (
              <li key={i} className="leading-relaxed">{q}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
