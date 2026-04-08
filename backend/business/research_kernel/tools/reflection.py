"""
研究内核反思工具：评估证据充足性、识别知识缺口、判断是否继续取证

核心职责：
- reflect：Agent 在取证过程中调用，获取当前研究状态的评估报告

不负责：检索执行、证据记录、判断形成
"""

from __future__ import annotations

from llama_index.core.tools import FunctionTool

from backend.business.research_kernel.state import ResearchState
from backend.infrastructure.logger import get_logger

logger = get_logger("research_kernel.tools.reflection")


def create_reflection_tool(state: ResearchState) -> FunctionTool:
    """创建反思工具

    Args:
        state: 研究状态（工具通过闭包捕获，只读访问）

    Returns:
        FunctionTool 实例
    """

    def reflect() -> str:
        """评估当前研究进度：证据是否充足、是否存在知识缺口、是否应该继续取证。
        调用此工具获取当前研究状态的全面评估报告，帮助决定下一步行动。"""
        lines = [
            "=== 研究状态评估 ===",
            f"原始问题：{state.original_question}",
        ]

        if state.focused_question:
            lines.append(f"聚焦问题：{state.focused_question}")

        lines.append(f"预算使用：{state.current_turn}/{state.budget_turns}轮（剩余{state.budget_remaining}轮）")
        lines.append(f"证据数量：{state.evidence_count}条")

        if state.has_evidence:
            lines.append("\n--- 已收集证据摘要 ---")
            for i, item in enumerate(state.evidence_ledger, 1):
                text_preview = item.text[:120].replace("\n", " ")
                lines.append(
                    f"  [{i}] query={item.query[:60]} | source={item.source_ref} | score={item.score:.2f}"
                    f"\n      {text_preview}..."
                )

            sources = set(item.source_ref for item in state.evidence_ledger if item.source_ref)
            lines.append(f"\n来源覆盖：{len(sources)}个不同来源")
        else:
            lines.append("\n⚠ 尚未收集任何证据。")

        if state.current_judgment:
            lines.append(f"\n当前判断：{state.current_judgment}")
            lines.append(f"置信度：{state.confidence.value}")
        else:
            lines.append("\n⚠ 尚未形成判断。")

        if state.unresolved_tensions:
            lines.append(f"\n未解决张力：")
            for tension in state.unresolved_tensions:
                lines.append(f"  - {tension}")

        if state.is_stopped:
            lines.append(f"\n⚠ 研究已停止（原因={state.stop_reason.value}）")
        elif state.budget_remaining <= 1:
            lines.append("\n⚠ 预算即将耗尽，建议尽快综合判断并收束。")
        elif not state.has_evidence:
            lines.append("\n建议：开始取证，使用 vector_search 或 hybrid_search 收集证据。")
        elif not state.current_judgment:
            lines.append("\n建议：已有证据，可以尝试使用 synthesize 形成阶段性判断。")

        report = "\n".join(lines)
        logger.debug("反思报告已生成", evidence_count=state.evidence_count, turn=state.current_turn)
        return report

    tool = FunctionTool.from_defaults(
        fn=reflect,
        name="reflect",
        description=reflect.__doc__,
    )

    logger.debug("反思工具已创建")
    return tool
