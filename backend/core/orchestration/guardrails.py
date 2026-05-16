"""CLDFlow orchestration guardrails.

Five guardrails for pipeline safety:
- Pipeline Rail: ensure CLD runs before FCM/D2D
- Budget Guard: token + turn budget enforcement
- Schema Guard: validate tool I/O against Pydantic models
- Isolation Guard: Specialist outputs are self-contained
- Self-Review Gate: CLD output quality check
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from backend.core.models import RunContext, SharedCLD


def check_pipeline_rail(run_context: RunContext, required_stage: str) -> None:
    """Ensure a required stage has been called before allowing the next.

    The Lead Agent records tool calls in run_context.tool_calls.
    This guardrail checks that the required stage appears there.
    """
    if required_stage not in run_context.tool_calls:
        raise RuntimeError(
            f"Pipeline rail: '{required_stage}' must complete before proceeding. "
            f"Completed stages: {run_context.tool_calls}"
        )


def check_budget(run_context: RunContext, estimated_tokens: int = 0) -> None:
    """Check token and turn budgets before making an LLM call."""
    if run_context.current_turn >= run_context.budget_turns:
        raise RuntimeError(
            f"Budget guard: turn limit reached ({run_context.budget_turns})"
        )
    remaining_tokens = run_context.budget_tokens - run_context.tokens_used
    if estimated_tokens > 0 and estimated_tokens > remaining_tokens:
        raise RuntimeError(
            f"Budget guard: estimated {estimated_tokens} tokens exceed "
            f"remaining budget ({remaining_tokens})"
        )
    if remaining_tokens <= 0:
        raise RuntimeError("Budget guard: token budget exhausted")


def check_schema(data: dict[str, Any], model: type[BaseModel]) -> BaseModel:
    """Validate raw data against a Pydantic model. Returns parsed instance."""
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise RuntimeError(f"Schema guard: validation failed for {model.__name__}: {exc}") from exc


def check_isolation(specialist_outputs: list[dict[str, Any]]) -> None:
    """Ensure Specialist outputs don't cross-reference each other.

    Each Specialist should produce self-contained causal links.
    This checks that no output references another output's ID namespace.
    """
    output_ids: set[str] = set()
    for output in specialist_outputs:
        perspective_id = output.get("perspective_id", "")
        if perspective_id:
            output_ids.add(perspective_id)

    for output in specialist_outputs:
        links = output.get("links", [])
        for link in links:
            source = link.get("source", "")
            target = link.get("target", "")
            # Links should not reference other perspectives' internal IDs
            for pid in output_ids:
                if pid != output.get("perspective_id", ""):
                    if source.startswith(pid + ".") or target.startswith(pid + "."):
                        raise RuntimeError(
                            f"Isolation guard: cross-reference detected. "
                            f"Perspective '{output.get('perspective_id')}' references '{pid}'"
                        )


def check_self_review(shared_cld: SharedCLD) -> None:
    """Validate SharedCLD quality before passing to downstream modules.

    Checks:
    - At least 2 nodes
    - At least 1 edge
    - No orphan nodes (every node appears in at least one edge)
    - All edge source/target IDs reference existing nodes
    """
    if len(shared_cld.nodes) < 2:
        raise RuntimeError(
            f"Self-review gate: need >=2 nodes, got {len(shared_cld.nodes)}"
        )
    if len(shared_cld.edges) < 1:
        raise RuntimeError("Self-review gate: need >=1 edge, got 0")

    node_ids = {node.id for node in shared_cld.nodes}
    referenced_ids: set[str] = set()

    for edge in shared_cld.edges:
        if edge.source not in node_ids:
            raise RuntimeError(
                f"Self-review gate: edge source '{edge.source}' not in node set"
            )
        if edge.target not in node_ids:
            raise RuntimeError(
                f"Self-review gate: edge target '{edge.target}' not in node set"
            )
        referenced_ids.add(edge.source)
        referenced_ids.add(edge.target)

    orphans = node_ids - referenced_ids
    if orphans:
        raise RuntimeError(
            f"Self-review gate: orphan nodes detected: {orphans}"
        )
