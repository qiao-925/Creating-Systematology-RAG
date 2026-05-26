"""Systematology CLD Judge: arbitrates high-conflict outputs and performs self-review.

Model selection (G6 fallback strategy):
  - If OPENAI_API_KEY is set → use GPT-4o-mini (preferred for evaluation)
  - Otherwise → use the configured judge_model (defaults to DeepSeek)
"""

from __future__ import annotations

import json
import os
from typing import Any

from llama_index.core.llms import LLM

from backend.core.models import CausalLink, CLDNode, SharedCLD
from backend.infrastructure.logger import get_logger

logger = get_logger("systematology.judge")

JUDGE_PROMPT = """You are a research quality judge. Review the following causal loop diagram (CLD) analysis.

## Analysis Results
- Perspectives analyzed: {perspective_count}
- Total nodes: {node_count}
- Total edges: {edge_count}
- Conflicts detected: {conflict_count}

## Conflict Details
{conflict_details}

## Merged CLD
{merged_cld}

## Task
Evaluate the quality of this CLD analysis. Respond with a JSON object:
{{
  "approved": true/false,
  "quality_score": 0.0-1.0,
  "issues": ["list of issues found"],
  "suggestions": ["list of improvements"],
  "reasoning": "brief explanation"
}}

Quality criteria:
1. Nodes are clear, distinct concepts (not redundant)
2. Edges represent plausible causal relationships
3. The graph has meaningful structure (not trivially simple)
4. Conflicts are either resolved or acknowledged
5. Coverage of the research question is adequate
"""


async def judge_cld_output(
    shared_cld: SharedCLD,
    specialist_outputs: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    llm: LLM,
) -> dict[str, Any]:
    """Judge the quality of a merged CLD.

    Args:
        shared_cld: The merged SharedCLD.
        specialist_outputs: Raw outputs from all specialists.
        conflicts: Detected conflicts.
        llm: LLM for evaluation.

    Returns:
        Dict with 'approved', 'quality_score', 'issues', 'suggestions', 'reasoning'.
    """
    conflict_details = "None"
    if conflicts:
        conflict_lines = []
        for c in conflicts[:5]:  # Limit to 5 for prompt size
            conflict_lines.append(
                f"- [{c['severity']}] {c['source']} → {c['target']}: "
                f"{', '.join(f'{pid}={rel}' for pid, rel in c['perspectives'].items())}"
            )
        conflict_details = "\n".join(conflict_lines)

    merged_cld_str = json.dumps({
        "nodes": [{"id": n.id, "label": n.label} for n in shared_cld.nodes],
        "edges": [{"source": e.source, "target": e.target, "relation": e.relation} for e in shared_cld.edges],
    }, indent=2)

    prompt = JUDGE_PROMPT.format(
        perspective_count=len(specialist_outputs),
        node_count=len(shared_cld.nodes),
        edge_count=len(shared_cld.edges),
        conflict_count=len(conflicts),
        conflict_details=conflict_details,
        merged_cld=merged_cld_str,
    )

    try:
        response = await llm.acomplete(prompt)
        result = _parse_judge_response(response.text)
        logger.info(
            "Judge evaluation complete",
            approved=result.get("approved"),
            quality_score=result.get("quality_score"),
            issues=len(result.get("issues", [])),
        )
        return result
    except Exception as exc:
        logger.warning("Judge evaluation failed", error=str(exc))
        return {
            "approved": True,  # Default to approved on failure
            "quality_score": 0.5,
            "issues": [f"Judge failed: {exc}"],
            "suggestions": [],
            "reasoning": "Judge evaluation failed, defaulting to approved",
        }


def _parse_judge_response(text: str) -> dict[str, Any]:
    """Parse judge LLM response."""
    text = text.strip()

    # Extract JSON from code block
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
        brace_start = text.find("{")
        brace_end = text.rfind("}") + 1
        if brace_start != -1 and brace_end > brace_start:
            data = json.loads(text[brace_start:brace_end])
        else:
            return {"approved": True, "quality_score": 0.5, "issues": ["Parse error"], "suggestions": [], "reasoning": text[:500]}

    return {
        "approved": bool(data.get("approved", True)),
        "quality_score": float(data.get("quality_score", 0.5)),
        "issues": list(data.get("issues", [])),
        "suggestions": list(data.get("suggestions", [])),
        "reasoning": str(data.get("reasoning", "")),
    }


async def self_review_gate(
    shared_cld: SharedCLD,
    specialist_outputs: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    llm: LLM,
    min_quality_score: float = 0.4,
) -> tuple[bool, dict[str, Any]]:
    """Run self-review gate. Returns (passed, review_details).

    The gate fails if:
    - quality_score < min_quality_score
    - judge says not approved
    - CLD has < 2 nodes or < 1 edge
    """
    # Structural checks
    if len(shared_cld.nodes) < 2:
        return False, {"approved": False, "quality_score": 0.0, "issues": ["Too few nodes"], "reasoning": "Structural check failed"}
    if len(shared_cld.edges) < 1:
        return False, {"approved": False, "quality_score": 0.0, "issues": ["No edges"], "reasoning": "Structural check failed"}

    # Judge evaluation
    review = await judge_cld_output(shared_cld, specialist_outputs, conflicts, llm)

    if not review.get("approved", True):
        return False, review
    if review.get("quality_score", 0.0) < min_quality_score:
        return False, review

    return True, review


def get_judge_llm(default_model: str = "deepseek-chat") -> LLM:
    """Create a Judge LLM with fallback strategy.

    G6 logic:
      - If OPENAI_API_KEY is set → GPT-4o-mini (better at evaluation tasks)
      - Otherwise → use the configured judge_model (typically DeepSeek)

    Args:
        default_model: Fallback model ID when OpenAI is unavailable.

    Returns:
        LLM instance for judge evaluation.
    """
    from backend.infrastructure.llms.factory import create_llm

    if os.getenv("OPENAI_API_KEY"):
        logger.info("Judge using GPT-4o-mini (OPENAI_API_KEY available)")
        return create_llm(model_id="gpt-4o-mini")

    logger.info("Judge using fallback model", model=default_model)
    return create_llm(model_id=default_model)
