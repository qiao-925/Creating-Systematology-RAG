"""[LEGACY] V1 ResearchKernel 冒烟测试。新版请看 test_research_agent.py。"""

from types import SimpleNamespace

import pytest

from backend.business.research_kernel import ResearchKernel

pytestmark = pytest.mark.legacy


class SmokeQueryEngine:
    def __init__(self):
        self._responses = {
            "系统科学为什么适合作为研究型 Agent 的知识底座？": (
                "系统科学强调结构、关系和边界分析，这使它天然适合作为研究型判断的证据框架。",
                [
                    {
                        "text": "系统科学强调结构、关系和边界分析。",
                        "score": 0.95,
                        "metadata": {"file_name": "systems.md"},
                        "file_name": "systems.md",
                        "node_id": "node-1",
                    }
                ],
                None,
                None,
            ),
            "系统科学为什么适合作为研究型 Agent 的知识底座的关键依据是什么？": (
                "关键依据在于它不仅描述事实，还能帮助组织复杂问题中的因果、层级和约束。",
                [
                    {
                        "text": "系统科学能组织复杂问题中的因果、层级和约束。",
                        "score": 0.92,
                        "metadata": {"file_name": "evidence.md"},
                        "file_name": "evidence.md",
                        "node_id": "node-2",
                    }
                ],
                None,
                None,
            ),
        }

    def query(self, question: str, collect_trace: bool = False):
        default = (
            "边界证据显示，这个判断仍需结合具体场景校验。",
            [
                {
                    "text": "判断仍需结合具体场景校验。",
                    "score": 0.88,
                    "metadata": {"file_name": "limits.md"},
                    "file_name": "limits.md",
                    "node_id": "node-3",
                }
            ],
            None,
            {"collect_trace": collect_trace},
        )
        return self._responses.get(question, default)


class SmokeLLM:
    def complete(self, prompt: str):
        if "已用轮数：1" in prompt:
            text = """{
              "judgment": "现有证据说明系统科学具备成为研究型 Agent 知识底座的潜力，但还需要补一轮边界证据。",
              "confidence": "low",
              "next_questions": ["系统科学作为知识底座的边界、限制或反例是什么？"],
              "should_continue": true
            }"""
        else:
            text = """{
              "judgment": "阶段性判断是：系统科学适合作为研究型 Agent 的知识底座，因为它提供了组织复杂问题、比较证据和识别边界的框架，而不是只堆积材料。",
              "confidence": "medium",
              "next_questions": ["哪些具体场景最能验证这一判断？"],
              "should_continue": false
            }"""
        return SimpleNamespace(text=text)


@pytest.mark.fast
def test_research_smoke_returns_non_empty_judgment():
    kernel = ResearchKernel(query_engine=SmokeQueryEngine(), llm=SmokeLLM())

    result = kernel.run("系统科学为什么适合作为研究型 Agent 的知识底座？", budget_turns=3)

    assert result.judgment
    assert result.turns_used == 2
    assert "systems.md" in " ".join(result.evidence_refs)
