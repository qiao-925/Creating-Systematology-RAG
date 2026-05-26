"use client";

import { useState } from "react";
import { CLDCanvasSVG } from "./cld-canvas-svg";
import { CLDCanvasReactFlow } from "./cld-canvas-reactflow";
import { CLDCanvasD3 } from "./cld-canvas-d3";
import type { CLDData } from "./cld-canvas-types";

type CanvasMode = "svg" | "reactflow" | "d3";

interface Props {
  data: CLDData;
}

const modes: { key: CanvasMode; label: string }[] = [
  { key: "svg", label: "SVG" },
  { key: "reactflow", label: "React Flow" },
  { key: "d3", label: "D3.js" },
];

export function CLDCanvasSwitcher({ data }: Props) {
  const [mode, setMode] = useState<CanvasMode>("svg");

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="h-9 bg-card border-b border-border flex items-center px-4 gap-1 text-xs text-muted-foreground">
        {modes.map((m) => (
          <button
            key={m.key}
            onClick={() => setMode(m.key)}
            className={`px-2.5 py-1 rounded font-medium transition-colors ${
              mode === m.key
                ? "bg-accent text-accent-foreground"
                : "hover:text-foreground hover:bg-accent/50"
            }`}
          >
            {m.label}
          </button>
        ))}
        <div className="flex-1" />
        <span className="text-muted-foreground/60">
          {data.nodes.length} 节点 · {data.edges.length} 边
        </span>
      </div>

      {/* Canvas area */}
      <div className="flex-1 overflow-hidden">
        {mode === "svg" && <CLDCanvasSVG data={data} />}
        {mode === "reactflow" && <CLDCanvasReactFlow data={data} />}
        {mode === "d3" && <CLDCanvasD3 data={data} />}
      </div>
    </div>
  );
}
