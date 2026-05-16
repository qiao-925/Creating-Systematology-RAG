"""CLDFlow MVP guardrails."""

from __future__ import annotations

from backend.core.models import RunContext


def ensure_question_is_valid(question: str) -> str:
    question = question.strip()
    if not question:
        raise ValueError("question cannot be empty")
    return question


def ensure_cld_ready(shared_cld: object | None) -> None:
    if shared_cld is None:
        raise RuntimeError("CLD must be ready before synthesis")


def ensure_budget_remaining(context: RunContext) -> None:
    remaining = context.budget_tokens - context.tokens_used
    if remaining <= 0:
        raise RuntimeError("budget exhausted")
