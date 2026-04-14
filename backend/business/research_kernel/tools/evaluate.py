"""
研究内核评估工具：运行时评估当前判断质量，提供改进建议

核心职责：
- evaluate_judgment：Agent 在 synthesize 后调用，获取规则指标分数 + 可执行改进建议

不负责：LLM-as-Judge 评估（运行时只用零延迟规则指标）、证据收集、判断形成
"""

from __future__ import annotations

from llama_index.core.tools import FunctionTool

from backend.business.research_kernel.state import ResearchOutput, ResearchState
from backend.infrastructure.evaluation.research_evaluator import (
    EvaluationResult,
    ResearchEvaluator,
)
from backend.infrastructure.logger import get_logger

logger = get_logger("research_kernel.tools.evaluate")

# 改进建议阈值
_THRESHOLDS = {
    "evidence_traceability": 0.15,
    "tension_identification": 0.3,
    "convergence_efficiency": 0.5,
}


def create_evaluate_tool(state: ResearchState, budget_turns: int) -> FunctionTool:
    """创建评估工具

    Args:
        state: 研究状态（只读访问，构造临时 ResearchOutput）
        budget_turns: 总预算轮次（传给评估器计算收束效率）

    Returns:
        FunctionTool 实例
    """
    evaluator = ResearchEvaluator()

    def evaluate_judgment() -> str:
        """评估当前判断的质量：证据可追溯性、张力识别、收束效率。
        在 synthesize 后调用此工具，获取评估分数和改进建议。
        如果分数不理想且预算允许，可以继续取证或修正判断后再次评估。"""
        if not state.current_judgment:
            return "⚠ 尚未形成判断，请先调用 synthesize 工具。"

        output = ResearchOutput.from_state(state)
        result = evaluator.evaluate(output, budget_turns=budget_turns)

        report = _format_report(result, state)

        logger.info(
            "运行时评估完成",
            evidence_traceability=round(result.evidence_traceability, 3),
            tension_identification=round(result.tension_identification, 3),
            convergence_efficiency=round(result.convergence_efficiency, 3),
            rule_based_score=round(result.rule_based_score, 3),
            budget_remaining=state.budget_remaining,
        )

        return report

    tool = FunctionTool.from_defaults(
        fn=evaluate_judgment,
        name="evaluate_judgment",
        description=evaluate_judgment.__doc__,
    )

    logger.debug("评估工具已创建")
    return tool


def _format_report(result: EvaluationResult, state: ResearchState) -> str:
    """将评估结果格式化为 Agent 可读的报告 + 改进建议"""
    lines = ["=== 判断质量评估 ==="]

    # 分数 + 状态标记
    metrics = [
        ("证据可追溯性", result.evidence_traceability, _THRESHOLDS["evidence_traceability"]),
        ("张力识别", result.tension_identification, _THRESHOLDS["tension_identification"]),
        ("收束效率", result.convergence_efficiency, _THRESHOLDS["convergence_efficiency"]),
    ]

    for name, score, threshold in metrics:
        mark = "✓" if score >= threshold else "⚠"
        lines.append(f"{name}: {score:.2f} {mark}")

    lines.append(f"综合规则分: {result.rule_based_score:.2f}")
    lines.append(f"剩余预算: {state.budget_remaining}轮")

    # 改进建议
    suggestions = _generate_suggestions(result, state)
    if suggestions:
        lines.append("\n改进建议:")
        for s in suggestions:
            lines.append(f"- {s}")
    else:
        lines.append("\n✓ 各项指标达标，可以结束研究。")

    return "\n".join(lines)


def _generate_suggestions(result: EvaluationResult, state: ResearchState) -> list[str]:
    """基于评估分数和当前状态生成可执行改进建议"""
    suggestions: list[str] = []

    if result.evidence_traceability < _THRESHOLDS["evidence_traceability"]:
        suggestions.append(
            "证据可追溯性偏低：判断中的关键表述与证据文本重叠不足。"
            "尝试在判断中更直接引用证据原文中的关键术语，"
            "或补充与判断更贴切的证据。"
        )

    if result.tension_identification < _THRESHOLDS["tension_identification"]:
        if not state.unresolved_tensions:
            suggestions.append(
                "未识别到张力：好的研究应揭示证据间的矛盾或限制条件。"
                "重新审视已有证据，识别不同观点的分歧点。"
            )
        else:
            suggestions.append(
                "张力表述过于泛化：避免'有待进一步研究'等模板，"
                "改为具体描述哪些证据之间存在什么样的冲突。"
            )

    if result.convergence_efficiency < _THRESHOLDS["convergence_efficiency"]:
        if state.budget_remaining == 0:
            suggestions.append(
                "预算已耗尽但效率偏低：考虑在下次研究中更早形成判断。"
            )

    return suggestions
