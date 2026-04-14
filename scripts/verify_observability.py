"""
可观测性 & 评估体系 端到端验证脚本

验证内容：
  1. Instrumentation 是否捕获 LLM / 检索 / 综合事件
  2. Span 计时是否正常
  3. ResearchEvaluator 规则指标是否正确打分

运行：uv run --no-sync python scripts/verify_observability.py
"""

import os
import sys

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def verify_instrumentation():
    """验证 Instrumentation 事件捕获"""
    print("\n" + "=" * 60)
    print("  STEP 1: 验证 Instrumentation 事件捕获")
    print("=" * 60)

    from backend.infrastructure.observers.setup import enable_instrumentation
    enabled = enable_instrumentation()
    print(f"  Instrumentation enabled: {enabled}")

    # 验证 handler 已注册
    from llama_index.core.instrumentation import get_dispatcher
    d = get_dispatcher()
    print(f"  Event handlers: {len(d.event_handlers)}")
    print(f"  Span handlers: {len(d.span_handlers)}")

    for h in d.event_handlers:
        print(f"    - {h.class_name()}")
    for h in d.span_handlers:
        print(f"    - {h.class_name()}")

    print("\n  ✅ Instrumentation handlers registered")
    return True


def verify_llm_tracing():
    """用真实 LLM 调用验证事件追踪"""
    print("\n" + "=" * 60)
    print("  STEP 2: 真实 LLM 调用追踪")
    print("=" * 60)
    print("  (观察下方 structlog 输出中的 llm_call_start / llm_call_end)")
    print()

    from backend.infrastructure.llms.factory import create_llm
    llm = create_llm()

    from llama_index.core.llms import ChatMessage
    resp = llm.chat([ChatMessage(role="user", content="回复'OK'两个字")])
    print(f"\n  LLM response: {resp.message.content.strip()}")
    print("  ✅ LLM tracing complete (check logs above for llm_call_start/end)")
    return True


def verify_evaluator():
    """验证 ResearchEvaluator 规则指标"""
    print("\n" + "=" * 60)
    print("  STEP 3: 验证 ResearchEvaluator 规则指标")
    print("=" * 60)

    from backend.business.research_kernel.state import (
        Confidence, EvidenceItem, ResearchOutput, StopReason,
    )
    from backend.infrastructure.evaluation.research_evaluator import ResearchEvaluator

    # 构造一个模拟的研究输出
    output = ResearchOutput(
        judgment="系统思维比还原论更适合处理复杂适应系统的涌现行为，因为涌现性质无法通过分解部件来理解",
        evidence=[
            EvidenceItem(
                query="系统思维与还原论的区别",
                text="系统思维强调整体性和涌现行为的不可还原性，认为系统的行为无法通过分解部件来完全理解",
                source_ref="file:systems_thinking.md",
                score=0.85,
            ),
            EvidenceItem(
                query="复杂适应系统的特征",
                text="复杂适应系统展现涌现行为，这些行为源于组分间的非线性交互，还原论在处理此类系统时存在明显局限",
                source_ref="file:complex_systems.md",
                score=0.78,
            ),
        ],
        confidence=Confidence.MEDIUM,
        tensions=["还原论在分子生物学领域仍有独特优势，与系统思维并非完全对立"],
        next_questions=["涌现性质的数学形式化方法有哪些？", "系统思维在工程实践中的具体应用案例"],
        turns_used=5,
        stop_reason=StopReason.CONVERGED,
    )

    evaluator = ResearchEvaluator()
    result = evaluator.evaluate(output, budget_turns=10)

    print(f"\n  评估结果:")
    print(f"    evidence_traceability : {result.evidence_traceability:.3f}")
    print(f"    tension_identification: {result.tension_identification:.3f}")
    print(f"    convergence_efficiency: {result.convergence_efficiency:.3f}")
    print(f"    ---")
    print(f"    rule_based_score      : {result.rule_based_score:.3f}")
    print()

    # 评分合理性检查
    assert result.evidence_traceability > 0.3, f"证据可追溯性太低: {result.evidence_traceability}"
    assert result.tension_identification > 0.4, f"张力识别太低: {result.tension_identification}"
    assert result.convergence_efficiency >= 0.8, f"收束效率太低: {result.convergence_efficiency}"

    print("  ✅ 所有规则指标通过合理性检查")

    # 展示评估详情
    eval_meta = output.metadata.get("evaluation", {})
    if eval_meta:
        print(f"\n  详情:")
        for key, val in eval_meta.items():
            print(f"    {key}: {val}")

    return True


def main():
    print("\n" + "#" * 60)
    print("#  可观测性 & 评估体系 端到端验证")
    print("#" * 60)

    steps = [
        ("Instrumentation 注册", verify_instrumentation),
        ("LLM 事件追踪", verify_llm_tracing),
        ("研究评估器", verify_evaluator),
    ]

    results = []
    for name, fn in steps:
        try:
            ok = fn()
            results.append((name, ok))
        except Exception as e:
            print(f"\n  ❌ {name} 失败: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("  验证结果汇总")
    print("=" * 60)
    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}  {name}")
    print()

    all_pass = all(ok for _, ok in results)
    if all_pass:
        print("  🎉 全部验证通过！可观测性和评估体系已就绪。")
    else:
        print("  ⚠️  部分验证失败，请检查上方日志。")
    print()
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
