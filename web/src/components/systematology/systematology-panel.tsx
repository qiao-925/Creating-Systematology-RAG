"use client";

import { useState, useCallback } from "react";
import { Loader2, AlertCircle, Network, BarChart3, TrendingUp } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import type {
  SystematologyResponse,
  SystematologyReport,
  SystematologyFailureReport,
  SystematologyNode,
  SystematologyEdge,
  SystematologyLeveragePoint,
} from "@/types";

function isFailureReport(
  report: SystematologyReport | SystematologyFailureReport,
): report is SystematologyFailureReport {
  return "stage" in report && "reason" in report;
}

function CLDGraph({ nodes, edges }: { nodes: SystematologyNode[]; edges: SystematologyEdge[] }) {
  return (
    <div className="rounded-lg border bg-muted/30 p-4">
      <div className="flex items-center gap-2 mb-3">
        <Network className="h-4 w-4 text-emerald-500" />
        <h3 className="text-sm font-semibold">Causal Loop Diagram</h3>
        <Badge variant="secondary">{nodes.length} nodes</Badge>
        <Badge variant="secondary">{edges.length} edges</Badge>
      </div>
      <div className="space-y-2">
        <div>
          <p className="text-xs text-muted-foreground mb-1">Nodes</p>
          <div className="flex flex-wrap gap-1.5">
            {nodes.map((n) => (
              <Badge key={n.id} variant="outline" className="text-xs">
                {n.label}
              </Badge>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs text-muted-foreground mb-1">Causal Links</p>
          <div className="space-y-1">
            {edges.map((e, i) => (
              <div key={i} className="text-xs font-mono text-muted-foreground">
                {e.source} <span className="text-emerald-500">{e.relation}</span>{" "}
                {e.target}
                {e.weight !== undefined && (
                  <span className="ml-1 text-muted-foreground/60">
                    ({e.weight.toFixed(2)})
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function LeverageRanking({ points }: { points: SystematologyLeveragePoint[] }) {
  const sorted = [...points].sort((a, b) => a.rank - b.rank);
  return (
    <div className="rounded-lg border bg-muted/30 p-4">
      <div className="flex items-center gap-2 mb-3">
        <TrendingUp className="h-4 w-4 text-blue-500" />
        <h3 className="text-sm font-semibold">Leverage Points</h3>
      </div>
      <div className="space-y-2">
        {sorted.map((p) => (
          <div key={p.node_id} className="flex items-center gap-3">
            <span className="text-xs font-mono text-muted-foreground w-6 text-right">
              #{p.rank}
            </span>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{p.node_label}</span>
                <Badge variant="outline" className="text-xs">
                  {(p.impact_score * 100).toFixed(1)}%
                </Badge>
              </div>
              <div className="mt-1 h-1.5 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full rounded-full bg-emerald-500"
                  style={{ width: `${Math.min(p.impact_score * 100, 100)}%` }}
                />
              </div>
            </div>
            <span className="text-xs text-muted-foreground">
              conf: {(p.confidence * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function SystematologyPanel() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SystematologyResponse | null>(null);

  const handleAnalyze = useCallback(async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.systematologyAnalyze(question.trim());
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }, [question]);

  const report = result?.report;
  const isFailure = report ? isFailureReport(report) : false;

  return (
    <div className="space-y-6">
      {/* Input */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Systematology Analysis</h2>
        <p className="text-sm text-muted-foreground">
          Enter a research question to run causal loop diagram analysis with FCM
          simulation and leverage point detection.
        </p>
        <div className="flex gap-2">
          <Input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. How do fiscal subsidies affect housing affordability?"
            disabled={loading}
            onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
          />
          <Button onClick={handleAnalyze} disabled={loading || !question.trim()}>
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "Analyze"
            )}
          </Button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Failure report */}
      {result && isFailure && (
        <div className="rounded-lg border border-amber-500/50 bg-amber-500/10 p-4 space-y-2">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-amber-500" />
            <span className="text-sm font-semibold text-amber-600">
              Analysis Failed
            </span>
          </div>
          <p className="text-sm text-muted-foreground">
            Stage: {(report as SystematologyFailureReport).stage}
          </p>
          <p className="text-sm">{(report as SystematologyFailureReport).reason}</p>
        </div>
      )}

      {/* Success report */}
      {result && !isFailure && report && (
        <div className="space-y-4">
          {/* CLD Visualization */}
          {(report as SystematologyReport).cld_visualization?.nodes &&
            (report as SystematologyReport).cld_visualization!.nodes!.length > 0 && (
              <CLDGraph
                nodes={(report as SystematologyReport).cld_visualization!.nodes!}
                edges={(report as SystematologyReport).cld_visualization!.edges ?? []}
              />
            )}

          {/* Insights */}
          {(report as SystematologyReport).synthesized_insights && (
            <div className="rounded-lg border bg-muted/30 p-4">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="h-4 w-4 text-purple-500" />
                <h3 className="text-sm font-semibold">Synthesized Insights</h3>
              </div>
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                {(report as SystematologyReport).synthesized_insights}
              </p>
            </div>
          )}

          {/* Leverage Ranking */}
          {(report as SystematologyReport).leverage_ranking &&
            (report as SystematologyReport).leverage_ranking!.length > 0 && (
              <LeverageRanking
                points={(report as SystematologyReport).leverage_ranking!}
              />
            )}

          {/* Scenario Comparison */}
          {(report as SystematologyReport).scenario_comparison && (
            <div className="rounded-lg border bg-muted/30 p-4">
              <h3 className="text-sm font-semibold mb-2">Scenario Comparison</h3>
              <pre className="text-xs text-muted-foreground overflow-auto max-h-48">
                {JSON.stringify(
                  (report as SystematologyReport).scenario_comparison,
                  null,
                  2,
                )}
              </pre>
            </div>
          )}

          {/* Raw fallback */}
          {(report as SystematologyReport).cld_visualization?.raw_response && (
            <details className="rounded-lg border bg-muted/30 p-4">
              <summary className="text-sm font-semibold cursor-pointer">
                Raw Response
              </summary>
              <pre className="mt-2 text-xs text-muted-foreground whitespace-pre-wrap max-h-64 overflow-auto">
                {(report as SystematologyReport).cld_visualization!.raw_response}
              </pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
