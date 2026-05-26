"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import * as d3 from "d3";
import type { CLDData, CLDNode } from "./cld-canvas-types";

interface Props {
  data: CLDData;
}

interface SimNode extends CLDNode {
  fx?: number | null;
  fy?: number | null;
}

interface SimEdge {
  source: string | SimNode;
  target: string | SimNode;
  polarity: "+" | "-";
  label?: string;
}

const NODE_W = 140;
const NODE_H = 36;

export function CLDCanvasD3({ data }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const simRef = useRef<d3.Simulation<SimNode, SimEdge> | null>(null);
  const [, setTick] = useState(0);

  const draw = useCallback(() => {
    const svg = svgRef.current;
    if (!svg) return;

    const container = svg.parentElement;
    if (!container) return;
    const width = container.clientWidth;
    const height = container.clientHeight;

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    // Clear previous
    d3.select(svg).selectAll("*").remove();

    const g = d3.select(svg).append("g");

    // Create simulation nodes
    const simNodes: SimNode[] = data.nodes.map((n) => ({
      ...n,
      x: n.x * (width / 800),
      y: n.y * (height / 560),
    }));

    const simEdges: SimEdge[] = data.edges.map((e) => ({
      ...e,
      source: e.source,
      target: e.target,
    }));

    // Force simulation
    const sim = d3
      .forceSimulation<SimNode>(simNodes)
      .force(
        "link",
        d3
          .forceLink<SimNode, SimEdge>(simEdges)
          .id((d) => d.id)
          .distance(120),
      )
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide(NODE_W / 2 + 10))
      .alphaDecay(0.02);

    simRef.current = sim;

    // Arrow markers
    const defs = g.append("defs");
    defs
      .append("marker")
      .attr("id", "d3-arrow-pos")
      .attr("viewBox", "0 0 10 10")
      .attr("refX", 9)
      .attr("refY", 5)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto-start-reverse")
      .append("path")
      .attr("d", "M 0 0 L 10 5 L 0 10 z")
      .attr("fill", "hsl(var(--primary))");

    defs
      .append("marker")
      .attr("id", "d3-arrow-neg")
      .attr("viewBox", "0 0 10 10")
      .attr("refX", 9)
      .attr("refY", 5)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto-start-reverse")
      .append("path")
      .attr("d", "M 0 0 L 10 5 L 0 10 z")
      .attr("fill", "hsl(var(--negative))");

    // Edges
    const edgeGroup = g.append("g");
    const edgeSel = edgeGroup
      .selectAll("line")
      .data(simEdges)
      .join("line")
      .attr("stroke", (d) =>
        d.polarity === "+" ? "hsl(var(--primary))" : "hsl(var(--negative))",
      )
      .attr("stroke-width", 1.5)
      .attr("stroke-dasharray", (d) => (d.polarity === "-" ? "6 3" : "none"))
      .attr("marker-end", (d) =>
        d.polarity === "+" ? "url(#d3-arrow-pos)" : "url(#d3-arrow-neg)",
      );

    // Edge polarity labels
    const edgeLabelSel = edgeGroup
      .selectAll("text")
      .data(simEdges)
      .join("text")
      .attr("text-anchor", "middle")
      .attr("font-size", 11)
      .attr("font-family", "monospace")
      .attr("font-weight", 600)
      .attr("fill", (d) =>
        d.polarity === "+" ? "hsl(var(--primary))" : "hsl(var(--negative))",
      )
      .text((d) => (d.polarity === "+" ? "+" : "−"));

    // Nodes
    const nodeGroup = g.append("g");
    const nodeSel = nodeGroup
      .selectAll("g")
      .data(simNodes)
      .join("g")
      .attr("cursor", "pointer");

    nodeSel
      .call(
        d3
          .drag<SVGGElement, SimNode>()
          .on("start", (event, d) => {
            if (!event.active) sim.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) sim.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }) as any,
      );

    nodeSel
      .append("rect")
      .attr("width", NODE_W)
      .attr("height", NODE_H)
      .attr("rx", 8)
      .attr("fill", "hsl(var(--card))")
      .attr("stroke", "hsl(var(--border))")
      .attr("stroke-width", 1);

    nodeSel
      .append("text")
      .attr("x", NODE_W / 2)
      .attr("y", NODE_H / 2 + 1)
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "central")
      .attr("fill", "hsl(var(--foreground))")
      .attr("font-size", 12)
      .attr("font-weight", 500)
      .text((d) => d.label);

    // Tick
    sim.on("tick", () => {
      edgeSel
        .attr("x1", (d) => (d.source as SimNode).x!)
        .attr("y1", (d) => (d.source as SimNode).y!)
        .attr("x2", (d) => (d.target as SimNode).x!)
        .attr("y2", (d) => (d.target as SimNode).y!);

      edgeLabelSel
        .attr(
          "x",
          (d) => ((d.source as SimNode).x! + (d.target as SimNode).x!) / 2,
        )
        .attr(
          "y",
          (d) => ((d.source as SimNode).y! + (d.target as SimNode).y!) / 2 - 6,
        );

      nodeSel.attr(
        "transform",
        (d) => `translate(${d.x! - NODE_W / 2}, ${d.y! - NODE_H / 2})`,
      );

      setTick((t) => t + 1);
    });
  }, [data]);

  useEffect(() => {
    draw();
    return () => {
      simRef.current?.stop();
    };
  }, [draw]);

  return (
    <div className="w-full h-full relative overflow-hidden">
      <svg ref={svgRef} className="w-full h-full" />
    </div>
  );
}
