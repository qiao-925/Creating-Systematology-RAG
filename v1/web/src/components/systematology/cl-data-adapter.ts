import type { SystematologyNode, SystematologyEdge, SystematologyLeveragePoint } from "@/types";
import type { CLDData, CLDNode, CLDEdge } from "./cld-canvas-types";

// --- Leverage Point Adapter ---

interface LeveragePoint {
  rank: number;
  variable: string;
  impact: number;
  uncertainty: [number, number];
}

interface RawLeveragePoint {
  node?: string;
  node_id?: string;
  node_label?: string;
  impact_score: number;
  confidence: number | string;
  rank?: number;
  affected_nodes?: string[];
}

export function adaptLeveragePoints(
  apiPoints: (SystematologyLeveragePoint | RawLeveragePoint)[],
): LeveragePoint[] {
  return apiPoints
    .map((p, i) => {
      const variable =
        ("node_label" in p ? p.node_label : undefined) ??
        ("node" in p ? (p as RawLeveragePoint).node : undefined) ??
        ("node_id" in p ? p.node_id : undefined) ??
        "unknown";
      const impact = p.impact_score;
      const confidence = typeof p.confidence === "number" ? p.confidence : 0.5;
      return {
        rank: ("rank" in p ? p.rank : undefined) ?? i + 1,
        variable,
        impact,
        uncertainty: [
          Math.max(0, impact - (1 - confidence) * 0.3),
          Math.min(1, impact + (1 - confidence) * 0.3),
        ] as [number, number],
      };
    })
    .sort((a, b) => a.rank - b.rank);
}

// --- CLD Canvas Adapter ---

const RELATION_TO_POLARITY: Record<string, "+" | "-"> = {
  influences: "+",
  causes: "+",
  enables: "+",
  inhibits: "-",
  supports: "+",
  requires: "+",
};

// Match SVG canvas constants
const CHAR_W = 16;
const NODE_PAD_X = 40;
const NODE_H = 36;
const MIN_NODE_W = 80;

function estimatedNodeW(label: string): number {
  return Math.max(MIN_NODE_W, label.length * CHAR_W + NODE_PAD_X);
}

function layoutNodes(nodes: SystematologyNode[]): CLDNode[] {
  const n = nodes.length;
  if (n === 0) return [];

  // Compute radius large enough so nodes don't overlap
  // Max node angular width ≈ max(w) / radius, need spacing between adjacent nodes
  const maxW = Math.max(...nodes.map((nd) => estimatedNodeW(nd.label)));
  const minSpacing = 20; // px between adjacent node edges on circle
  // Circular arc per node: 2*PI / n, need: radius * angle >= maxW + minSpacing
  const radius = Math.max(140, n * 28, (n * (maxW + minSpacing)) / (2 * Math.PI));
  const cx = Math.max(radius + 60, 440);
  const cy = Math.max(radius + 60, 320);

  return nodes.map((node, i) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2;
    return {
      id: node.id,
      label: node.label,
      x: Math.round(cx + radius * Math.cos(angle)),
      y: Math.round(cy + radius * Math.sin(angle)),
    };
  });
}

export function adaptCLDData(
  nodes: SystematologyNode[],
  edges: SystematologyEdge[],
): CLDData {
  const canvasNodes = layoutNodes(nodes);
  const canvasEdges: CLDEdge[] = edges.map((e) => ({
    source: e.source,
    target: e.target,
    polarity: RELATION_TO_POLARITY[e.relation] ?? "+",
    label: e.relation,
  }));

  return { nodes: canvasNodes, edges: canvasEdges };
}
