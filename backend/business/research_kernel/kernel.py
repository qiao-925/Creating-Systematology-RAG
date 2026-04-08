"""[DEPRECATED] V1 循环式研究内核，已被 agent.py (AgentWorkflow) 替代。

保留原因：向后兼容旧测试。新代码请使用：
    from backend.business.research_kernel.agent import ResearchAgent
    from backend.business.research_kernel.state import ResearchOutput
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from backend.business.rag_api.models import QueryRequest, RAGResponse
from backend.business.rag_api.rag_service import RAGService
from backend.business.rag_api.rag_service_query import execute_query
from backend.infrastructure.llms import create_llm
from backend.infrastructure.logger import get_logger

logger = get_logger("research_kernel")


@dataclass(slots=True)
class ResearchResult:
    question: str
    judgment: str
    evidence_refs: list[str]
    confidence: str
    next_questions: list[str]
    turns_used: int


@dataclass(slots=True)
class _EvidenceItem:
    query: str
    answer: str
    refs: list[str] = field(default_factory=list)


class ResearchKernel:
    """Single-agent MVP research loop."""

    def __init__(self, query_engine: Any | None = None, llm: Any | None = None):
        self._query_engine = query_engine
        self._llm = llm
        self._rag_service: Optional[RAGService] = None

    def run(self, question: str, budget_turns: int = 5) -> ResearchResult:
        normalized_question = question.strip()
        if not normalized_question:
            raise ValueError("question must not be empty")

        max_turns = max(1, budget_turns)
        pending_queries = self._plan_initial_queries(normalized_question, max_turns)
        evidence_items: list[_EvidenceItem] = []
        analysis = self._fallback_analysis(
            question=normalized_question,
            evidence_items=evidence_items,
            turns_used=0,
            budget_turns=max_turns,
            pending_queries=pending_queries,
        )
        turns_used = 0

        while pending_queries and turns_used < max_turns:
            current_query = pending_queries.pop(0)
            response = self._execute_research_query(current_query)
            evidence_items.append(
                _EvidenceItem(
                    query=current_query,
                    answer=response.answer,
                    refs=self._collect_refs(response),
                )
            )
            turns_used += 1

            analysis = self._synthesize(
                question=normalized_question,
                evidence_items=evidence_items,
                turns_used=turns_used,
                budget_turns=max_turns,
                pending_queries=pending_queries,
            )

            if not analysis["should_continue"]:
                break

            for next_query in analysis["next_questions"]:
                if turns_used + len(pending_queries) >= max_turns:
                    break
                if next_query not in pending_queries:
                    pending_queries.append(next_query)

        evidence_refs = _dedupe_preserve_order(
            ref for item in evidence_items for ref in item.refs if ref
        )
        return ResearchResult(
            question=normalized_question,
            judgment=analysis["judgment"],
            evidence_refs=evidence_refs,
            confidence=analysis["confidence"],
            next_questions=analysis["next_questions"],
            turns_used=turns_used,
        )

    @property
    def query_engine(self) -> Any:
        if self._query_engine is None:
            self._rag_service = RAGService(use_agentic_rag=False)
            self._query_engine = self._rag_service.modular_query_engine
        return self._query_engine

    @property
    def llm(self) -> Any:
        if self._llm is None:
            self._llm = create_llm()
        return self._llm

    def _plan_initial_queries(self, question: str, budget_turns: int) -> list[str]:
        base = question.rstrip("。！？?! ")
        planned = [
            question,
            f"{base}的关键依据是什么？",
            f"{base}的边界、限制或反例是什么？",
        ]
        return _dedupe_preserve_order(planned)[: min(3, budget_turns)]

    def _execute_research_query(self, question: str) -> RAGResponse:
        logger.info("research kernel query", question=question)
        request = QueryRequest(question=question)
        return execute_query(self.query_engine, request, collect_trace=False)

    def _collect_refs(self, response: RAGResponse) -> list[str]:
        refs: list[str] = []
        for source in response.sources:
            ref = _normalize_ref(source)
            if ref:
                refs.append(ref)
        return _dedupe_preserve_order(refs)

    def _synthesize(
        self,
        question: str,
        evidence_items: list[_EvidenceItem],
        turns_used: int,
        budget_turns: int,
        pending_queries: list[str],
    ) -> dict[str, Any]:
        try:
            prompt = self._build_synthesis_prompt(
                question=question,
                evidence_items=evidence_items,
                turns_used=turns_used,
                budget_turns=budget_turns,
                pending_queries=pending_queries,
            )
            response = self.llm.complete(prompt)
            parsed = _extract_json_payload(getattr(response, "text", str(response)))
            return _normalize_analysis(parsed, pending_queries, turns_used, budget_turns)
        except Exception as exc:
            logger.warning("research synthesis fallback", error=str(exc))
            return self._fallback_analysis(
                question=question,
                evidence_items=evidence_items,
                turns_used=turns_used,
                budget_turns=budget_turns,
                pending_queries=pending_queries,
            )

    def _build_synthesis_prompt(
        self,
        question: str,
        evidence_items: list[_EvidenceItem],
        turns_used: int,
        budget_turns: int,
        pending_queries: list[str],
    ) -> str:
        evidence_lines = []
        for index, item in enumerate(evidence_items, start=1):
            refs = " | ".join(item.refs[:3]) if item.refs else "no-ref"
            answer = item.answer.strip().replace("\n", " ")[:240]
            evidence_lines.append(
                f"{index}. query={item.query}\nrefs={refs}\nanswer={answer}"
            )
        pending = " | ".join(pending_queries[:2]) if pending_queries else "none"
        evidence_block = "\n\n".join(evidence_lines) if evidence_lines else "none"
        return f"""你是研究型 Agent 的研究内核。

目标问题：{question}
已用轮数：{turns_used}
总预算：{budget_turns}
待处理查询：{pending}

请基于下面证据给出“阶段性判断”，不要写成材料摘要：
{evidence_block}

要求：
1. judgment 必须是一个判断句，明确当前更可能成立的观点。
2. confidence 只能是 high / medium / low。
3. next_questions 最多 2 个，且只保留真正有助于继续取证的问题。
4. should_continue 只有在预算未耗尽且继续取证有明显价值时才为 true。

只返回 JSON：
{{
  "judgment": "阶段性判断",
  "confidence": "medium",
  "next_questions": ["问题1", "问题2"],
  "should_continue": false
}}
"""

    def _fallback_analysis(
        self,
        question: str,
        evidence_items: list[_EvidenceItem],
        turns_used: int,
        budget_turns: int,
        pending_queries: list[str],
    ) -> dict[str, Any]:
        evidence_refs = [ref for item in evidence_items for ref in item.refs]
        if not evidence_items:
            judgment = f"围绕“{question}”尚未取得可用证据，当前不能形成判断。"
            confidence = "low"
        else:
            latest_answer = evidence_items[-1].answer.strip().replace("\n", " ")
            latest_answer = latest_answer[:180] if latest_answer else "证据内容不足"
            judgment = f"基于当前证据，关于“{question}”的阶段性判断是：{latest_answer}"
            confidence = "medium" if len(evidence_refs) >= 2 else "low"

        should_continue = (
            turns_used < budget_turns
            and confidence == "low"
            and bool(pending_queries)
        )
        return {
            "judgment": judgment,
            "confidence": confidence,
            "next_questions": pending_queries[:2],
            "should_continue": should_continue,
        }


def _extract_json_payload(text: str) -> dict[str, Any]:
    normalized = text.strip()
    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", normalized, re.DOTALL)
    if fenced_match:
        normalized = fenced_match.group(1)
    else:
        brace_match = re.search(r"\{.*\}", normalized, re.DOTALL)
        if brace_match:
            normalized = brace_match.group(0)
    return json.loads(normalized)


def _normalize_analysis(
    payload: dict[str, Any],
    pending_queries: list[str],
    turns_used: int,
    budget_turns: int,
) -> dict[str, Any]:
    confidence = str(payload.get("confidence", "low")).lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"

    next_questions = [
        str(item).strip()
        for item in payload.get("next_questions", [])
        if str(item).strip()
    ][:2]
    should_continue = bool(payload.get("should_continue"))
    if turns_used >= budget_turns or not next_questions and not pending_queries:
        should_continue = False

    judgment = str(payload.get("judgment", "")).strip()
    if not judgment:
        raise ValueError("empty judgment")

    return {
        "judgment": judgment,
        "confidence": confidence,
        "next_questions": next_questions or pending_queries[:2],
        "should_continue": should_continue,
    }


def _normalize_ref(source: Any) -> str:
    file_name = getattr(source, "file_name", None) or source.metadata.get("file_name")
    file_path = source.metadata.get("file_path")
    node_id = getattr(source, "node_id", None)
    if file_name:
        return f"file:{file_name}"
    if file_path:
        return f"path:{file_path}"
    if node_id:
        return f"node:{node_id}"
    text = getattr(source, "text", "").strip().replace("\n", " ")
    return f"snippet:{text[:80]}" if text else ""


def _dedupe_preserve_order(values: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
