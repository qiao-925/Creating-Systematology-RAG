"""CLDFlow FCM rater: LLM-based batch rating of edge weights.

Uses DeepSeek-V3 to rate all edges in a single call for global context.
"""

from __future__ import annotations

import json
from typing import Any

from llama_index.core.llms import LLM

from backend.core.models import CausalLink, SharedCLD
from backend.infrastructure.logger import get_logger

logger = get_logger("cldflow.fcm.rater")

RATER_PROMPT = """You are a quantitative analyst. Rate the strength of each causal relationship.

## Causal Loop Diagram
Nodes: {node_list}

Edges:
{edge_list}

## Rating Scale
Use these ratings for each edge:
- +L (positive low): +0.3
- +M (positive medium): +0.5
- +H (positive high): +0.7
- +VH (positive very high): +0.9
- -L (negative low): -0.3
- -M (negative medium): -0.5
- -H (negative high): -0.7
- -VH (negative very high): -0.9

## Output Format
Return a JSON array of ratings:
[
  {{"source": "node_id", "target": "node_id", "rating": "+H", "confidence": 0.7, "reasoning": "brief explanation"}},
  ...
]

Rate ALL edges. Consider the global context of the full diagram when rating each edge.
"""


async def rate_edges(
    shared_cld: SharedCLD,
    llm: LLM,
) -> dict[tuple[str, str], tuple[float, float, str]]:
    """Rate all edges using LLM.

    Args:
        shared_cld: The SharedCLD with edges to rate.
        llm: LLM for rating.

    Returns:
        Dict mapping (source, target) → (weight, confidence, reasoning).
    """
    node_list = "\n".join(f"- {n.id}: {n.label}" for n in shared_cld.nodes)
    edge_list = "\n".join(
        f"- {e.source} → {e.target} ({e.relation})"
        for e in shared_cld.edges
    )

    prompt = RATER_PROMPT.format(node_list=node_list, edge_list=edge_list)

    try:
        response = await llm.acomplete(prompt)
        ratings = _parse_ratings(response.text)
        logger.info("Edge rating complete", rated=len(ratings), total=len(shared_cld.edges))
        return ratings
    except Exception as exc:
        logger.warning("Edge rating failed, using defaults", error=str(exc))
        # Fallback: use mapper defaults
        from backend.core.modules.fcm.mapper import map_relation_to_weight
        return {
            (e.source, e.target): (map_relation_to_weight(e.relation), 0.3, "fallback")
            for e in shared_cld.edges
        }


def _parse_ratings(text: str) -> dict[tuple[str, str], tuple[float, float, str]]:
    """Parse LLM rating response."""
    text = text.strip()

    # Extract JSON array
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        text = text[start:end].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        bracket_start = text.find("[")
        bracket_end = text.rfind("]") + 1
        if bracket_start != -1 and bracket_end > bracket_start:
            data = json.loads(text[bracket_start:bracket_end])
        else:
            return {}

    rating_map = {
        "+L": 0.3, "+M": 0.5, "+H": 0.7, "+VH": 0.9,
        "-L": -0.3, "-M": -0.5, "-H": -0.7, "-VH": -0.9,
    }

    results: dict[tuple[str, str], tuple[float, float, str]] = {}
    for item in data:
        if isinstance(item, dict):
            src = item.get("source", "")
            tgt = item.get("target", "")
            rating = item.get("rating", "+M").upper()
            confidence = float(item.get("confidence", 0.5))
            reasoning = item.get("reasoning", "")
            weight = rating_map.get(rating, 0.5)
            results[(src, tgt)] = (weight, confidence, reasoning)

    return results
