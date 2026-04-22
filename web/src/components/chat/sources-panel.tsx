"use client";

import { FileText } from "lucide-react";
import type { Source } from "@/types";

interface Props {
  sources: Source[];
}

export function SourcesPanel({ sources }: Props) {
  if (!sources.length) return null;

  return (
    <div className="mt-3 space-y-1.5">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Sources
      </p>
      <div className="grid gap-1.5">
        {sources.map((s, i) => (
          <div
            key={i}
            id={`source-${i + 1}`}
            className="flex items-start gap-2 rounded-md border border-border/50 bg-muted/30 px-3 py-2 text-sm transition-colors hover:bg-muted/50"
          >
            <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded bg-emerald-500/10 text-xs font-medium text-emerald-400">
              {i + 1}
            </span>
            <div className="min-w-0 flex-1">
              <p className="flex items-center gap-1.5 font-medium truncate">
                <FileText className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                {s.title || s.file_path || `Source ${i + 1}`}
              </p>
              {s.content && (
                <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">
                  {s.content}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
