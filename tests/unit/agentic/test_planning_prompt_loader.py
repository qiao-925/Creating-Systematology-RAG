from pathlib import Path

from backend.business.rag_engine.agentic.prompts.loader import (
    DEFAULT_PLANNING_PROMPT,
    load_planning_prompt,
)

EXPECTED_RESEARCH_ACTIONS = [
    "continue_gathering_evidence",
    "synthesize_answer",
    "stop_due_to_insufficient_evidence",
]
EXPECTED_RESEARCH_DECISION_FIELDS = [
    "<research_decision>",
    "recommended_action",
    "stop_reason",
    "open_tensions",
    "next_question",
]
EXPECTED_RESEARCH_DECISION_GUARDRAILS = [
    "三者只能选一个",
    "`continue_gathering_evidence`，`stop_reason` 必须为 `needs_more_evidence`",
    "`synthesize_answer`，`stop_reason` 必须为 `evidence_sufficient_for_now`",
    "`stop_due_to_insufficient_evidence`，`stop_reason` 必须为 `insufficient_evidence`",
]


def assert_contains_all_actions(prompt: str) -> None:
    for action in EXPECTED_RESEARCH_ACTIONS:
        assert action in prompt, f"缺少研究动作 '{action}'"


def assert_contains_research_decision_contract(prompt: str) -> None:
    for field in EXPECTED_RESEARCH_DECISION_FIELDS:
        assert field in prompt, f"缺少研究决策契约字段 '{field}'"


def assert_contains_research_decision_guardrails(prompt: str) -> None:
    for guardrail in EXPECTED_RESEARCH_DECISION_GUARDRAILS:
        assert guardrail in prompt, f"缺少研究决策护栏 '{guardrail}'"


def test_loads_prompt_from_default_template_contains_research_actions() -> None:
    prompt = load_planning_prompt()
    assert prompt.strip(), "加载的 Prompt 内容不能为空"
    assert_contains_all_actions(prompt)
    assert_contains_research_decision_contract(prompt)
    assert_contains_research_decision_guardrails(prompt)


def test_missing_template_reverts_to_default_prompt_with_actions(tmp_path: Path) -> None:
    missing_template = tmp_path / "no_template.txt"
    prompt = load_planning_prompt(missing_template)
    assert prompt == DEFAULT_PLANNING_PROMPT
    assert_contains_all_actions(prompt)
    assert_contains_research_decision_contract(prompt)
    assert_contains_research_decision_guardrails(prompt)
