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
            JSON with shared_cld, perspectives_used, confidence, diagnostics.
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
            run_context.tool_calls.append("run_cld_analysis")
            return json.dumps(output.model_dump(), default=str)
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
        shared_cld_json: str,
        scenarios_json: str = "[]",
    ) -> str:
        """Run FCM (Fuzzy Cognitive Map) simulation on a SharedCLD.

        Args:
            shared_cld_json: JSON of the SharedCLD from CLD analysis.
            scenarios_json: JSON array of intervention scenarios (optional).

        Returns:
            JSON with weighted_fcm and diagnostics.
        """
        try:
            cld_data = json.loads(shared_cld_json)
            shared_cld = SharedCLD(**cld_data)

            from backend.core.modules.fcm.mapper import map_weights
            from backend.core.modules.fcm.simulator import run_simulation

            weighted_fcm = map_weights(shared_cld)
            if scenarios_json and scenarios_json != "[]":
                scenarios = json.loads(scenarios_json)
                node_labels = [n.label for n in shared_cld.nodes]
                for scenario in scenarios:
                    # Apply interventions: override baseline state for specified nodes
                    initial = list(weighted_fcm.baseline_state)
                    for node_label, value in scenario.get("interventions", {}).items():
                        if node_label in node_labels:
                            idx = node_labels.index(node_label)
                            initial[idx] = value
                    state = run_simulation(weighted_fcm, shared_cld, initial_state=initial)
                    weighted_fcm.intervention_states[scenario.get("name", "unnamed")] = state

            run_context.tool_calls.append("run_fcm_analysis")
            return json.dumps(weighted_fcm.model_dump(), default=str)
        except Exception as exc:
            run_context.failures.append(FailureRecord(stage="fcm_analysis", reason=str(exc)))
            return json.dumps({"error": str(exc), "stage": "fcm_analysis"})

    return FunctionTool.from_defaults(
        fn=run_fcm_analysis,
        name="run_fcm_analysis",
        description="Run FCM simulation on a SharedCLD. Returns weighted FCM with simulation results.",
    )


def _make_run_d2d_tool(run_context: RunContext) -> FunctionTool:
    """Create the D2D analysis tool for the Lead Agent."""

    def run_d2d_analysis(
        shared_cld_json: str,
        perturbation_pct: float = 0.1,
    ) -> str:
        """Run D2D (Dynamic Leverage Point) analysis on a SharedCLD.

        Args:
            shared_cld_json: JSON of the SharedCLD from CLD analysis.
            perturbation_pct: Perturbation percentage (0-1, default 0.1 = 10%).

        Returns:
            JSON with leverage_analysis and diagnostics.
        """
        try:
            cld_data = json.loads(shared_cld_json)
            shared_cld = SharedCLD(**cld_data)

            from backend.core.modules.d2d.sensitivity import compute_sensitivity
            from backend.core.modules.d2d.ranking import rank_leverage_points

            sensitivity = compute_sensitivity(shared_cld, perturbation_pct)
            leverage = rank_leverage_points(sensitivity, shared_cld)

            run_context.tool_calls.append("run_d2d_analysis")
            return json.dumps(leverage.model_dump(), default=str)
        except Exception as exc:
            run_context.failures.append(FailureRecord(stage="d2d_analysis", reason=str(exc)))
            return json.dumps({"error": str(exc), "stage": "d2d_analysis"})

    return FunctionTool.from_defaults(
        fn=run_d2d_analysis,
        name="run_d2d_analysis",
        description="Run D2D leverage point analysis on a SharedCLD. Returns leverage ranking.",
    )


def _make_report_tool(run_context: RunContext) -> FunctionTool:
    """Create the report generation tool for the Lead Agent."""

    def generate_report(
        shared_cld_json: str,
        weighted_fcm_json: str = "null",
        leverage_analysis_json: str = "null",
        synthesized_insights: str = "",
    ) -> str:
        """Generate a structured report from all analysis results.

        Args:
            shared_cld_json: JSON of the SharedCLD.
            weighted_fcm_json: JSON of WeightedFCM (optional).
            leverage_analysis_json: JSON of LeverageAnalysis (optional).
            synthesized_insights: Natural language synthesis of findings.

        Returns:
            JSON StructuredReport.
        """
        try:
            shared_cld = SharedCLD(**json.loads(shared_cld_json))
            weighted_fcm = WeightedFCM(**json.loads(weighted_fcm_json)) if weighted_fcm_json != "null" else None
            leverage = LeverageAnalysis(**json.loads(leverage_analysis_json)) if leverage_analysis_json != "null" else None

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
        description="Synthesize CLD/FCM/D2D results into a structured report.",
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
