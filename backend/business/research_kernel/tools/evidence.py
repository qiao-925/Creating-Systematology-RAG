"""
研究内核证据记录工具：将检索结果写入 State 的证据账本

核心职责：
- record_evidence：Agent 判断某条检索结果有价值后，调用此工具将其记录到证据账本

不负责：检索执行、判断形成、反思评估
"""

from __future__ import annotations

from llama_index.core.tools import FunctionTool

from backend.business.research_kernel.state import EvidenceItem, ResearchState
from backend.infrastructure.logger import get_logger

logger = get_logger("research_kernel.tools.evidence")


def create_evidence_tool(state: ResearchState) -> FunctionTool:
    """创建证据记录工具

    Args:
        state: 研究状态（工具通过闭包捕获并直接修改）

    Returns:
        FunctionTool 实例
    """

    def record_evidence(
        query: str,
        text: str,
        source_ref: str = "",
        score: float = 0.0,
    ) -> str:
        """记录一条证据到证据账本。
        当你从检索结果中发现对研究问题有价值的信息时，使用此工具记录。
        每条证据应包含：获取时使用的查询、证据文本、来源标注和相关度分数。"""
        query = query.strip()
        text = text.strip()
        if not query or not text:
            return "错误：query 和 text 不能为空。"

        if state.is_stopped or state.budget_remaining == 0:
            logger.warning(
                "预算已耗尽，拒绝记录证据",
                turn=state.current_turn,
                budget=state.budget_turns,
                stop_reason=str(state.stop_reason),
            )
            return (
                f"预算已耗尽（{state.current_turn}/{state.budget_turns}），"
                f"无法继续记录证据。请调用 synthesize 生成最终判断。"
            )

        score = max(0.0, min(1.0, score))

        item = EvidenceItem(
            query=query,
            text=text,
            source_ref=source_ref,
            score=score,
        )
        state.record_evidence(item)
        state.increment_turn()

        logger.info(
            "证据已记录",
            evidence_count=state.evidence_count,
            turn=state.current_turn,
            source_ref=source_ref,
        )

        return (
            f"证据已记录（第{state.evidence_count}条）。"
            f"当前轮次={state.current_turn}/{state.budget_turns}，"
            f"剩余预算={state.budget_remaining}轮。"
        )

    tool = FunctionTool.from_defaults(
        fn=record_evidence,
        name="record_evidence",
        description=record_evidence.__doc__,
    )

    logger.debug("证据记录工具已创建")
    return tool
