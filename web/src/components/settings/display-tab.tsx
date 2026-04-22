"use client";

import { useCallback } from "react";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useConfigStore } from "@/stores/config-store";
import { api } from "@/lib/api";

export function DisplayTab() {
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
      {/* Show reasoning */}
      <div className="flex items-center justify-between">
        <div>
          <Label className="text-sm">Show Reasoning</Label>
          <p className="text-[11px] text-muted-foreground">Display model reasoning chain</p>
        </div>
        <Switch
          checked={config.show_reasoning}
          onCheckedChange={(v) => update({ show_reasoning: v })}
        />
      </div>
    </>
  );
}
