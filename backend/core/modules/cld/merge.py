"""Systematology CLD merge: node deduplication using string similarity.

Project uses API-based LLM; no local sentence-transformers needed.
String similarity (Jaccard on character trigrams) is sufficient for
short concept labels in CLD node merging.
"""

from __future__ import annotations

from backend.core.models import CausalLink, CLDNode
from backend.infrastructure.logger import get_logger

logger = get_logger("systematology.merge")

MERGE_THRESHOLD = 0.6


def _string_similarity(a: str, b: str) -> float:
    """String similarity using character n-grams (Jaccard)."""
    a_lower = a.lower().strip()
    b_lower = b.lower().strip()
    if a_lower == b_lower:
        return 1.0

    def trigrams(s: str) -> set[str]:
        return {s[i:i+3] for i in range(max(len(s) - 2, 0))}

    ta, tb = trigrams(a_lower), trigrams(b_lower)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def compute_similarity_matrix(nodes: list[CLDNode]) -> list[list[float]]:
    """Compute pairwise similarity matrix for nodes using string similarity.

    Args:
        nodes: List of CLDNode objects.

    Returns:
        NxN similarity matrix as list of lists.
    """
    n = len(nodes)
    labels = [node.label for node in nodes]
    sim_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                sim_matrix[i][j] = 1.0
            else:
                sim_matrix[i][j] = _string_similarity(labels[i], labels[j])
    return sim_matrix


def merge_nodes(
    nodes: list[CLDNode],
    edges: list[CausalLink],
    threshold: float = MERGE_THRESHOLD,
) -> tuple[list[CLDNode], list[CausalLink], dict[str, str]]:
    """Merge similar nodes and remap edges.

    Args:
        nodes: Original node list.
        edges: Original edge list.
        threshold: Cosine similarity threshold for merging.

    Returns:
        Tuple of (merged_nodes, remapped_edges, merge_map).
        merge_map maps old node IDs to their merged node ID.
    """
    if len(nodes) <= 1:
        return nodes, edges, {}

    sim_matrix = compute_similarity_matrix(nodes)

    # Find merge groups using greedy approach
    n = len(nodes)
    merged_into: dict[int, int] = {}  # node_idx -> representative_idx

    for i in range(n):
        if i in merged_into:
            continue
        for j in range(i + 1, n):
            if j in merged_into:
                continue
            if sim_matrix[i][j] >= threshold:
                merged_into[j] = i

    # Build merge map: old_id -> new_id
    merge_map: dict[str, str] = {}
    merged_nodes: list[CLDNode] = []

    for i in range(n):
        if i in merged_into:
            # This node was merged into another
            rep = merged_into[i]
            # Walk to find the root representative
            while rep in merged_into:
                rep = merged_into[rep]
            merge_map[nodes[i].id] = nodes[rep].id
        else:
            # This is a representative node
            merged_nodes.append(nodes[i])
            merge_map[nodes[i].id] = nodes[i].id

    # Remap edges
    merged_edges: list[CausalLink] = []
    seen_edges: set[tuple[str, str, str]] = set()

    for edge in edges:
        new_source = merge_map.get(edge.source, edge.source)
        new_target = merge_map.get(edge.target, edge.target)

        # Skip self-loops (node merged with itself)
        if new_source == new_target:
            continue

        edge_key = (new_source, new_target, edge.relation)
        if edge_key not in seen_edges:
            seen_edges.add(edge_key)
            merged_edges.append(CausalLink(
                source=new_source,
                target=new_target,
                relation=edge.relation,
            ))

    logger.info(
        "Node merge complete",
        original=len(nodes),
        merged=len(merged_nodes),
        edges_before=len(edges),
        edges_after=len(merged_edges),
    )

    return merged_nodes, merged_edges, merge_map
