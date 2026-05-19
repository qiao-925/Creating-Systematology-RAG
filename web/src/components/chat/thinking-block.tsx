"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";

interface Props {
  reasoning: string;
}

export function ThinkingBlock({ reasoning }: Props) {
  const [expanded, setExpanded] = useState(true);

  if (!reasoning) return null;

  // Parse reasoning into steps (split by newlines or bullet points)
  const steps = reasoning
    .split(/\n/)
    .filter((line) => line.trim())
    .map((line) => line.replace(/^[-•*]\s*/, "").trim());

  return (
    <div className="rounded-lg border border-border/50 bg-muted/30 p-3.5">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 text-xs font-medium text-muted-foreground"
      >
        <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-muted-foreground/30 border-t-foreground" />
        <span>Thinking...</span>
        <ChevronDown
          className={`ml-auto h-3.5 w-3.5 transition-transform ${
            expanded ? "rotate-180" : ""
          }`}
        />
      </button>

      {expanded && steps.length > 0 && (
        <div className="mt-3 space-y-1.5 pl-5">
          {steps.map((step, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
              <span className="mt-0.5 h-4 w-4 shrink-0 rounded-full bg-primary/10 text-center text-[10px] font-semibold leading-4 text-primary">
                {i + 1}
              </span>
              <span className="leading-relaxed">{step}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
