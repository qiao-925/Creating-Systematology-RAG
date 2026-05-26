"use client";

import { TrendingUp } from "lucide-react";

interface LeveragePoint {
  rank: number;
  variable: string;
  impact: number;
  uncertainty: [number, number];
}

interface Props {
  points?: LeveragePoint[];
}

const defaultPoints: LeveragePoint[] = [
  { rank: 1, variable: "碳定价机制强度", impact: 0.87, uncertainty: [0.78, 0.95] },
  { rank: 2, variable: "研发投入占比", impact: 0.72, uncertainty: [0.61, 0.83] },
  { rank: 3, variable: "电网接入能力", impact: 0.58, uncertainty: [0.42, 0.74] },
  { rank: 4, variable: "化石能源退出速度", impact: 0.45, uncertainty: [0.30, 0.60] },
  { rank: 5, variable: "公众环保意识", impact: 0.31, uncertainty: [0.15, 0.47] },
];

function impactColor(value: number): string {
  if (value >= 0.7) return "text-negative";
  if (value >= 0.5) return "text-primary";
  return "text-muted-foreground";
}

export function LeverageTable({ points = defaultPoints }: Props) {
  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2.5">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <TrendingUp className="h-4 w-4" />
          <span className="font-medium">杠杆点排序</span>
        </div>
        <span className="text-xs text-muted-foreground/60">按影响力排序</span>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-t border-border">
            <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">
              #
            </th>
            <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">
              变量
            </th>
            <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">
              影响力
            </th>
            <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">
              不确定性区间
            </th>
          </tr>
        </thead>
        <tbody>
          {points.map((p) => (
            <tr key={p.rank} className="border-t border-border last:border-b-0">
              <td className="px-4 py-2 font-mono text-muted-foreground">
                {p.rank}
              </td>
              <td className="px-4 py-2 text-foreground">{p.variable}</td>
              <td className={`px-4 py-2 font-mono font-medium ${impactColor(p.impact)}`}>
                {p.impact.toFixed(2)}
              </td>
              <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                [{p.uncertainty[0].toFixed(2)}, {p.uncertainty[1].toFixed(2)}]
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
