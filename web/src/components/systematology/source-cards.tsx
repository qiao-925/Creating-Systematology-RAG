"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";

type SourceTier = "T1" | "T2" | "T3";

interface Source {
  tier: SourceTier;
  title: string;
  meta: string;
}

interface Props {
  sources?: Source[];
}

const tierStyles: Record<SourceTier, string> = {
  T1: "bg-primary/15 text-primary border-primary/20",
  T2: "bg-positive/15 text-positive border-positive/20",
  T3: "bg-muted text-muted-foreground border-border",
};

const defaultSources: Source[] = [
  {
    tier: "T1",
    title: "Renewable Energy Subsidies and Carbon Emission Reduction: A Causal Analysis",
    meta: "Nature Energy · 2024 · 被引 89 次",
  },
  {
    tier: "T1",
    title: "The Impact of Feed-in Tariffs on Innovation in Renewable Energy Technologies",
    meta: "Energy Policy · 2023 · 被引 67 次",
  },
  {
    tier: "T2",
    title: "EU Emissions Trading System: Evidence on Carbon Price and Innovation",
    meta: "European Commission · 2024",
  },
  {
    tier: "T3",
    title: "Global Renewable Energy Investment Trends Report",
    meta: "IRENA · 2024",
  },
];

export function SourceCards({ sources = defaultSources }: Props) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      <button
        className="w-full flex items-center justify-between px-4 py-2.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="font-medium">来源 ({sources.length})</span>
        {expanded ? (
          <ChevronUp className="h-3.5 w-3.5" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5" />
        )}
      </button>
      {expanded && (
        <div className="px-4 pb-3 flex flex-col">
          {sources.map((source, i) => (
            <div
              key={i}
              className="flex items-start gap-2.5 py-2 border-t border-border first:border-t-0"
            >
              <Badge
                variant="outline"
                className={`text-[10px] font-semibold shrink-0 ${tierStyles[source.tier]}`}
              >
                {source.tier}
              </Badge>
              <div className="min-w-0">
                <div className="text-sm text-foreground truncate">
                  {source.title}
                </div>
                <div className="text-xs text-muted-foreground mt-0.5">
                  {source.meta}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
