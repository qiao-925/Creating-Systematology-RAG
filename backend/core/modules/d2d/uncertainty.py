"""Systematology D2D uncertainty: propagates weight confidence into impact estimates.

Converts FCM confidence matrix into uncertainty ranges for leverage points.
"""

from __future__ import annotations

from backend.core.models import SharedCLD, WeightedFCM
from backend.infrastructure.logger import get_logger

logger = get_logger("systematology.d2d.uncertainty")


def compute_uncertainty_ranges(
    shared_cld: SharedCLD,
    weighted_fcm: WeightedFCM,
    sensitivity_results: list[dict],
) -> dict[str, tuple[float, float]]:
    """Compute uncertainty ranges for each node's impact score.

    Uses confidence matrix to estimate upper/lower bounds:
    - High confidence (0.8-1.0): narrow range (±10%)
    - Medium confidence (0.4-0.8): moderate range (±30%)
    - Low confidence (0.0-0.4): wide range (±50%)

    Args:
        shared_cld: The SharedCLD.
        weighted_fcm: WeightedFCM with confidence matrix.
        sensitivity_results: Output from compute_sensitivity().

    Returns:
        Dict mapping node ID to (lower_bound, upper_bound) impact range.
    """
    nodes = shared_cld.nodes
    n = len(nodes)

    # Average confidence per node (from its outgoing edges)
    node_confidences: dict[str, float] = {}
    for i, node in enumerate(nodes):
        confidences = []
        for j in range(n):
            if i < len(weighted_fcm.confidence_matrix) and j < len(weighted_fcm.confidence_matrix[i]):
                c = weighted_fcm.confidence_matrix[i][j]
                if c > 0:
                    confidences.append(c)
        node_confidences[node.id] = sum(confidences) / len(confidences) if confidences else 0.5

    # Build uncertainty ranges
    ranges: dict[str, tuple[float, float]] = {}
    for result in sensitivity_results:
        node_id = result["node"]
        impact = result["total_impact"]
        conf = node_confidences.get(node_id, 0.5)

        # Uncertainty factor: lower confidence → wider range
        uncertainty_factor = 1.0 - conf  # 0.0 (high conf) to 1.0 (low conf)
        margin = impact * uncertainty_factor * 0.5

        lower = max(0.0, impact - margin)
        upper = impact + margin
        ranges[node_id] = (round(lower, 4), round(upper, 4))

    logger.info(
        "D2D uncertainty computed",
        nodes=len(ranges),
        avg_confidence=sum(node_confidences.values()) / len(node_confidences) if node_confidences else 0,
    )

    return ranges
