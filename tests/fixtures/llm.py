"""
LLM 相关 Fixtures

提供 LLM 测试相关的 fixtures。
"""

import pytest


@pytest.fixture
def mock_openai_response(mocker):
    """Mock OpenAI API响应"""
    mock_llm = mocker.Mock()
    mock_llm.complete.return_value.text = "这是一个测试回答。系统科学是研究系统的科学。"
    return mock_llm


@pytest.fixture
def mock_llm(mocker):
    """Mock LLM 对象"""
    mock = mocker.Mock()
    mock.complete.return_value.text = "测试回答"
    mock.stream_complete.return_value = iter(["测试", "回答"])
    return mock
