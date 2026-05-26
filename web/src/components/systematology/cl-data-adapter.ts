import type { SystematologyNode, SystematologyEdge, SystematologyLeveragePoint } from "@/types";
import type { CLDData, CLDNode, CLDEdge } from "./cld-canvas-types";

// --- Leverage Point Adapter ---

interface LeveragePoint {
  rank: number;
  variable: string;
  impact: number;
  uncertainty: [number, number];
}

// Backend may send either SystematologyLeveragePoint or raw NodeImpact shape
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

function layoutNodes(nodes: SystematologyNode[]): CLDNode[] {
  const n = nodes.length;
  if (n === 0) return [];

  // Circular layout with radius proportional to node count
  const radius = Math.max(120, n * 25);
  const cx = 400;
  const cy = 280;

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
