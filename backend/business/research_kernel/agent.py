"""
研究内核 Agent：基于 LlamaIndex AgentWorkflow 构建研究型 Agent

核心职责：
- 创建 ResearchAgent（AgentWorkflow 包装）
- 注册 5 个工具到 AgentWorkflow
- 配置 LLM、护栏（timeout、max_iterations）
- 运行研究并返回 ResearchOutput

不负责：工具实现细节、状态模型定义、prompt 设计
"""

from __future__ import annotations

from typing import Any, Optional

from llama_index.core.agent.workflow import AgentWorkflow, ReActAgent
from llama_index.core.llms.llm import LLM

from backend.business.research_kernel.prompts.system import RESEARCH_SYSTEM_PROMPT
from backend.business.research_kernel.state import (
    ResearchOutput,
    ResearchState,
    StopReason,
)
from backend.business.research_kernel.tools.evaluate import create_evaluate_tool
from backend.business.research_kernel.tools.evidence import create_evidence_tool
from backend.business.research_kernel.tools.reflection import create_reflection_tool
from backend.business.research_kernel.tools.search import create_search_tools
from backend.business.research_kernel.tools.synthesis import create_synthesis_tool
from backend.infrastructure.indexer import IndexManager
from backend.infrastructure.logger import get_logger

logger = get_logger("research_kernel.agent")

# 默认护栏参数
DEFAULT_BUDGET_TURNS = 10
DEFAULT_MAX_ITERATIONS = 30
DEFAULT_TIMEOUT_SECONDS = 120.0
DEFAULT_SIMILARITY_TOP_K = 5


class ResearchAgent:
    """研究型 Agent：基于 LlamaIndex AgentWorkflow 的证据驱动判断系统"""

    def __init__(
        self,
        index_manager: IndexManager,
        llm: LLM,
        budget_turns: int = DEFAULT_BUDGET_TURNS,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        similarity_top_k: int = DEFAULT_SIMILARITY_TOP_K,
    ):
        """初始化 ResearchAgent

        Args:
            index_manager: 索引管理器（检索工具需要）
            llm: LLM 实例
            budget_turns: 预算轮次上限（record_evidence 消耗轮次）
            max_iterations: AgentWorkflow 最大迭代次数（护栏）
            timeout_seconds: 超时秒数（护栏）
            similarity_top_k: 检索 Top-K
        """
        self._index_manager = index_manager
        self._llm = llm
        self._budget_turns = budget_turns
        self._max_iterations = max_iterations
        self._timeout_seconds = timeout_seconds
        self._similarity_top_k = similarity_top_k

        logger.info(
            "ResearchAgent 初始化",
            budget_turns=budget_turns,
            max_iterations=max_iterations,
            timeout=timeout_seconds,
            top_k=similarity_top_k,
        )

    async def run(self, question: str) -> ResearchOutput:
        """执行研究

        Args:
            question: 用户研究问题

        Returns:
            ResearchOutput 结构化研究结果
        """
        question = question.strip()
        if not question:
            raise ValueError("研究问题不能为空")

        state = ResearchState(
            original_question=question,
            budget_turns=self._budget_turns,
        )

        search_tools = create_search_tools(
            self._index_manager,
            similarity_top_k=self._similarity_top_k,
        )
        evidence_tool = create_evidence_tool(state)
        synthesis_tool = create_synthesis_tool(state)
        reflection_tool = create_reflection_tool(state)

        evaluate_tool = create_evaluate_tool(state, self._budget_turns)
        all_tools = search_tools + [evidence_tool, synthesis_tool, reflection_tool, evaluate_tool]

        agent = ReActAgent(
            name="ResearchAgent",
            description="研究型 Agent，通过取证-综合-判断链路形成研究结论。",
            system_prompt=RESEARCH_SYSTEM_PROMPT,
            tools=all_tools,
            llm=self._llm,
        )

        workflow = AgentWorkflow(
            agents=[agent],
            root_agent="ResearchAgent",
            timeout=self._timeout_seconds,
        )

        logger.info("研究开始", question=question[:80])

        try:
            response = await workflow.run(
                user_msg=question,
                max_iterations=self._max_iterations,
            )
            logger.info(
                "研究完成",
                turns_used=state.current_turn,
                evidence_count=state.evidence_count,
                has_judgment=bool(state.current_judgment),
            )
        except TimeoutError:
            state.stop_reason = StopReason.TIMEOUT
            logger.warning("研究超时", timeout=self._timeout_seconds, turns=state.current_turn)
        except Exception as exc:
            state.stop_reason = StopReason.ERROR
            logger.warning(
                "研究异常，降级产出部分结果",
                error=str(exc),
                turns=state.current_turn,
                evidence_count=state.evidence_count,
            )

        output = ResearchOutput.from_state(state)

        if not output.has_evidence:
            logger.warning("研究完成但无证据", question=question[:80])
        if not state.current_judgment:
            logger.warning("研究完成但无判断", question=question[:80])

        return output

    def run_sync(self, question: str) -> ResearchOutput:
        """同步执行研究（便捷方法）

        使用 ThreadPoolExecutor 在独立线程中创建新事件循环，
        避免在 Streamlit 等已有 asyncio 事件循环的环境中崩溃。
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def _run_in_new_loop():
            return asyncio.run(self.run(question))

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_in_new_loop)
            return future.result(timeout=self._timeout_seconds + 10)
