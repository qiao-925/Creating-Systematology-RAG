"""Systematology Lead Agent tool definitions.

Each tool wraps a module's run() method and returns a JSON-serializable result.
The Lead Agent sees FunctionTool interfaces, not internal implementation.
"""

from __future__ import annotations

import json
from typing import Any

from llama_index.core.tools import FunctionTool

from backend.core.models import (
    CausalLink,
    CLDNode,
    FailureRecord,
    LeverageAnalysis,
    NodeImpact,
    RunContext,
    SharedCLD,
    StructuredFailureReport,
    StructuredReport,
    WeightedFCM,
)


def _make_run_cld_tool(run_context: RunContext, llm: Any = None, judge_model: str = "deepseek-chat") -> FunctionTool:
    """Create the CLD analysis tool for the Lead Agent."""

    async def run_cld_analysis(
        research_question: str,
        documents_json: str = "[]",
        perspective_hints: str = "[]",
        max_perspectives: int = 3,
    ) -> str:
        """Run CLD analysis to extract causal structure from research documents.

        Args:
            research_question: The research question to analyze.
            documents_json: JSON array of document texts.
            perspective_hints: JSON array of perspective hints (optional).
            max_perspectives: Maximum perspectives to generate (1-5).

        Returns:
            JSON summary with node/edge count and key structure.
        """
        try:
            docs = json.loads(documents_json) if documents_json else []
            hints = json.loads(perspective_hints) if perspective_hints else None

            from backend.core.modules.cld.module import CLDModule
            from backend.core.modules.cld.schema import CLDAnalysisInput

            module = CLDModule(llm=llm, judge_model=judge_model)
            input_data = CLDAnalysisInput(
                research_question=research_question,
                documents=docs,
                perspective_hints=hints,
                max_perspectives=max_perspectives,
            )
            output = await module.run(input_data)
            run_context.cached_cld = output.shared_cld
            run_context.tool_calls.append("run_cld_analysis")
            return json.dumps({
                "status": "ok",
                "nodes": len(output.shared_cld.nodes),
                "edges": len(output.shared_cld.edges),
                "perspectives": output.perspectives_used,
                "confidence": output.confidence,
            })
        except Exception as exc:
            run_context.failures.append(FailureRecord(stage="cld_analysis", reason=str(exc)))
            return json.dumps({"error": str(exc), "stage": "cld_analysis"})

    return FunctionTool.from_defaults(
        fn=run_cld_analysis,
        name="run_cld_analysis",
        description="Generate a SharedCLD (causal loop diagram) from a research question and documents.",
    )


def _make_run_fcm_tool(run_context: RunContext) -> FunctionTool:
    """Create the FCM simulation tool for the Lead Agent."""

    def run_fcm_analysis(
        shared_cld_json: str = "",
        scenarios_json: str = "[]",
    ) -> str:
        """Run FCM (Fuzzy Cognitive Map) simulation on the cached SharedCLD.

        The shared_cld_json argument is ignored — FCM reads from the cached CLD result.
        This avoids relying on the LLM to pass large JSON between tools.

        Args:
            shared_cld_json: Ignored (reads from RunContext cache).
            scenarios_json: JSON array of intervention scenarios (optional).

        Returns:
            JSON summary with matrix dimensions and simulation results.
        """
        try:
            shared_cld = run_context.cached_cld
            if shared_cld is None:
                # Fallback: try parsing from JSON argument
                if shared_cld_json and shared_cld_json != "":
                    shared_cld = SharedCLD(**json.loads(shared_cld_json))
                else:
                    raise ValueError("No cached CLD and no shared_cld_json provided")

            from backend.core.modules.fcm.mapper import map_weights
            from backend.core.modules.fcm.simulator import run_simulation

            weighted_fcm = map_weights(shared_cld)
            if scenarios_json and scenarios_json != "[]":
                scenarios = json.loads(scenarios_json)
                node_labels = [n.label for n in shared_cld.nodes]
                for scenario in scenarios:
                    initial = list(weighted_fcm.baseline_state)
                    for node_label, value in scenario.get("interventions", {}).items():
                        if node_label in node_labels:
                            idx = node_labels.index(node_label)
                            initial[idx] = value
                    state = run_simulation(weighted_fcm, shared_cld, initial_state=initial)
                    weighted_fcm.intervention_states[scenario.get("name", "unnamed")] = state

            run_context.cached_fcm = weighted_fcm
            run_context.tool_calls.append("run_fcm_analysis")
            n = len(shared_cld.nodes)
            return json.dumps({
                "status": "ok",
                "nodes": n,
                "edges": len(shared_cld.edges),
                "non_zero_weights": sum(1 for row in weighted_fcm.weight_matrix for w in row if w != 0),
                "scenarios_run": list(weighted_fcm.intervention_states.keys()),
            })
        except Exception as exc:
            run_context.failures.append(FailureRecord(stage="fcm_analysis", reason=str(exc)))
            return json.dumps({"error": str(exc), "stage": "fcm_analysis"})

    return FunctionTool.from_defaults(
        fn=run_fcm_analysis,
        name="run_fcm_analysis",
        description="Run FCM simulation on the cached CLD. Returns simulation summary.",
    )


def _make_run_d2d_tool(run_context: RunContext) -> FunctionTool:
    """Create the D2D analysis tool for the Lead Agent."""

    def run_d2d_analysis(
        shared_cld_json: str = "",
        perturbation_pct: float = 0.1,
    ) -> str:
        """Run D2D (Dynamic Leverage Point) analysis on the cached SharedCLD.

        The shared_cld_json argument is ignored — D2D reads from the cached CLD result.

        Args:
            shared_cld_json: Ignored (reads from RunContext cache).
            perturbation_pct: Perturbation percentage (0-1, default 0.1 = 10%).

        Returns:
            JSON summary with top leverage points.
        """
        try:
            shared_cld = run_context.cached_cld
            if shared_cld is None:
                if shared_cld_json and shared_cld_json != "":
                    shared_cld = SharedCLD(**json.loads(shared_cld_json))
                else:
                    raise ValueError("No cached CLD and no shared_cld_json provided")

            from backend.core.modules.d2d.sensitivity import compute_sensitivity
            from backend.core.modules.d2d.ranking import rank_leverage_points

            sensitivity = compute_sensitivity(shared_cld, perturbation_pct)
            leverage = rank_leverage_points(sensitivity, shared_cld)

            run_context.cached_leverage = leverage
            run_context.tool_calls.append("run_d2d_analysis")
            top = sorted(leverage.leverage_points, key=lambda x: x.impact_score, reverse=True)[:5]
            return json.dumps({
                "status": "ok",
                "leverage_points_count": len(leverage.leverage_points),
                "top_leverage": [{"node": lp.node, "score": round(lp.impact_score, 3), "confidence": lp.confidence} for lp in top],
            })
        except Exception as exc:
            run_context.failures.append(FailureRecord(stage="d2d_analysis", reason=str(exc)))
            return json.dumps({"error": str(exc), "stage": "d2d_analysis"})

    return FunctionTool.from_defaults(
        fn=run_d2d_analysis,
        name="run_d2d_analysis",
        description="Run D2D leverage point analysis on the cached CLD. Returns top leverage points.",
    )


def _make_report_tool(run_context: RunContext) -> FunctionTool:
    """Create the report generation tool for the Lead Agent."""

    def generate_report(
        shared_cld_json: str = "",
        weighted_fcm_json: str = "null",
        leverage_analysis_json: str = "null",
        synthesized_insights: str = "",
    ) -> str:
        """Generate a structured report from cached analysis results.

        JSON arguments are ignored — the report is built from RunContext cache.
        Only synthesized_insights is used directly.

        Args:
            shared_cld_json: Ignored (reads from cache).
            weighted_fcm_json: Ignored (reads from cache).
            leverage_analysis_json: Ignored (reads from cache).
            synthesized_insights: Natural language synthesis of findings.

        Returns:
            JSON StructuredReport.
        """
        try:
            shared_cld = run_context.cached_cld
            weighted_fcm = run_context.cached_fcm
            leverage = run_context.cached_leverage

            if shared_cld is None:
                raise ValueError("No cached CLD — run CLD analysis first")

            report = StructuredReport(
                cld_visualization={
                    "nodes": [n.model_dump() for n in shared_cld.nodes],
                    "edges": [e.model_dump() for e in shared_cld.edges],
                },
                scenario_comparison=weighted_fcm.model_dump() if weighted_fcm else None,
                leverage_ranking=[lp.model_dump() for lp in leverage.leverage_points] if leverage else None,
                synthesized_insights=synthesized_insights or "Analysis completed.",
                evidence_tracing={"run_id": run_context.run_id, "tool_calls": run_context.tool_calls},
            )
            return json.dumps(report.model_dump(), default=str)
        except Exception as exc:
            run_context.failures.append(FailureRecord(stage="report", reason=str(exc)))
            return json.dumps({"error": str(exc), "stage": "report"})

    return FunctionTool.from_defaults(
        fn=generate_report,
        name="generate_report",
        description="Synthesize CLD/FCM/D2D results into a structured report. Reads from cached analysis results.",
    )


def _make_failure_report_tool(run_context: RunContext) -> FunctionTool:
    """Create the failure report tool."""

    def generate_failure_report(stage: str, reason: str, details: str = "{}") -> str:
        """Generate a structured failure report when analysis cannot continue.

        Args:
            stage: Which pipeline stage failed.
            reason: Why it failed.
            details: JSON of additional details.

        Returns:
            JSON StructuredFailureReport.
        """
        report = StructuredFailureReport(
            run_id=run_context.run_id,
            stage=stage,
            reason=reason,
            details=json.loads(details) if details else {},
        )
        run_context.failures.append(
            FailureRecord(stage=stage, reason=reason, details=report.details)
        )
        return json.dumps(report.model_dump(), default=str)

    return FunctionTool.from_defaults(
        fn=generate_failure_report,
        name="generate_failure_report",
        description="Generate a structured failure report when analysis cannot proceed.",
    )


def create_lead_agent_tools(
    run_context: RunContext,
    llm: Any = None,
    judge_model: str = "deepseek-chat",
) -> list[FunctionTool]:
    """Create all tools for the Lead Agent."""
    return [
        _make_run_cld_tool(run_context, llm=llm, judge_model=judge_model),
        _make_run_fcm_tool(run_context),
        _make_run_d2d_tool(run_context),
        _make_report_tool(run_context),
        _make_failure_report_tool(run_context),
    ]
