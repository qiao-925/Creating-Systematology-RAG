"use client";

import { useCallback } from "react";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { useConfigStore } from "@/stores/config-store";
import { api } from "@/lib/api";

const STRATEGIES = [
  { id: "vector", label: "Vector", desc: "Semantic similarity" },
  { id: "keyword", label: "Keyword", desc: "BM25 keyword match" },
  { id: "hybrid", label: "Hybrid", desc: "Vector + keyword fusion" },
];

export function RetrievalTab() {
  const config = useConfigStore((s) => s.config);
  const setConfig = useConfigStore((s) => s.setConfig);

  const update = useCallback(
    async (partial: Record<string, unknown>) => {
      setConfig(partial);
      try {
        const updated = await api.updateConfig(partial);
        setConfig(updated);
      } catch {
        /* rollback handled by next poll */
      }
    },
    [setConfig],
  );

  return (
    <>
      {/* Retrieval strategy */}
      <div className="space-y-2">
        <Label className="text-xs text-muted-foreground">Strategy</Label>
        <Select
          value={config.retrieval_strategy}
          onValueChange={(v) => update({ retrieval_strategy: v })}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STRATEGIES.map((s) => (
              <SelectItem key={s.id} value={s.id}>
                <span className="flex items-center gap-2">
                  {s.label}
                  <span className="text-xs text-muted-foreground">— {s.desc}</span>
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Top-K */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="text-xs text-muted-foreground">Top-K Results</Label>
          <span className="text-xs font-mono text-foreground/70">{config.similarity_top_k}</span>
        </div>
        <Slider
          value={[config.similarity_top_k]}
          onValueChange={(v) => update({ similarity_top_k: (v as number[])[0] })}
          min={1}
          max={20}
          step={1}
        />
      </div>

      {/* Similarity threshold */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="text-xs text-muted-foreground">Similarity Threshold</Label>
          <span className="text-xs font-mono text-foreground/70">{config.similarity_threshold.toFixed(2)}</span>
        </div>
        <Slider
          value={[config.similarity_threshold]}
          onValueChange={(v) => update({ similarity_threshold: Math.round((v as number[])[0] * 100) / 100 })}
          min={0}
          max={1}
          step={0.05}
        />
      </div>

      {/* Rerank */}
      <div className="flex items-center justify-between">
        <div>
          <Label className="text-sm">Rerank</Label>
          <p className="text-[11px] text-muted-foreground">Cross-encoder re-ranking</p>
        </div>
        <Switch
          checked={config.enable_rerank}
          onCheckedChange={(v) => update({ enable_rerank: v })}
        />
      </div>
    </>
  );
}
