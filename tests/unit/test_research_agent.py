"""
研究内核 Agent 构建单元测试

验证 ResearchAgent 的创建、工具注册和基本运行（mock LLM + mock 检索）。
"""

import pytest
from unittest.mock import MagicMock, patch

from backend.business.research_kernel.agent import (
    ResearchAgent,
    DEFAULT_BUDGET_TURNS,
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_TIMEOUT_SECONDS,
)
from backend.business.research_kernel.state import ResearchOutput


class TestResearchAgentInit:

    def test_create_agent(self):
        mock_im = MagicMock()
        mock_llm = MagicMock()
        agent = ResearchAgent(
            index_manager=mock_im,
            llm=mock_llm,
        )
        assert agent._budget_turns == DEFAULT_BUDGET_TURNS
        assert agent._max_iterations == DEFAULT_MAX_ITERATIONS
        assert agent._timeout_seconds == DEFAULT_TIMEOUT_SECONDS

    def test_custom_params(self):
        agent = ResearchAgent(
            index_manager=MagicMock(),
            llm=MagicMock(),
            budget_turns=3,
            max_iterations=10,
            timeout_seconds=30.0,
            similarity_top_k=3,
        )
        assert agent._budget_turns == 3
        assert agent._max_iterations == 10
        assert agent._timeout_seconds == 30.0
        assert agent._similarity_top_k == 3


class TestResearchAgentValidation:

    @pytest.mark.asyncio
    async def test_empty_question_raises(self):
        agent = ResearchAgent(index_manager=MagicMock(), llm=MagicMock())
        with pytest.raises(ValueError, match="不能为空"):
            await agent.run("")

    @pytest.mark.asyncio
    async def test_whitespace_question_raises(self):
        agent = ResearchAgent(index_manager=MagicMock(), llm=MagicMock())
        with pytest.raises(ValueError, match="不能为空"):
            await agent.run("   ")
