"""CLDFlow CLD conflict detection: identifies contradictory causal links.

Detects conflicts where two perspectives assign different relations
to the same (source, target) pair.
"""

from __future__ import annotations

from typing import Any

from backend.core.models import CausalLink
from backend.infrastructure.logger import get_logger

logger = get_logger("cldflow.conflict")

# Conflict severity thresholds
CONFLICT_THRESHOLD_LOW = 0.3
CONFLICT_THRESHOLD_MEDIUM = 0.5
CONFLICT_THRESHOLD_HIGH = 0.7


def detect_conflicts(
    specialist_outputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect conflicting causal links across specialist outputs.

    A conflict occurs when different perspectives assign different relations
    to the same (source, target) pair.

    Args:
        specialist_outputs: List of specialist output dicts with 'links' key.

    Returns:
        List of conflict dicts with keys:
        - source, target: the conflicting edge endpoints
        - perspectives: dict mapping perspective_id to assigned relation
        - severity: "low", "medium", or "high"
    """
    # Group links by (source, target) across perspectives
    edge_perspectives: dict[tuple[str, str], dict[str, str]] = {}

    for output in specialist_outputs:
        pid = output.get("perspective_id", "unknown")
        links = output.get("links", [])

        for link in links:
            if isinstance(link, dict):
                src = link.get("source", "")
                tgt = link.get("target", "")
                rel = link.get("relation", "influences")
                key = (src, tgt)

                if key not in edge_perspectives:
                    edge_perspectives[key] = {}
                edge_perspectives[key][pid] = rel

    # Find conflicts
    conflicts: list[dict[str, Any]] = []

    for (src, tgt), perspectives in edge_perspectives.items():
        unique_relations = set(perspectives.values())
        if len(unique_relations) > 1:
            # Conflict detected
            severity = _classify_severity(perspectives)
            conflicts.append({
                "source": src,
                "target": tgt,
                "perspectives": perspectives,
                "unique_relations": list(unique_relations),
                "severity": severity,
            })

    logger.info(
        "Conflict detection complete",
        total_edges=len(edge_perspectives),
        conflicts=len(conflicts),
        high=sum(1 for c in conflicts if c["severity"] == "high"),
        medium=sum(1 for c in conflicts if c["severity"] == "medium"),
        low=sum(1 for c in conflicts if c["severity"] == "low"),
    )

    return conflicts


def _classify_severity(perspectives: dict[str, str]) -> str:
    """Classify conflict severity based on relation divergence.

    - Opposite relations (causes vs inhibits) → high
    - Related but different (influences vs supports) → medium
    - Minor variation → low
    """
    relations = set(perspectives.values())

    # High severity: directly opposing
    opposing_pairs = [
        ({"causes", "inhibits"}),
        ({"enables", "inhibits"}),
        ({"supports", "inhibits"}),
    ]
    for pair in opposing_pairs:
        if pair.issubset(relations):
            return "high"

    # Medium severity: different strength
    if len(relations) >= 3:
        return "medium"

    return "low"


def resolve_conflicts_by_arbitration(
    conflicts: list[dict[str, Any]],
    all_links: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Resolve conflicts by keeping the most common relation (majority vote).

    For ties, keeps the relation that appears first in the all_links list.

    Args:
        conflicts: Conflict list from detect_conflicts().
        all_links: All links from all specialists.

    Returns:
        Resolved list of links (conflicts removed, majority kept).
    """
    conflict_keys: set[tuple[str, str]] = set()
    conflict_resolutions: dict[tuple[str, str], str] = {}

    for conflict in conflicts:
        key = (conflict["source"], conflict["target"])
        conflict_keys.add(key)

        # Majority vote
        relation_counts: dict[str, int] = {}
        for rel in conflict["perspectives"].values():
            relation_counts[rel] = relation_counts.get(rel, 0) + 1

        best_relation = max(relation_counts, key=lambda r: relation_counts[r])
        conflict_resolutions[key] = best_relation

    # Build resolved list
    resolved: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()

    for link in all_links:
        key = (link["source"], link["target"])
        if key in conflict_keys:
            if key not in seen_keys:
                resolved.append({
                    "source": key[0],
                    "target": key[1],
                    "relation": conflict_resolutions[key],
                    "conflict_resolved": True,
                })
                seen_keys.add(key)
        else:
            resolved.append(link)

    return resolved
