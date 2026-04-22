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
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { useConfigStore } from "@/stores/config-store";
import { api } from "@/lib/api";

const PRESETS: { id: string; label: string; desc: string }[] = [
  { id: "precise", label: "Precise", desc: "T=0.1, 低创造性" },
  { id: "balanced", label: "Balanced", desc: "T=0.7, 默认" },
  { id: "creative", label: "Creative", desc: "T=1.0, 高创造性" },
];

export function ModelTab() {
  const config = useConfigStore((s) => s.config);
  const models = useConfigStore((s) => s.models);
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

  const currentModel = models.find((m) => m.id === config.selected_model);

  return (
    <>
      {/* Model selection */}
      <div className="space-y-2">
        <Label className="text-xs text-muted-foreground">Model</Label>
        <Select
          value={config.selected_model}
          onValueChange={(v) => update({ selected_model: v })}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select model" />
          </SelectTrigger>
          <SelectContent>
            {models.map((m) => (
              <SelectItem key={m.id} value={m.id}>
                <span className="flex items-center gap-2">
                  {m.name}
                  {m.supports_reasoning && (
                    <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                      Reasoning
                    </Badge>
                  )}
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Preset */}
      <div className="space-y-2">
        <Label className="text-xs text-muted-foreground">Preset</Label>
        <div className="grid grid-cols-3 gap-2">
          {PRESETS.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => update({ llm_preset: p.id })}
              className={`rounded-lg border px-3 py-2 text-left transition-all ${
                config.llm_preset === p.id
                  ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-500"
                  : "border-border/50 hover:border-border"
              }`}
            >
              <p className="text-sm font-medium">{p.label}</p>
              <p className="text-[11px] text-muted-foreground">{p.desc}</p>
            </button>
          ))}
        </div>
        {currentModel?.supports_reasoning && (
          <p className="text-[11px] text-amber-500/80">
            Reasoning models ignore temperature settings
          </p>
        )}
      </div>

      {/* Agentic RAG */}
      <div className="flex items-center justify-between">
        <div>
          <Label className="text-sm">Agentic RAG</Label>
          <p className="text-[11px] text-muted-foreground">Multi-step query decomposition</p>
        </div>
        <Switch
          checked={config.use_agentic_rag}
          onCheckedChange={(v) => update({ use_agentic_rag: v })}
        />
      </div>

      {/* Research mode */}
      <div className="flex items-center justify-between">
        <div>
          <Label className="text-sm">Research Mode</Label>
          <p className="text-[11px] text-muted-foreground">Structured deep research output</p>
        </div>
        <Switch
          checked={config.research_mode}
          onCheckedChange={(v) => update({ research_mode: v })}
        />
      </div>
    </>
  );
}
