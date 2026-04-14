"""
评估模块：研究输出质量度量

两层评估：
- RAG 层：RAGAS（已有 RAGASEvaluator）
- 研究输出层：ResearchEvaluator（rule-based + LLM-as-Judge）
"""

from typing import Any

__all__ = ["ResearchEvaluator", "EvaluationResult"]


def __getattr__(name: str) -> Any:
    if name in ("ResearchEvaluator", "EvaluationResult"):
        from backend.infrastructure.evaluation.research_evaluator import (
            ResearchEvaluator,
            EvaluationResult,
        )
        return locals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
