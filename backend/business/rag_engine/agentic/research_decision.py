"""
研究决策解析器：处理结构化研究决策块及其解析诊断。
"""

from __future__ import annotations

import json
import re
from typing import Any


_ALLOWED_RESEARCH_ACTIONS = {
    "continue_gathering_evidence",
    "synthesize_answer",
    "stop_due_to_insufficient_evidence",
}
_ALLOWED_STOP_REASONS = {
    "insufficient_evidence",
    "needs_more_evidence",
    "evidence_sufficient_for_now",
}
_ALLOWED_DECISION_PARSE_STATUS = {
    "missing",
    "parsed",
    "parsed_no_valid_fields",
    "invalid_json",
    "provided_directly",
}
_RESEARCH_DECISION_PATTERN = re.compile(
    r"<research_decision>\s*(.*?)\s*</research_decision>",
    re.IGNORECASE | re.DOTALL,
)


def extract_research_decision(answer: str) -> tuple[str, dict[str, Any] | None]:
    """从回答中剥离结构化研究决策块。"""

    cleaned_answer, decision, _ = extract_research_decision_with_trace(answer)
    return cleaned_answer, decision


def extract_research_decision_with_trace(
    answer: str,
) -> tuple[str, dict[str, Any] | None, dict[str, Any]]:
    """从回答中剥离结构化研究决策块，并返回解析诊断信息。"""

    match = _RESEARCH_DECISION_PATTERN.search(answer)
    if not match:
        return answer, None, _build_decision_trace(decision=None)

    decision, parse_status = _safe_parse_research_decision(match.group(1))
    cleaned_answer = _clean_research_decision_block(answer, match)
    return cleaned_answer, decision, _build_decision_trace(
        decision=decision,
        parse_status=parse_status,
    )


def normalize_research_decision(research_decision: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(research_decision, dict):
        return {}

    normalized: dict[str, Any] = {}

    recommended_action = research_decision.get("recommended_action")
    if recommended_action in _ALLOWED_RESEARCH_ACTIONS:
        normalized["recommended_action"] = recommended_action

    stop_reason = research_decision.get("stop_reason")
    if stop_reason in _ALLOWED_STOP_REASONS:
        normalized["stop_reason"] = stop_reason

    _align_action_and_stop_reason(normalized)

    open_tensions = research_decision.get("open_tensions")
    if isinstance(open_tensions, list):
        normalized_tensions = [
            _normalize_text(str(item))
            for item in open_tensions
            if _normalize_text(str(item))
        ]
        normalized["open_tensions"] = normalized_tensions[:2]

    next_question = research_decision.get("next_question")
    if isinstance(next_question, str):
        normalized_question = _normalize_text(next_question)
        if normalized_question:
            normalized["next_question"] = normalized_question

    return normalized


def normalize_decision_trace(
    decision_trace: dict[str, Any] | None,
    normalized_decision: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(decision_trace, dict):
        parse_status = "provided_directly" if normalized_decision else "missing"
        return _build_decision_trace(
            decision=normalized_decision or None,
            parse_status=parse_status,
        )

    parse_status = decision_trace.get("decision_parse_status")
    if parse_status not in _ALLOWED_DECISION_PARSE_STATUS:
        parse_status = "provided_directly" if normalized_decision else "missing"

    fields_present = decision_trace.get("decision_fields_present")
    normalized_fields = _normalize_decision_fields(fields_present)
    if not normalized_fields and normalized_decision:
        normalized_fields = sorted(normalized_decision.keys())

    return {
        "decision_source": "structured_output" if normalized_fields else "heuristic_fallback",
        "decision_parse_status": parse_status,
        "decision_fields_present": normalized_fields,
    }


def build_recommended_action(stop_reason: str) -> str:
    if stop_reason == "insufficient_evidence":
        return "stop_due_to_insufficient_evidence"
    if stop_reason == "needs_more_evidence":
        return "continue_gathering_evidence"
    return "synthesize_answer"


def map_action_to_stop_reason(recommended_action: str) -> str:
    if recommended_action == "stop_due_to_insufficient_evidence":
        return "insufficient_evidence"
    if recommended_action == "continue_gathering_evidence":
        return "needs_more_evidence"
    return "evidence_sufficient_for_now"


def _align_action_and_stop_reason(normalized: dict[str, Any]) -> None:
    recommended_action = normalized.get("recommended_action")
    stop_reason = normalized.get("stop_reason")

    if recommended_action:
        normalized["stop_reason"] = map_action_to_stop_reason(recommended_action)
        return

    if stop_reason:
        normalized["recommended_action"] = build_recommended_action(stop_reason)


def _safe_parse_research_decision(text: str) -> tuple[dict[str, Any] | None, str]:
    text = _strip_markdown_code_fence(text)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None, "invalid_json"

    normalized = normalize_research_decision(parsed)
    if normalized:
        return normalized, "parsed"
    return normalized, "parsed_no_valid_fields"


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _strip_markdown_code_fence(text: str) -> str:
    match = re.fullmatch(r"\s*```(?:json)?\s*(.*?)\s*```\s*", text, re.DOTALL)
    if match:
        return match.group(1)
    return text


def _clean_research_decision_block(answer: str, match: re.Match[str]) -> str:
    cleaned = answer[: match.start()] + answer[match.end() :]
    return cleaned.strip()


def _build_decision_trace(
    *,
    decision: dict[str, Any] | None,
    parse_status: str = "missing",
) -> dict[str, Any]:
    normalized_fields = _normalize_decision_fields(
        sorted(decision.keys()) if isinstance(decision, dict) else []
    )
    return {
        "decision_source": "structured_output" if normalized_fields else "heuristic_fallback",
        "decision_parse_status": parse_status,
        "decision_fields_present": normalized_fields,
    }


def _normalize_decision_fields(fields: Any) -> list[str]:
    if not isinstance(fields, list):
        return []

    normalized_fields = [
        _normalize_text(str(field))
        for field in fields
        if _normalize_text(str(field))
    ]
    return sorted(set(normalized_fields))
