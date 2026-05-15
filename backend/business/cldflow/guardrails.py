"""CLDFlow MVP guardrails."""

from __future__ import annotations

from backend.business.cldflow.models import CLDFlowRunContext


def ensure_question_is_valid(question: str) -> str:
    question = question.strip()
    if not question:
        raise ValueError("question cannot be empty")
    return question


def ensure_cld_ready(context: CLDFlowRunContext) -> None:
    if context.shared_cld is None:
        raise RuntimeError("CLD must be ready before synthesis")


def ensure_budget_remaining(context: CLDFlowRunContext) -> None:
    if context.budget_remaining <= 0:
        raise RuntimeError("budget exhausted")
