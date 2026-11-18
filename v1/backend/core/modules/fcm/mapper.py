"""Systematology FCM mapper: maps qualitative relation strengths to numerical weights.

7-level mapping table: ±L/M/H/VH → ±0.3/0.5/0.7/0.9
"""

from __future__ import annotations

from backend.core.models import CausalLink, SharedCLD, WeightedFCM
from backend.infrastructure.logger import get_logger

logger = get_logger("systematology.fcm.mapper")

# Relation type → base weight (direction encoded in sign)
RELATION_WEIGHTS: dict[str, float] = {
    "causes": 0.7,
    "enables": 0.5,
    "influences": 0.5,
    "supports": 0.5,
    "requires": 0.7,
    "inhibits": -0.7,
}

# Default weight for unknown relations
DEFAULT_WEIGHT = 0.5


def map_relation_to_weight(relation: str) -> float:
    """Map a relation string to a numerical weight.

    Args:
        relation: One of the CausalLink relation types.

    Returns:
        Float weight in [-1.0, 1.0].
    """
    return RELATION_WEIGHTS.get(relation, DEFAULT_WEIGHT)


def map_weights(shared_cld: SharedCLD) -> WeightedFCM:
    """Build a WeightedFCM from a SharedCLD using the mapping table.

    Creates:
    - weight_matrix: NxN where N = len(nodes)
    - confidence_matrix: NxN with 0.5 default confidence
    - baseline_state: N zeros

    Args:
        shared_cld: The SharedCLD to convert.

    Returns:
        WeightedFCM with weight and confidence matrices.
    """
    nodes = shared_cld.nodes
    n = len(nodes)
    node_id_to_idx = {node.id: i for i, node in enumerate(nodes)}

    # Initialize matrices
    weight_matrix = [[0.0] * n for _ in range(n)]
    confidence_matrix = [[0.5] * n for _ in range(n)]

    # Fill from edges
    for edge in shared_cld.edges:
        src_idx = node_id_to_idx.get(edge.source)
        tgt_idx = node_id_to_idx.get(edge.target)
        if src_idx is None or tgt_idx is None:
            logger.warning(
                "Edge references unknown node",
                source=edge.source,
                target=edge.target,
            )
            continue

        weight = map_relation_to_weight(edge.relation)
        weight_matrix[src_idx][tgt_idx] = weight
        confidence_matrix[src_idx][tgt_idx] = 0.6  # Default confidence for mapped edges

    baseline_state = [0.0] * n

    logger.info(
        "FCM weight mapping complete",
        nodes=n,
        edges=len(shared_cld.edges),
        non_zero=sum(1 for row in weight_matrix for w in row if w != 0),
    )

    return WeightedFCM(
        weight_matrix=weight_matrix,
        confidence_matrix=confidence_matrix,
        baseline_state=baseline_state,
    )
