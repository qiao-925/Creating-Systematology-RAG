"""
研究输出质量评估器（轻量版）

评估 ResearchOutput 的 5 个维度：
  1. judgment_has_position  — 判断是判断句还是摘要（LLM-as-Judge）
  2. evidence_traceability  — 判断要点可追溯到证据（规则）
  3. tension_identification — 识别了有意义的张力（规则）
  4. convergence_efficiency — 预算利用效率（规则）
  5. next_questions_quality — 后续问题的深度与差异度（LLM-as-Judge）

规则指标同步计算，LLM 指标可选异步执行。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.infrastructure.logger import get_logger

logger = get_logger("evaluation.research")

# ── 泛化张力模板（视为无效张力） ──────────────────────────────

_GENERIC_TENSION_PATTERNS = [
    "需要更多研究",
    "有待进一步验证",
    "尚不清楚",
    "存在争议",
    "有待考证",
]


# ── 评估结果 ──────────────────────────────────────────────────

@dataclass
class EvaluationResult:
    """单次研究输出的评估结果"""
    # 规则指标 (0.0 ~ 1.0)
    evidence_traceability: float = 0.0
    tension_identification: float = 0.0
    convergence_efficiency: float = 0.0

    # LLM 指标 (0.0 ~ 1.0, None = 未评估)
    judgment_has_position: Optional[float] = None
    next_questions_quality: Optional[float] = None

    # 元数据
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def rule_based_score(self) -> float:
        """规则指标加权均分"""
        scores = [self.evidence_traceability, self.tension_identification, self.convergence_efficiency]
        return sum(scores) / len(scores)

    @property
    def overall_score(self) -> Optional[float]:
        """综合评分（含 LLM 指标时才计算）"""
        all_scores = [self.evidence_traceability, self.tension_identification, self.convergence_efficiency]
        if self.judgment_has_position is not None:
            all_scores.append(self.judgment_has_position)
        if self.next_questions_quality is not None:
            all_scores.append(self.next_questions_quality)
        return sum(all_scores) / len(all_scores) if all_scores else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_traceability": self.evidence_traceability,
            "tension_identification": self.tension_identification,
            "convergence_efficiency": self.convergence_efficiency,
            "judgment_has_position": self.judgment_has_position,
            "next_questions_quality": self.next_questions_quality,
            "rule_based_score": round(self.rule_based_score, 3),
            "overall_score": round(self.overall_score, 3) if self.overall_score is not None else None,
            "details": self.details,
        }


# ── 评估器 ────────────────────────────────────────────────────

class ResearchEvaluator:
    """研究输出质量评估器

    Usage:
        evaluator = ResearchEvaluator()
        result = evaluator.evaluate(research_output)          # 规则指标
        result = await evaluator.evaluate_full(output, llm)   # + LLM 指标
    """

    def evaluate(self, output: Any, budget_turns: int = 10) -> EvaluationResult:
        """同步评估规则指标（不需要 LLM）

        Args:
            output: ResearchOutput instance
            budget_turns: 总预算轮次（用于计算收束效率）
        """
        result = EvaluationResult()

        result.evidence_traceability = self._score_evidence_traceability(output)
        result.tension_identification = self._score_tension_identification(output)
        result.convergence_efficiency = self._score_convergence_efficiency(output, budget_turns)

        logger.info(
            "rule_evaluation_complete",
            evidence_traceability=round(result.evidence_traceability, 3),
            tension_identification=round(result.tension_identification, 3),
            convergence_efficiency=round(result.convergence_efficiency, 3),
            rule_based_score=round(result.rule_based_score, 3),
        )
        return result

    async def evaluate_full(
        self, output: Any, llm: Any, budget_turns: int = 10
    ) -> EvaluationResult:
        """完整评估（规则 + LLM 指标）

        Args:
            output: ResearchOutput instance
            llm: LlamaIndex LLM instance for judge calls
            budget_turns: 总预算轮次
        """
        result = self.evaluate(output, budget_turns)

        result.judgment_has_position = await self._judge_has_position(output, llm)
        result.next_questions_quality = await self._judge_next_questions(output, llm)

        logger.info(
            "full_evaluation_complete",
            judgment_has_position=result.judgment_has_position,
            next_questions_quality=result.next_questions_quality,
            overall_score=round(result.overall_score, 3) if result.overall_score else None,
        )
        return result

    # ── 规则指标 ──────────────────────────────────────────────

    def _score_evidence_traceability(self, output: Any) -> float:
        """判断中的关键词是否在证据中出现（4-gram overlap）"""
        judgment = getattr(output, "judgment", "")
        evidence_list = getattr(output, "evidence", [])
        if not judgment or not evidence_list:
            return 0.0

        # 合并所有证据文本
        evidence_text = " ".join(
            getattr(item, "text", "") for item in evidence_list
        )
        if not evidence_text:
            return 0.0

        # 使用 4-gram 字符窗口计算重叠率（适合中文）
        n = 4
        clean_j = judgment.replace(" ", "")
        clean_e = evidence_text.replace(" ", "")
        if len(clean_j) < n:
            return 0.5  # 判断太短

        j_grams = {clean_j[i:i+n] for i in range(len(clean_j) - n + 1)}
        e_grams = {clean_e[i:i+n] for i in range(len(clean_e) - n + 1)}
        if not j_grams:
            return 0.5

        overlap = len(j_grams & e_grams)
        score = overlap / len(j_grams)

        self._detail(output, "evidence_traceability", {
            "judgment_grams": len(j_grams),
            "overlap": overlap,
        })
        return round(min(1.0, score), 3)

    def _score_tension_identification(self, output: Any) -> float:
        """张力字段是否包含有意义的内容"""
        tensions = getattr(output, "tensions", [])
        if not tensions:
            # 无张力：如果 confidence=high 且有证据，可以接受
            confidence = getattr(output, "confidence", None)
            has_evidence = getattr(output, "has_evidence", False)
            if confidence and str(confidence.value) == "high" and has_evidence:
                return 0.7  # 高置信度无张力是合理的
            return 0.0

        # 过滤泛化模板
        meaningful = []
        for t in tensions:
            is_generic = any(pat in t for pat in _GENERIC_TENSION_PATTERNS)
            if not is_generic and len(t.strip()) >= 5:
                meaningful.append(t)

        if not meaningful:
            return 0.2  # 有张力但都是泛化的

        score = min(1.0, len(meaningful) / 2)  # 1-2 条有意义的张力即满分
        self._detail(output, "tension_identification", {
            "total": len(tensions),
            "meaningful": len(meaningful),
        })
        return round(score, 3)

    def _score_convergence_efficiency(self, output: Any, budget_turns: int) -> float:
        """预算利用效率：在合理轮数内收束"""
        turns_used = getattr(output, "turns_used", 0)
        has_evidence = getattr(output, "has_evidence", False)
        stop_reason = getattr(output, "stop_reason", None)

        if turns_used == 0:
            return 0.0

        ratio = turns_used / max(budget_turns, 1)

        # 理想区间：使用 30%-80% 预算
        if 0.3 <= ratio <= 0.8 and has_evidence:
            score = 1.0
        elif ratio < 0.3 and has_evidence:
            score = 0.8  # 快速收束，可能浅尝辄止
        elif ratio > 0.8:
            score = 0.5  # 接近预算耗尽
            if stop_reason and str(stop_reason.value) == "budget_exhausted":
                score = 0.3  # 被迫停止
        else:
            score = 0.4

        self._detail(output, "convergence_efficiency", {
            "turns_used": turns_used,
            "budget_turns": budget_turns,
            "ratio": round(ratio, 2),
        })
        return round(score, 3)

    # ── LLM-as-Judge ──────────────────────────────────────────

    async def _judge_has_position(self, output: Any, llm: Any) -> float:
        """LLM 判断：judgment 是判断句还是摘要"""
        judgment = getattr(output, "judgment", "")
        if not judgment:
            return 0.0

        prompt = (
            "请判断以下文本是一个'判断句'还是'摘要'。\n"
            "判断句：明确表达一个立场或观点，说明什么更可能成立。\n"
            "摘要：仅列举或转述已有材料，没有明确立场。\n\n"
            f"文本：{judgment[:500]}\n\n"
            "只回答一个词：'判断' 或 '摘要'"
        )
        try:
            response = await llm.acomplete(prompt)
            answer = str(response).strip()
            score = 1.0 if "判断" in answer else 0.0
            self._detail(output, "judgment_has_position", {"llm_answer": answer})
            return score
        except Exception as e:
            logger.warning("judge_has_position_failed", error=str(e))
            return 0.5  # 无法判断给中性分

    async def _judge_next_questions(self, output: Any, llm: Any) -> float:
        """LLM 判断：后续问题的质量"""
        questions = getattr(output, "next_questions", [])
        original = getattr(output, "original_question", "") if hasattr(output, "original_question") else ""
        judgment = getattr(output, "judgment", "")

        if not questions:
            return 0.0

        q_list = "\n".join(f"- {q}" for q in questions[:5])
        prompt = (
            "评估以下后续研究问题的质量（0-10分）。\n"
            "高分标准：与原问题有明确关联但角度更深入，具体可操作，不重复已有判断。\n"
            "低分标准：过于宽泛、与原问题无关、或只是重复已有判断。\n\n"
            f"原始问题：{original[:200]}\n"
            f"当前判断：{judgment[:200]}\n"
            f"后续问题：\n{q_list}\n\n"
            "只回答一个 0-10 的整数分数。"
        )
        try:
            response = await llm.acomplete(prompt)
            import re
            match = re.search(r"\d+", str(response).strip())
            raw_score = int(match.group()) if match else 5
            score = min(10, max(0, raw_score)) / 10.0
            self._detail(output, "next_questions_quality", {
                "llm_score": raw_score,
                "question_count": len(questions),
            })
            return round(score, 3)
        except Exception as e:
            logger.warning("judge_next_questions_failed", error=str(e))
            return 0.5

    # ── 内部工具 ──────────────────────────────────────────────

    @staticmethod
    def _detail(output: Any, key: str, data: Dict[str, Any]) -> None:
        """将详情写入 output.metadata（如果可写）"""
        if hasattr(output, "metadata") and isinstance(output.metadata, dict):
            output.metadata.setdefault("evaluation", {})[key] = data
