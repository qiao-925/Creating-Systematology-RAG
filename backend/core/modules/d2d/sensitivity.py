"""CLDFlow D2D sensitivity: single-node perturbation analysis.

Uses NumPy matrix operations for efficient computation.
Default perturbation: 10% (0.1).
"""

from __future__ import annotations

import numpy as np

from backend.core.models import SharedCLD
from backend.infrastructure.logger import get_logger

logger = get_logger("cldflow.d2d.sensitivity")


def compute_sensitivity(
    shared_cld: SharedCLD,
    perturbation_pct: float = 0.1,
) -> list[dict[str, float]]:
    """Compute sensitivity by perturbing each node individually.

    For each node i:
    1. Set state[i] = perturbation_pct
    2. Compute one-step propagation: effect = W^T @ perturbed_state
    3. Record the impact on all other nodes

    Args:
        shared_cld: The SharedCLD to analyze.
        perturbation_pct: Perturbation magnitude (0-1).

    Returns:
        List of dicts with 'node', 'total_impact', 'impacts' (per-node impacts).
    """
    nodes = shared_cld.nodes
    n = len(nodes)
    node_id_to_idx = {node.id: i for i, node in enumerate(nodes)}

    # Build adjacency matrix from edges
    W = np.zeros((n, n))
    for edge in shared_cld.edges:
        src = node_id_to_idx.get(edge.source)
        tgt = node_id_to_idx.get(edge.target)
        if src is not None and tgt is not None:
            from backend.core.modules.fcm.mapper import map_relation_to_weight
            W[src][tgt] = map_relation_to_weight(edge.relation)

    results: list[dict[str, float]] = []

    for i in range(n):
        # Create perturbed state
        state = np.zeros(n)
        state[i] = perturbation_pct

        # One-step propagation
        effect = W.T @ state

        # Record impacts
        impacts = {nodes[j].id: float(effect[j]) for j in range(n) if j != i and abs(effect[j]) > 1e-10}
        total_impact = float(np.sum(np.abs(effect)))

        results.append({
            "node": nodes[i].id,
            "node_label": nodes[i].label,
            "total_impact": total_impact,
            "impacts": impacts,
        })

    logger.info(
        "D2D sensitivity complete",
        nodes=n,
        edges=len(shared_cld.edges),
        top_node=max(results, key=lambda r: r["total_impact"])["node"] if results else "none",
    )

    return results
