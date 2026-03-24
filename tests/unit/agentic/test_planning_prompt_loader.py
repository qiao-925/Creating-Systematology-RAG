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


def assert_contains_all_actions(prompt: str) -> None:
    for action in EXPECTED_RESEARCH_ACTIONS:
        assert action in prompt, f"缺少研究动作 '{action}'"


def test_loads_prompt_from_default_template_contains_research_actions() -> None:
    prompt = load_planning_prompt()
    assert prompt.strip(), "加载的 Prompt 内容不能为空"
    assert_contains_all_actions(prompt)


def test_missing_template_reverts_to_default_prompt_with_actions(tmp_path: Path) -> None:
    missing_template = tmp_path / "no_template.txt"
    prompt = load_planning_prompt(missing_template)
    assert prompt == DEFAULT_PLANNING_PROMPT
    assert_contains_all_actions(prompt)
