"""
研究内核 E2E 验证：fixture-driven 可复用闭环

验证链路：
    YAML fixture → ResearchAgent.run() → ResearchOutput → Evaluator.evaluate() → 断言阈值
    （Instrumentation 全程自动追踪）

运行方式：
    make e2e-smoke           # 1 题快速冒烟
    make e2e-regression      # 多题质量回归
    uv run --no-sync pytest tests/e2e/test_research_e2e.py -v -m e2e  # 直接 pytest
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from backend.business.research_kernel.agent import ResearchAgent
from backend.business.research_kernel.state import ResearchOutput
from backend.infrastructure.evaluation.research_evaluator import (
    EvaluationResult,
    ResearchEvaluator,
)
from backend.infrastructure.logger import get_logger

logger = get_logger("e2e.research")

# ── Fixture 加载 ──────────────────────────────────────────────

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixtures(suite: str) -> List[Dict[str, Any]]:
    """从 YAML 加载测试 fixture"""
    path = FIXTURES_DIR / "research_questions.yml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get(suite, [])


# ── 共享资源 ──────────────────────────────────────────────────

@pytest.fixture(scope="module")
def llm():
    """创建 LLM 实例（模块级复用）"""
    from backend.infrastructure.llms.factory import create_llm
    return create_llm()


@pytest.fixture(scope="module")
def index_manager():
    """创建 IndexManager（连接 Chroma Cloud，模块级复用）"""
    from backend.infrastructure.indexer import IndexManager
    return IndexManager()


@pytest.fixture(scope="module")
def evaluator():
    return ResearchEvaluator()


@pytest.fixture(scope="module", autouse=True)
def _enable_instrumentation():
    """确保 Instrumentation 在 E2E 测试期间启用"""
    from backend.infrastructure.observers.setup import enable_instrumentation
    enable_instrumentation()


# ── 测试参数化 ────────────────────────────────────────────────

def _smoke_params():
    fixtures = _load_fixtures("smoke")
    return [pytest.param(f, id=f["question"][:30]) for f in fixtures]


def _regression_params():
    fixtures = _load_fixtures("regression")
    return [pytest.param(f, id=f["question"][:30]) for f in fixtures]


# ── 核心验证逻辑 ──────────────────────────────────────────────

_MAX_RETRIES = 2


def _run_and_evaluate(
    fixture: Dict[str, Any],
    index_manager: Any,
    llm: Any,
    evaluator: ResearchEvaluator,
) -> tuple[ResearchOutput, EvaluationResult]:
    """执行研究 + 评估，返回原始输出和评估结果

    对瞬态 API 错误（DeepSeek 断连、网络超时等）自动重试一次。
    """
    question = fixture["question"]
    budget = fixture.get("budget_turns", 10)

    last_error = None
    for attempt in range(1, _MAX_RETRIES + 1):
        agent = ResearchAgent(
            index_manager=index_manager,
            llm=llm,
            budget_turns=budget,
            max_iterations=budget * 3,
            timeout_seconds=300.0,  # HF embedding ~6s/call, 需要足够时间
        )

        logger.info("e2e_research_start", question=question[:50], budget=budget, attempt=attempt)
        try:
            output = agent.run_sync(question)
        except Exception as exc:
            last_error = exc
            logger.warning("e2e_research_transient_error", error=str(exc)[:120], attempt=attempt)
            if attempt < _MAX_RETRIES:
                import time
                time.sleep(5)
                continue
            pytest.fail(f"研究执行失败（重试 {_MAX_RETRIES} 次）: {exc}")

        logger.info(
            "e2e_research_done",
            turns=output.turns_used,
            evidence=len(output.evidence),
            confidence=output.confidence.value,
            stop_reason=output.stop_reason.value,
            judgment_len=len(output.judgment),
        )

        result = evaluator.evaluate(output, budget_turns=budget)
        return output, result

    # unreachable, but satisfy type checker
    pytest.fail(f"研究执行失败: {last_error}")


def _assert_thresholds(
    result: EvaluationResult,
    thresholds: Dict[str, float],
    question: str,
):
    """断言评估分数 >= 阈值"""
    failures = []
    for metric, threshold in thresholds.items():
        actual = getattr(result, metric, None)
        if actual is None:
            continue
        if actual < threshold:
            failures.append(f"{metric}: {actual:.3f} < {threshold:.3f}")

    if failures:
        msg = f"质量阈值未达标 [{question[:40]}]:\n  " + "\n  ".join(failures)
        pytest.fail(msg)


# ── 测试用例 ──────────────────────────────────────────────────

@pytest.mark.e2e
@pytest.mark.requires_api
class TestResearchSmoke:
    """冒烟测试：1 题验证管线不崩 + 基本质量"""

    @pytest.mark.parametrize("fixture", _smoke_params())
    def test_smoke(self, fixture, index_manager, llm, evaluator):
        output, result = _run_and_evaluate(fixture, index_manager, llm, evaluator)

        # 基本完整性
        assert output.judgment, "应产出判断"
        assert output.turns_used > 0, "应消耗至少 1 轮"

        # 质量阈值
        _assert_thresholds(result, fixture["thresholds"], fixture["question"])

        # 打印摘要
        print(f"\n{'─'*50}")
        print(f"问题: {fixture['question']}")
        print(f"判断: {output.judgment[:100]}...")
        print(f"证据: {len(output.evidence)} 条")
        print(f"置信: {output.confidence.value}")
        print(f"轮次: {output.turns_used}/{fixture.get('budget_turns', 10)}")
        print(f"评分: {result.to_dict()}")
        print(f"{'─'*50}")


@pytest.mark.e2e
@pytest.mark.requires_api
class TestResearchRegression:
    """回归测试：多题验证质量不退化"""

    @pytest.mark.parametrize("fixture", _regression_params())
    def test_regression(self, fixture, index_manager, llm, evaluator):
        output, result = _run_and_evaluate(fixture, index_manager, llm, evaluator)

        assert output.judgment, "应产出判断"
        _assert_thresholds(result, fixture["thresholds"], fixture["question"])

        logger.info(
            "e2e_regression_result",
            question=fixture["question"][:40],
            rule_based_score=round(result.rule_based_score, 3),
            evidence_count=len(output.evidence),
            confidence=output.confidence.value,
        )
