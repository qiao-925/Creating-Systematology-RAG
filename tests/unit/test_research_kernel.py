"""[LEGACY] V1 ResearchKernel 测试。新版请看 test_research_agent.py。"""

import pytest
from types import SimpleNamespace

from backend.business.research_kernel import ResearchKernel, ResearchResult

pytestmark = pytest.mark.legacy


class FakeQueryEngine:
    def query(self, question: str, collect_trace: bool = False):
        answer = f"{question} 的证据表明，该主题存在明确的定义与适用边界。"
        sources = [
            {
                "text": f"{question} 证据片段",
                "score": 0.91,
                "metadata": {"file_name": "research-notes.md"},
                "file_name": "research-notes.md",
                "node_id": f"node-{abs(hash(question)) % 1000}",
            }
        ]
        return answer, sources, None, {"collect_trace": collect_trace}


class FakeLLM:
    def complete(self, prompt: str):
        if "已用轮数：1" in prompt:
            text = """{
              "judgment": "当前证据已经表明该问题可以形成初步判断，但还需要补一轮边界证据。",
              "confidence": "low",
              "next_questions": ["补充该判断的边界条件与反例"],
              "should_continue": true
            }"""
        else:
            text = """{
              "judgment": "当前证据支持一个阶段性判断：核心结论成立，但适用范围受边界条件约束。",
              "confidence": "medium",
              "next_questions": ["哪些条件会推翻当前判断？"],
              "should_continue": false
            }"""
        return SimpleNamespace(text=text)


def test_research_kernel_is_instantiable():
    kernel = ResearchKernel()
    assert isinstance(kernel, ResearchKernel)


def test_run_returns_research_result_type():
    kernel = ResearchKernel(query_engine=FakeQueryEngine(), llm=FakeLLM())
    result = kernel.run("什么是研究型 Agent MVP？", budget_turns=3)

    assert isinstance(result, ResearchResult)


def test_run_returns_non_empty_judgment():
    kernel = ResearchKernel(query_engine=FakeQueryEngine(), llm=FakeLLM())
    result = kernel.run("为什么研究型 Agent 需要主动收束？", budget_turns=3)

    assert result.judgment.strip()
    assert result.turns_used <= 3
    assert result.evidence_refs
