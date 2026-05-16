"""CLDFlow reporting: synthesizes analysis results into structured reports.

Report layer uses Lead Agent for semantic fusion, not hardcoded data transformation.
"""

from __future__ import annotations

from typing import Any

from backend.core.models import (
    LeverageAnalysis,
    RunContext,
    SharedCLD,
    StructuredFailureReport,
    StructuredReport,
    WeightedFCM,
)
from backend.infrastructure.logger import get_logger

logger = get_logger("cldflow.reporting")


def synthesize_report(
    run_context: RunContext,
    shared_cld: SharedCLD,
    weighted_fcm: WeightedFCM | None = None,
    leverage_analysis: LeverageAnalysis | None = None,
    synthesized_insights: str = "",
) -> StructuredReport:
    """Synthesize all analysis results into a structured report.

    Args:
        run_context: Run context with metadata.
        shared_cld: The CLD analysis result.
        weighted_fcm: Optional FCM simulation result.
        leverage_analysis: Optional D2D leverage analysis.
        synthesized_insights: Natural language synthesis from Lead Agent.

    Returns:
        StructuredReport with all available results.
    """
    cld_viz = {
        "nodes": [n.model_dump() for n in shared_cld.nodes],
        "edges": [e.model_dump() for e in shared_cld.edges],
        "metadata": shared_cld.metadata,
    }

    scenario_comparison = None
    if weighted_fcm:
        scenario_comparison = {
            "weight_matrix": weighted_fcm.weight_matrix,
            "baseline_state": weighted_fcm.baseline_state,
            "intervention_states": weighted_fcm.intervention_states,
        }

    leverage_ranking = None
    if leverage_analysis:
        leverage_ranking = [lp.model_dump() for lp in leverage_analysis.leverage_points]

    if not synthesized_insights:
        synthesized_insights = _generate_default_insights(
            shared_cld, weighted_fcm, leverage_analysis
        )

    report = StructuredReport(
        cld_visualization=cld_viz,
        scenario_comparison=scenario_comparison,
        leverage_ranking=leverage_ranking,
        synthesized_insights=synthesized_insights,
        evidence_tracing={
            "run_id": run_context.run_id,
            "tool_calls": run_context.tool_calls,
            "failures": len(run_context.failures),
        },
    )

    logger.info(
        "Report synthesized",
        run_id=run_context.run_id,
        has_fcm=weighted_fcm is not None,
        has_d2d=leverage_analysis is not None,
    )

    return report


def _generate_default_insights(
    shared_cld: SharedCLD,
    weighted_fcm: WeightedFCM | None,
    leverage_analysis: LeverageAnalysis | None,
) -> str:
    """Generate default insights when Lead Agent doesn't provide them."""
    parts = []

    parts.append(f"Analysis identified {len(shared_cld.nodes)} key concepts "
                 f"connected by {len(shared_cld.edges)} causal relationships.")

    if shared_cld.metadata.get("conflict_count", 0) > 0:
        parts.append(f"{shared_cld.metadata['conflict_count']} conflicts were detected and resolved.")

    if weighted_fcm:
        parts.append("FCM simulation was performed with Kosko iteration.")

    if leverage_analysis and leverage_analysis.leverage_points:
        top = leverage_analysis.leverage_points[0]
        parts.append(f"Top leverage point: {top.node} (impact: {top.impact_score:.2f}).")

    return " ".join(parts) if parts else "Analysis completed."
