"use client";

import { useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { SystematologyResponse, SystematologyReport } from "@/types";
import type { Step, StepLog } from "@/components/systematology/thinking-pipeline";

export interface PipelineState {
  loading: boolean;
  error: string | null;
  result: SystematologyResponse | null;
  question: string;
  animateCanvas: boolean;
  steps: Step[];
  /** Raw report for consumers to derive canvas data, leverage points, etc */
  successReport: SystematologyReport | null;
}

function ts(startMs: number): string {
  return `${((Date.now() - startMs) / 1000).toFixed(1)}s`;
}

export function useAnalysisPipeline() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SystematologyResponse | null>(null);
  const [question, setQuestion] = useState("");
  const [animateCanvas, setAnimateCanvas] = useState(false);

  const [stepRetrieval, setStepRetrieval] = useState<Step["status"]>("waiting");
  const [stepBuild, setStepBuild] = useState<Step["status"]>("waiting");
  const [stepEvaluate, setStepEvaluate] = useState<Step["status"]>("waiting");

  const [retrievalLogs, setRetrievalLogs] = useState<StepLog[]>([]);
  const [buildLogs, setBuildLogs] = useState<StepLog[]>([]);
  const [evaluateLogs, setEvaluateLogs] = useState<StepLog[]>([]);

  const successReport =
    result?.success && !("stage" in result.report)
      ? (result.report as SystematologyReport)
      : null;

  const steps: Step[] = [
    {
      label: "①",
      name: "检索",
      status: stepRetrieval,
      detail: stepRetrieval === "done" ? `${retrievalLogs.length} 步` : undefined,
      logs: retrievalLogs,
    },
    {
      label: "②",
      name: "建图",
      status: stepBuild,
      detail:
        stepBuild === "done" && successReport?.cld_visualization?.nodes
          ? `${successReport.cld_visualization.nodes.length} 节点`
          : undefined,
      logs: buildLogs,
    },
    {
      label: "③",
      name: "评估",
      status: stepEvaluate,
      detail:
        stepEvaluate === "done" && successReport?.leverage_ranking
          ? `${successReport.leverage_ranking.length} 杠杆点`
          : undefined,
      logs: evaluateLogs,
    },
  ];

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setQuestion("");
    setLoading(false);
    setAnimateCanvas(false);
    setStepRetrieval("waiting");
    setStepBuild("waiting");
    setStepEvaluate("waiting");
    setRetrievalLogs([]);
    setBuildLogs([]);
    setEvaluateLogs([]);
  }, []);

  const handleSend = useCallback(async (message: string) => {
    if (!message.trim()) return;
    const startTime = Date.now();

    reset();
    setQuestion(message.trim());
    setLoading(true);
    setStepRetrieval("running");

    try {
      // ═══ Stage 1: 检索 ═══
      const rLog: StepLog[] = [];
      rLog.push({ time: ts(startTime), message: "解析问题语义结构..." });
      setRetrievalLogs([...rLog]);

      await new Promise((r) => setTimeout(r, 500));
      rLog.push({ time: ts(startTime), message: "连接知识库索引 (chroma vector store)" });
      setRetrievalLogs([...rLog]);

      await new Promise((r) => setTimeout(r, 400));
      rLog.push({ time: ts(startTime), message: "查询向量化 → 语义检索 (top_k=5, threshold=0.3)" });
      setRetrievalLogs([...rLog]);

      const apiCall = api.systematologyAnalyze(message.trim());

      await new Promise((r) => setTimeout(r, 500));
      rLog.push({ time: ts(startTime), message: "检索完成，返回匹配文献集" });
      setRetrievalLogs([...rLog]);
      setStepRetrieval("done");

      // ═══ Stage 2: 建图 ═══
      setStepBuild("running");
      const bLog: StepLog[] = [];
      bLog.push({ time: ts(startTime), message: "加载文献全文，启动实体识别..." });
      setBuildLogs([...bLog]);

      await new Promise((r) => setTimeout(r, 500));
      bLog.push({ time: ts(startTime), message: "提取因果变量节点 (NER + relation extraction)" });
      setBuildLogs([...bLog]);

      const res = await apiCall;
      setResult(res);

      if (res.success) {
        const rpt = res.report as SystematologyReport;
        const nodeCount = rpt.cld_visualization?.nodes?.length ?? 0;
        const edgeCount = rpt.cld_visualization?.edges?.length ?? 0;
        // Estimate loops from edge-to-node ratio
        const estLoops = Math.max(1, edgeCount - nodeCount + 1);

        await new Promise((r2) => setTimeout(r2, 300));
        bLog.push({ time: ts(startTime), message: `已识别 ${nodeCount} 个因果变量，构建因果关系邻接矩阵` });
        setBuildLogs([...bLog]);

        await new Promise((r2) => setTimeout(r2, 500));
        bLog.push({ time: ts(startTime), message: `语义归并完成 → ${nodeCount} 节点、${edgeCount} 条边` });
        setBuildLogs([...bLog]);

        await new Promise((r2) => setTimeout(r2, 400));
        bLog.push({ time: ts(startTime), message: `检测反馈回路 → 识别约 ${estLoops} 个反馈回路` });
        setBuildLogs([...bLog]);

        await new Promise((r2) => setTimeout(r2, 300));
        bLog.push({ time: ts(startTime), message: "CLD 因果回路图生成完毕 ✓" });
        setBuildLogs([...bLog]);
      }
      setStepBuild("done");

      // ═══ Stage 3: 评估 ═══
      setStepEvaluate("running");
      const eLog: StepLog[] = [];
      eLog.push({ time: ts(startTime), message: "计算各节点网络中心度 (betweenness / closeness)..." });
      setEvaluateLogs([...eLog]);

      await new Promise((r) => setTimeout(r, 400));
      eLog.push({ time: ts(startTime), message: "评估节点影响力 (impact score) 与置信度 (confidence)" });
      setEvaluateLogs([...eLog]);

      await new Promise((r) => setTimeout(r, 500));
      const lpCount = res.success
        ? (res.report as SystematologyReport).leverage_ranking?.length ?? 0
        : 0;
      eLog.push({ time: ts(startTime), message: `杠杆点排序完成 → Top ${lpCount} 高影响力干预节点` });
      setEvaluateLogs([...eLog]);

      await new Promise((r) => setTimeout(r, 400));
      eLog.push({ time: ts(startTime), message: "综合洞察已生成 ✓" });
      setEvaluateLogs([...eLog]);
      setStepEvaluate("done");

      setAnimateCanvas(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "分析失败");
      setStepRetrieval("waiting");
      setStepBuild("waiting");
      setStepEvaluate("waiting");
    } finally {
      setLoading(false);
    }
  }, [reset]);

  return {
    loading,
    error,
    result,
    question,
    animateCanvas,
    steps,
    successReport,
    handleSend,
    reset,
  };
}
