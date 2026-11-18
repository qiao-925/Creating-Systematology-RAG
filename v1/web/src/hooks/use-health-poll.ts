"use client";

import { useEffect } from "react";
import { api } from "@/lib/api";
import { useConfigStore } from "@/stores/config-store";

export function useHealthPoll(intervalMs = 3000) {
  const { health, setHealth, setConfig, setModels } = useConfigStore();

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      try {
        const h = await api.health();
        if (cancelled) return;
        setHealth(h);

        if (h.status === "ready") {
          const [cfg, models] = await Promise.all([
            api.getConfig(),
            api.getModels(),
          ]);
          if (!cancelled) {
            setConfig(cfg);
            setModels(models);
          }
        }
      } catch {
        if (!cancelled) setHealth({ status: "error", message: "API unreachable" });
      }
    };

    poll();

    if (health.status !== "ready") {
      const timer = setInterval(poll, intervalMs);
      return () => {
        cancelled = true;
        clearInterval(timer);
      };
    }

    return () => { cancelled = true; };
  }, [health.status, intervalMs, setHealth, setConfig, setModels]);
}
