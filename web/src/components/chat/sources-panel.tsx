"use client";

import type { Source } from "@/types";

interface Props {
  sources: Source[];
}

export function SourcesPanel({ sources }: Props) {
  if (!sources.length) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {sources.map((s, i) => (
        <div
          key={i}
          id={`source-${i + 1}`}
          className="flex items-center gap-2 rounded-lg border border-border/50 bg-muted/30 px-3 py-2 text-xs transition-colors hover:border-foreground/20 cursor-pointer max-w-[200px]"
        >
          <span className="flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded bg-primary/10 text-[10px] font-semibold text-primary">
            {i + 1}
          </span>
          <span className="truncate text-muted-foreground">
            {s.title || s.file_path || `Source ${i + 1}`}
          </span>
        </div>
      ))}
    </div>
  );
}
