"""
研究内核综合判断工具：基于证据账本形成阶段性判断

核心职责：
- synthesize：Agent 在收集足够证据后，调用此工具将判断写入 State

不负责：证据收集、检索执行、反思评估
"""

from __future__ import annotations

from llama_index.core.tools import FunctionTool

from backend.business.research_kernel.state import Confidence, ResearchState
from backend.infrastructure.logger import get_logger

logger = get_logger("research_kernel.tools.synthesis")

_VALID_CONFIDENCE = {c.value for c in Confidence}


def create_synthesis_tool(state: ResearchState) -> FunctionTool:
    """创建综合判断工具

    Args:
        state: 研究状态（工具通过闭包捕获并直接修改）

    Returns:
        FunctionTool 实例
    """

    def synthesize(
        judgment: str,
        confidence: str = "low",
        tensions: str = "",
        next_questions: str = "",
    ) -> str:
        """综合当前证据，形成阶段性判断并写入研究状态。
        judgment 必须是一个判断句（非摘要），明确当前更可能成立的观点。
        confidence 只能是 high/medium/low。
        tensions 是未解决的关键张力或矛盾，多条用竖线分隔。
        next_questions 是值得继续追问的方向，多条用竖线分隔。"""
        judgment = judgment.strip()
        if not judgment:
            return "错误：judgment 不能为空，必须给出一个判断句。"

        if not state.has_evidence:
            return "错误：证据账本为空，无法在没有证据的情况下形成判断。请先使用检索工具收集证据。"

        confidence = confidence.strip().lower()
        if confidence not in _VALID_CONFIDENCE:
            confidence = "low"

        state.current_judgment = judgment
        state.confidence = Confidence(confidence)
        state.unresolved_tensions = _split_items(tensions)
        state.next_questions = _split_items(next_questions)

        logger.info(
            "判断已更新",
            confidence=confidence,
            tension_count=len(state.unresolved_tensions),
            next_q_count=len(state.next_questions),
            evidence_count=state.evidence_count,
        )

        return (
            f"判断已记录（置信度={confidence}）。"
            f"张力={len(state.unresolved_tensions)}条，"
            f"追问方向={len(state.next_questions)}条。"
        )

    tool = FunctionTool.from_defaults(
        fn=synthesize,
        name="synthesize",
        description=synthesize.__doc__,
    )

    logger.debug("综合判断工具已创建")
    return tool


def _split_items(text: str) -> list[str]:
    """将竖线分隔的字符串拆分为列表"""
    if not text or not text.strip():
        return []
    return [item.strip() for item in text.split("|") if item.strip()]
