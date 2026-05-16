"""CLDFlow D2D ranking: ranks leverage points by impact and confidence.

Combines sensitivity results with uncertainty ranges to produce
the final LeverageAnalysis output.
"""

from __future__ import annotations

from backend.core.models import LeverageAnalysis, NodeImpact, SharedCLD
from backend.infrastructure.logger import get_logger

logger = get_logger("cldflow.d2d.ranking")


def rank_leverage_points(
    sensitivity_results: list[dict],
    shared_cld: SharedCLD,
    uncertainty_ranges: dict[str, tuple[float, float]] | None = None,
) -> LeverageAnalysis:
    """Rank nodes by leverage (impact × confidence).

    Args:
        sensitivity_results: Output from compute_sensitivity().
        shared_cld: The SharedCLD.
        uncertainty_ranges: Optional uncertainty ranges from compute_uncertainty_ranges().

    Returns:
        LeverageAnalysis with ranked leverage points.
    """
    # Build node label lookup
    node_labels = {node.id: node.label for node in shared_cld.nodes}

    # Build impact list
    impacts: list[NodeImpact] = []
    for result in sensitivity_results:
        node_id = result["node"]
        total_impact = result["total_impact"]

        # Determine confidence level from impact magnitude
        if total_impact > 0.7:
            confidence = "high"
        elif total_impact > 0.3:
            confidence = "medium"
        else:
            confidence = "low"

        # Get affected nodes
        affected = [
            node_labels.get(nid, nid)
            for nid in result.get("impacts", {}).keys()
        ]

        impacts.append(NodeImpact(
            node=node_labels.get(node_id, node_id),
            impact_score=round(total_impact, 4),
            confidence=confidence,
            affected_nodes=affected,
        ))

    # Sort by impact score descending
    impacts.sort(key=lambda x: x.impact_score, reverse=True)

    # Build uncertainty ranges
    ranges: dict[str, tuple[float, float]] = {}
    if uncertainty_ranges:
        for node_id, bounds in uncertainty_ranges.items():
            label = node_labels.get(node_id, node_id)
            ranges[label] = bounds
    else:
        # Default: ±20% for all
        for impact in impacts:
            margin = impact.impact_score * 0.2
            ranges[impact.node] = (
                round(max(0.0, impact.impact_score - margin), 4),
                round(impact.impact_score + margin, 4),
            )

    logger.info(
        "D2D ranking complete",
        leverage_points=len(impacts),
        top_point=impacts[0].node if impacts else "none",
    )

    return LeverageAnalysis(
        leverage_points=impacts,
        uncertainty_ranges=ranges,
    )
