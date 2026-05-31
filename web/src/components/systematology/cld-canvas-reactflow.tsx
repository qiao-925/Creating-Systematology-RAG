"use client";

import { useMemo, useCallback, useState, useEffect } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  type OnNodesChange,
  type OnEdgesChange,
  applyNodeChanges,
  applyEdgeChanges,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { CLDData } from "./cld-canvas-types";

interface Props {
  data: CLDData;
}

const NODE_W = 140;
const NODE_H = 36;

function toFlowData(data: CLDData) {
  const nodes: Node[] = data.nodes.map((n) => ({
    id: n.id,
    position: { x: n.x, y: n.y },
    data: { label: n.label },
    style: {
      width: NODE_W,
      height: NODE_H,
      borderRadius: 8,
      border: "1px solid hsl(var(--border))",
      background: "hsl(var(--card))",
      color: "hsl(var(--foreground))",
      fontSize: 12,
      fontWeight: 500,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    },
  }));

  const edges: Edge[] = data.edges.map((e, i) => ({
    id: `e-${i}`,
    source: e.source,
    target: e.target,
    type: "default",
    animated: false,
    style: {
      stroke:
        e.polarity === "+"
          ? "hsl(var(--primary))"
          : "hsl(var(--negative))",
      strokeWidth: 1.5,
      strokeDasharray: e.polarity === "-" ? "6 3" : undefined,
    },
    label: e.polarity === "+" ? "+" : "−",
    labelStyle: {
      fill:
        e.polarity === "+"
          ? "hsl(var(--primary))"
          : "hsl(var(--negative))",
      fontWeight: 600,
      fontSize: 11,
      fontFamily: "monospace",
    },
  }));

  return { nodes, edges };
}

export function CLDCanvasReactFlow({ data }: Props) {
  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => toFlowData(data),
    [data],
  );
  const [nodes, setNodes] = useState(initialNodes);
  const [edges, setEdges] = useState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges]);

  const onNodesChange: OnNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    [],
  );
  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    [],
  );

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background color="hsl(var(--border))" gap={24} size={1} />
        <Controls
          className="!bg-card !border-border !rounded-lg !shadow-sm"
          showInteractive={false}
        />
      </ReactFlow>
    </div>
  );
}
