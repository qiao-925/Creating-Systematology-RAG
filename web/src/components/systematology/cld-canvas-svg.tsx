"use client";

import type { CLDData, CLDNode, CLDEdge } from "./cld-canvas-types";

interface Props {
  data: CLDData;
}

const NODE_W = 140;
const NODE_H = 36;
const SVG_W = 800;
const SVG_H = 560;

function nodeCenter(node: CLDNode) {
  return { x: node.x + NODE_W / 2, y: node.y + NODE_H / 2 };
}

function edgePath(edge: CLDEdge, nodes: CLDNode[]): string {
  const from = nodes.find((n) => n.id === edge.source);
  const to = nodes.find((n) => n.id === edge.target);
  if (!from || !to) return "";

  const fc = nodeCenter(from);
  const tc = nodeCenter(to);

  // Offset start/end to node border
  const dx = tc.x - fc.x;
  const dy = tc.y - fc.y;
  const angle = Math.atan2(dy, dx);
  const sx = fc.x + Math.cos(angle) * (NODE_W / 2 + 4);
  const sy = fc.y + Math.sin(angle) * (NODE_H / 2 + 4);
  const ex = tc.x - Math.cos(angle) * (NODE_W / 2 + 8);
  const ey = tc.y - Math.sin(angle) * (NODE_H / 2 + 8);

  // Bezier curve
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
  const dx = tc.x - fc.x;
  const dy = tc.y - fc.y;
  const angle = Math.atan2(dy, dx);
  const sx = fc.x + Math.cos(angle) * (NODE_W / 2 + 4);
  const sy = fc.y + Math.sin(angle) * (NODE_H / 2 + 4);
  const ex = tc.x - Math.cos(angle) * (NODE_W / 2 + 8);
  const ey = tc.y - Math.sin(angle) * (NODE_H / 2 + 8);

  const mx = (sx + ex) / 2;
  const my = (sy + ey) / 2;
  const cx = mx + (ey - sy) * 0.2;
  const cy = my - (ex - sx) * 0.2;

  // Point at t=0.5 on quadratic bezier
  return {
    x: 0.25 * sx + 0.5 * cx + 0.25 * ex,
    y: 0.25 * sy + 0.5 * cy + 0.25 * ey,
  };
}

export function CLDCanvasSVG({ data }: Props) {
  const { nodes, edges } = data;

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
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        className="w-full h-full"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <marker
            id="arrow-pos"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" className="fill-primary" />
          </marker>
          <marker
            id="arrow-neg"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" className="fill-negative" />
          </marker>
        </defs>

        {/* Edges */}
        {edges.map((edge, i) => {
          const d = edgePath(edge, nodes);
          const mid = edgeMidpoint(edge, nodes);
          if (!d) return null;
          return (
            <g key={i}>
              <path
                d={d}
                fill="none"
                strokeWidth={1.5}
                className={
                  edge.polarity === "+"
                    ? "stroke-primary"
                    : "stroke-negative [stroke-dasharray:6_3]"
                }
                markerEnd={
                  edge.polarity === "+" ? "url(#arrow-pos)" : "url(#arrow-neg)"
                }
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
        {nodes.map((node) => (
          <g key={node.id} className="cursor-pointer transition-opacity hover:opacity-80">
            <rect
              x={node.x}
              y={node.y}
              width={NODE_W}
              height={NODE_H}
              rx={8}
              className="fill-card stroke-border stroke-1"
            />
            <text
              x={node.x + NODE_W / 2}
              y={node.y + NODE_H / 2 + 1}
              textAnchor="middle"
              dominantBaseline="central"
              className="fill-foreground text-xs font-medium"
            >
              {node.label}
            </text>
          </g>
        ))}
      </svg>

      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-card/90 border border-border rounded-lg px-4 py-3 text-xs text-muted-foreground flex flex-col gap-1.5">
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
