"""
研究型 trace 组装器：把一次 Agentic 查询收敛成最小研究结构。
"""

from __future__ import annotations

import json
import re
from typing import Any


_UNCERTAINTY_MARKERS = (
    "可能",
    "也许",
    "尚不清楚",
    "无法确定",
    "不确定",
    "仍需",
    "有待",
    "未知",
    "没有找到",
    "缺少",
)
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
_RESEARCH_DECISION_PATTERN = re.compile(
    r"<research_decision>\s*(\{.*?\})\s*</research_decision>",
    re.IGNORECASE | re.DOTALL,
)


def build_research_trace(
    *,
    question: str,
    answer: str,
    sources: list[dict[str, Any]],
    reasoning_content: str | None = None,
    research_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """构建最小研究型结构化结果。

    该结构当前只作为内部 trace 扩展使用，不改变公开返回契约。
    """

    supporting_evidence = _build_supporting_evidence(sources)
    normalized_decision = _normalize_research_decision(research_decision)
    heuristic_open_tensions = _build_open_tensions(answer, supporting_evidence)
    open_tensions = normalized_decision.get("open_tensions") or heuristic_open_tensions
    stop_reason = normalized_decision.get("stop_reason") or _classify_stop_reason(
        supporting_evidence,
        open_tensions,
    )
    recommended_action = normalized_decision.get("recommended_action") or _build_recommended_action(
        stop_reason,
    )
    next_question = normalized_decision.get("next_question") or _build_next_question(
        question,
        stop_reason,
        open_tensions,
    )

    return {
        "current_judgment": _extract_current_judgment(answer, question),
        "supporting_evidence": supporting_evidence,
        "open_tensions": open_tensions,
        "next_question": next_question,
        "stop_reason": stop_reason,
        "recommended_action": recommended_action,
        "has_reasoning_trace": bool(reasoning_content),
    }


def extract_research_decision(answer: str) -> tuple[str, dict[str, Any] | None]:
    """从回答中剥离结构化研究决策块。"""

    match = _RESEARCH_DECISION_PATTERN.search(answer)
    if not match:
        return answer, None

    decision = _safe_parse_research_decision(match.group(1))
    cleaned_answer = _clean_research_decision_block(answer, match)
    return cleaned_answer, decision


def _build_supporting_evidence(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for source in sources[:3]:
        metadata = source.get("metadata") or {}
        file_name = (
            source.get("file_name")
            or metadata.get("file_name")
            or metadata.get("file_path")
            or metadata.get("source")
            or "unknown"
        )
        excerpt = _normalize_text(source.get("text") or "")
        evidence.append(
            {
                "file_name": file_name,
                "score": source.get("score"),
                "excerpt": excerpt[:160] if excerpt else "",
            }
        )
    return evidence


def _build_open_tensions(
    answer: str,
    supporting_evidence: list[dict[str, Any]],
) -> list[str]:
    if not supporting_evidence:
        return ["当前回答缺少可核实来源，无法支撑阶段性判断。"]

    candidate_sentences = re.split(r"[。！？\n]+", _normalize_text(answer))
    tensions = [
        sentence
        for sentence in candidate_sentences
        if sentence and any(marker in sentence for marker in _UNCERTAINTY_MARKERS)
    ]
    return tensions[:2]


def _classify_stop_reason(
    supporting_evidence: list[dict[str, Any]],
    open_tensions: list[str],
) -> str:
    if not supporting_evidence:
        return "insufficient_evidence"
    if open_tensions:
        return "needs_more_evidence"
    return "evidence_sufficient_for_now"


def _build_next_question(
    question: str,
    stop_reason: str,
    open_tensions: list[str],
) -> str:
    if stop_reason == "insufficient_evidence":
        return f"还缺少哪些一手材料或文档，才能回答“{question}”？"
    if stop_reason == "needs_more_evidence":
        tension = open_tensions[0] if open_tensions else question
        return f"要消除“{tension}”这类不确定性，下一步应补什么证据？"
    return "是否存在反例、边界条件或时间条件，会改变当前阶段性判断？"


def _build_recommended_action(stop_reason: str) -> str:
    if stop_reason == "insufficient_evidence":
        return "stop_due_to_insufficient_evidence"
    if stop_reason == "needs_more_evidence":
        return "continue_gathering_evidence"
    return "synthesize_answer"


def _extract_current_judgment(answer: str, question: str) -> str:
    normalized = _normalize_text(answer)
    if not normalized:
        return f"当前还不能对“{question}”形成稳定判断。"

    first_sentence = re.split(r"[。！？\n]+", normalized, maxsplit=1)[0].strip()
    if first_sentence:
        return first_sentence
    return normalized[:120]


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _safe_parse_research_decision(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return _normalize_research_decision(parsed)


def _normalize_research_decision(research_decision: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(research_decision, dict):
        return {}

    normalized: dict[str, Any] = {}

    recommended_action = research_decision.get("recommended_action")
    if recommended_action in _ALLOWED_RESEARCH_ACTIONS:
        normalized["recommended_action"] = recommended_action

    stop_reason = research_decision.get("stop_reason")
    if stop_reason in _ALLOWED_STOP_REASONS:
        normalized["stop_reason"] = stop_reason

    open_tensions = research_decision.get("open_tensions")
    if isinstance(open_tensions, list):
        normalized_tensions = [
            _normalize_text(str(item))
            for item in open_tensions
            if _normalize_text(str(item))
        ]
        if normalized_tensions:
            normalized["open_tensions"] = normalized_tensions[:2]

    next_question = research_decision.get("next_question")
    if isinstance(next_question, str):
        normalized_question = _normalize_text(next_question)
        if normalized_question:
            normalized["next_question"] = normalized_question

    if "stop_reason" not in normalized and "recommended_action" in normalized:
        normalized["stop_reason"] = _map_action_to_stop_reason(normalized["recommended_action"])

    if "recommended_action" not in normalized and "stop_reason" in normalized:
        normalized["recommended_action"] = _build_recommended_action(normalized["stop_reason"])

    return normalized


def _map_action_to_stop_reason(recommended_action: str) -> str:
    if recommended_action == "stop_due_to_insufficient_evidence":
        return "insufficient_evidence"
    if recommended_action == "continue_gathering_evidence":
        return "needs_more_evidence"
    return "evidence_sufficient_for_now"


def _clean_research_decision_block(answer: str, match: re.Match[str]) -> str:
    cleaned = answer[: match.start()] + answer[match.end() :]
    return cleaned.strip()
