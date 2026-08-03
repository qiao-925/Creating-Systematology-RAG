"use client";

import { useState, useEffect, useRef } from "react";
import type { CLDData, CLDNode, CLDEdge } from "./cld-canvas-types";

interface Props {
  data: CLDData;
  /** If true, nodes and edges appear sequentially with animation */
  animate?: boolean;
}

const CHAR_W = 16;   // approximate width per Chinese char in text-xs
const NODE_PAD_X = 40; // horizontal padding inside node
const NODE_H = 36;
const NODE_APPEAR_INTERVAL = 350;
const EDGE_APPEAR_INTERVAL = 200;

/** Compute node width from its label length */
function nodeW(node: CLDNode): number {
  return Math.max(80, node.label.length * CHAR_W + NODE_PAD_X);
}

function nodeCenter(node: CLDNode) {
  const w = nodeW(node);
  return { x: node.x + w / 2, y: node.y + NODE_H / 2 };
}

function edgePath(edge: CLDEdge, nodes: CLDNode[]): string {
  const from = nodes.find((n) => n.id === edge.source);
  const to = nodes.find((n) => n.id === edge.target);
  if (!from || !to) return "";

  const fc = nodeCenter(from);
  const tc = nodeCenter(to);
  const fromW = nodeW(from);
  const toW = nodeW(to);

  const dx = tc.x - fc.x;
  const dy = tc.y - fc.y;
  const angle = Math.atan2(dy, dx);
  const sx = fc.x + Math.cos(angle) * (fromW / 2 + 4);
  const sy = fc.y + Math.sin(angle) * (NODE_H / 2 + 4);
  const ex = tc.x - Math.cos(angle) * (toW / 2 + 8);
  const ey = tc.y - Math.sin(angle) * (NODE_H / 2 + 8);

  const mx = (sx + ex) / 2;
  const my = (sy + ey) / 2;
  const cx = mx + (ey - sy) * 0.2;
  const cy = my - (ex - sx) * 0.2;

  return `M ${sx},${sy} Q ${cx},${cy} ${ex},${ey}`;
}

function edgeMidpoint(edge: CLDEdge, nodes: CLDNode[]): { x: number; y: number } {
  const from = nodes.find((n) => n.id === edge.source);
  const to = nodes.find((n) => n.id === edge.target);
  if (!from || !to) return { x: 0, y: 0 };

  const fc = nodeCenter(from);
  const tc = nodeCenter(to);
  const fromW = nodeW(from);
  const toW = nodeW(to);
  const dx = tc.x - fc.x;
  const dy = tc.y - fc.y;
  const angle = Math.atan2(dy, dx);
  const sx = fc.x + Math.cos(angle) * (fromW / 2 + 4);
  const sy = fc.y + Math.sin(angle) * (NODE_H / 2 + 4);
  const ex = tc.x - Math.cos(angle) * (toW / 2 + 8);
  const ey = tc.y - Math.sin(angle) * (NODE_H / 2 + 8);

  const mx = (sx + ex) / 2;
  const my = (sy + ey) / 2;
  const cx = mx + (ey - sy) * 0.2;
  const cy = my - (ex - sx) * 0.2;

  return {
    x: 0.25 * sx + 0.5 * cx + 0.25 * ex,
    y: 0.25 * sy + 0.5 * cy + 0.25 * ey,
  };
}

/** Compute viewBox width needed to contain all nodes */
function computeViewBox(nodes: CLDNode[]): { w: number; h: number } {
  if (nodes.length === 0) return { w: 800, h: 560 };
  let maxX = 0, maxY = 0, minX = Infinity, minY = Infinity;
  for (const n of nodes) {
    const w = nodeW(n);
    maxX = Math.max(maxX, n.x + w);
    maxY = Math.max(maxY, n.y + NODE_H);
    minX = Math.min(minX, n.x);
    minY = Math.min(minY, n.y);
  }
  const pad = 40;
  return {
    w: Math.max(800, maxX - minX + pad * 2),
    h: Math.max(560, maxY - minY + pad * 2),
  };
}

export function CLDCanvasSVG({ data, animate = false }: Props) {
  const { nodes, edges } = data;
  const [visibleNodes, setVisibleNodes] = useState<number>(animate ? 0 : nodes.length);
  const [visibleEdges, setVisibleEdges] = useState<number>(animate ? 0 : edges.length);
  const [drawProgress, setDrawProgress] = useState(0);
  const prevDataRef = useRef(data);

  const viewBox = computeViewBox(nodes);

  useEffect(() => {
    if (!animate) {
      setVisibleNodes(nodes.length);
      setVisibleEdges(edges.length);
      setDrawProgress(100);
      return;
    }

    setVisibleNodes(0);
    setVisibleEdges(0);
    setDrawProgress(0);

    const nodeTimers: ReturnType<typeof setTimeout>[] = [];
    nodes.forEach((_, i) => {
      const t = setTimeout(() => setVisibleNodes(i + 1), 400 + i * NODE_APPEAR_INTERVAL);
      nodeTimers.push(t);
    });

    const totalNodeTime = 400 + nodes.length * NODE_APPEAR_INTERVAL;
    const edgeStartTimer = setTimeout(() => {
      edges.forEach((_, i) => {
        const t = setTimeout(() => setVisibleEdges(i + 1), i * EDGE_APPEAR_INTERVAL);
        nodeTimers.push(t);
      });
    }, totalNodeTime + 300);

    const drawTimer = setTimeout(() => {
      setDrawProgress(100);
    }, totalNodeTime + 300 + edges.length * EDGE_APPEAR_INTERVAL);

    return () => {
      nodeTimers.forEach(clearTimeout);
      clearTimeout(edgeStartTimer);
      clearTimeout(drawTimer);
    };
  }, [animate, data]);

  const allNodesVisible = visibleNodes >= nodes.length;

  return (
    <div className="w-full h-full relative overflow-hidden">
      {/* Grid dot pattern */}
      <div
        className="absolute inset-0 opacity-30 pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(circle, hsl(var(--border)) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />

      <svg
        viewBox={`0 0 ${viewBox.w} ${viewBox.h}`}
        className="w-full h-full"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <marker id="arrow-pos" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" className="fill-primary" />
          </marker>
          <marker id="arrow-neg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" className="fill-negative" />
          </marker>
        </defs>

        {/* Edges */}
        {edges.map((edge, i) => {
          if (i >= visibleEdges) return null;
          const d = edgePath(edge, nodes);
          const mid = edgeMidpoint(edge, nodes);
          if (!d) return null;

          return (
            <g key={i} className="animate-in fade-in duration-300">
              <path
                d={d}
                fill="none"
                strokeWidth={1.5}
                className={
                  edge.polarity === "+"
                    ? "stroke-primary"
                    : "stroke-negative [stroke-dasharray:6_3]"
                }
                markerEnd={edge.polarity === "+" ? "url(#arrow-pos)" : "url(#arrow-neg)"}
              />
              <text
                x={mid.x}
                y={mid.y - 6}
                textAnchor="middle"
                className={`text-[11px] font-mono font-semibold ${
                  edge.polarity === "+" ? "fill-primary" : "fill-negative"
                }`}
              >
                {edge.polarity === "+" ? "+" : "−"}
              </text>
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map((node, i) => {
          if (i >= visibleNodes) return null;
          const isNew = i === visibleNodes - 1 && !allNodesVisible;
          const w = nodeW(node);
          return (
            <g
              key={node.id}
              className="cursor-pointer"
              style={{
                opacity: isNew ? undefined : 1,
                animation: isNew ? "node-appear 0.4s ease-out both" : undefined,
              }}
            >
              <rect
                x={node.x}
                y={node.y}
                width={w}
                height={NODE_H}
                rx={8}
                className="fill-card stroke-border stroke-1"
              />
              <text
                x={node.x + w / 2}
                y={node.y + NODE_H / 2 + 1}
                textAnchor="middle"
                dominantBaseline="central"
                className="fill-foreground text-xs font-medium"
              >
                {node.label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Progress indicator */}
      {animate && visibleNodes < nodes.length && (
        <div className="absolute top-4 left-4 bg-card/90 border border-border rounded-lg px-3 py-1.5 text-xs text-muted-foreground flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
          <span>正在绘制因果图... ({visibleNodes}/{nodes.length} 节点)</span>
        </div>
      )}

      {/* Legend */}
      <div
        className={`absolute bottom-4 right-4 bg-card/90 border border-border rounded-lg px-4 py-3 text-xs text-muted-foreground flex flex-col gap-1.5 transition-opacity duration-500 ${
          allNodesVisible ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
      >
        <div className="flex items-center gap-2">
          <div className="w-6 h-0.5 rounded bg-primary" />
          <span>正极性 (+)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-0 border-t-2 border-dashed border-negative" />
          <span>负极性 (−)</span>
        </div>
      </div>
    </div>
  );
}
