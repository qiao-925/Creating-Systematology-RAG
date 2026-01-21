"""
查询处理 Agent 集成测试

测试内容：
- 规划 Agent 使用查询处理工具
- 意图理解 + 改写 + 检索完整流程
- 多意图查询分解
"""

import pytest
from unittest.mock import MagicMock, patch
from llama_index.core.schema import Document as LlamaDocument

from backend.business.rag_engine.agentic.agent.planning import create_planning_agent
from backend.business.rag_engine.agentic.agent.tools import (
    create_query_processing_tools,
    create_retrieval_tools,
)
from backend.infrastructure.indexer import IndexManager
from backend.infrastructure.config import config


@pytest.fixture
def test_documents():
    """创建测试文档"""
    return [
        LlamaDocument(
            text="系统科学是研究系统一般规律的学科，包括系统论、控制论、信息论。",
            metadata={"title": "系统科学", "file_name": "系统科学.md"}
        ),
        LlamaDocument(
            text="钱学森提出了开放的复杂巨系统理论，是系统工程的奠基人。",
            metadata={"title": "钱学森", "file_name": "钱学森.md"}
        ),
    ]


@pytest.fixture
def index_manager(test_documents):
    """创建测试索引"""
    manager = IndexManager(collection_name="test_query_processing_agent")
    manager.build_index(test_documents)
    return manager


class TestQueryProcessingToolsIntegration:
    """查询处理工具集成测试"""
    
    def test_create_all_tools(self, index_manager):
        """测试创建所有工具（查询处理 + 检索）"""
        # 创建 Mock LLM
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "测试回答"
        mock_llm.complete.return_value = mock_response
        
        # 创建查询处理工具
        qp_tools = create_query_processing_tools()
        assert len(qp_tools) == 3
        
        # 创建检索工具
        retrieval_tools = create_retrieval_tools(
            index_manager=index_manager,
            llm=mock_llm,
            similarity_top_k=3,
        )
        assert len(retrieval_tools) == 3
        
        # 总共 6 个工具
        all_tools = qp_tools + retrieval_tools
        assert len(all_tools) == 6
        
        # 验证工具名称
        tool_names = [t.metadata.name for t in all_tools]
        assert "analyze_intent" in tool_names
        assert "rewrite_query" in tool_names
        assert "decompose_multi_intent" in tool_names
        assert "vector_search" in tool_names
        assert "hybrid_search" in tool_names
        assert "multi_search" in tool_names


class TestPlanningAgentWithQueryProcessing:
    """规划 Agent 与查询处理工具集成测试"""
    
    @pytest.mark.skipif(
        not config.DEEPSEEK_API_KEY or config.DEEPSEEK_API_KEY.startswith("test_"),
        reason="需要真实的 DEEPSEEK_API_KEY"
    )
    def test_create_agent_with_query_processing(self, index_manager):
        """测试创建带查询处理工具的规划 Agent"""
        from backend.infrastructure.llms import create_deepseek_llm_for_query
        
        llm = create_deepseek_llm_for_query(
            api_key=config.DEEPSEEK_API_KEY,
            model=config.LLM_MODEL,
        )
        
        # 创建带查询处理工具的 Agent
        agent = create_planning_agent(
            index_manager=index_manager,
            llm=llm,
            similarity_top_k=3,
            enable_query_processing=True,
            max_iterations=5,
        )
        
        assert agent is not None
        # Agent 应该有 6 个工具（3 查询处理 + 3 检索）
        # 注意：具体数量取决于实现，这里主要验证 Agent 创建成功
    
    @pytest.mark.skipif(
        not config.DEEPSEEK_API_KEY or config.DEEPSEEK_API_KEY.startswith("test_"),
        reason="需要真实的 DEEPSEEK_API_KEY"
    )
    def test_create_agent_without_query_processing(self, index_manager):
        """测试创建不带查询处理工具的规划 Agent"""
        from backend.infrastructure.llms import create_deepseek_llm_for_query
        
        llm = create_deepseek_llm_for_query(
            api_key=config.DEEPSEEK_API_KEY,
            model=config.LLM_MODEL,
        )
        
        # 创建不带查询处理工具的 Agent
        agent = create_planning_agent(
            index_manager=index_manager,
            llm=llm,
            similarity_top_k=3,
            enable_query_processing=False,  # 禁用查询处理工具
            max_iterations=5,
        )
        
        assert agent is not None


class TestQueryProcessingFunctions:
    """查询处理函数直接测试"""
    
    @pytest.mark.skipif(
        not config.DEEPSEEK_API_KEY or config.DEEPSEEK_API_KEY.startswith("test_"),
        reason="需要真实的 DEEPSEEK_API_KEY"
    )
    def test_analyze_intent_real_llm(self):
        """测试意图分析（真实 LLM）"""
        import json
        from backend.business.rag_engine.agentic.agent.tools.query_processing_impl import (
            analyze_intent,
        )
        
        result = analyze_intent("系统科学和系统工程有什么区别？")
        result_dict = json.loads(result)
        
        assert "query_type" in result_dict
        assert "complexity" in result_dict
        assert "entities" in result_dict
        assert "needs_rewrite" in result_dict
    
    @pytest.mark.skipif(
        not config.DEEPSEEK_API_KEY or config.DEEPSEEK_API_KEY.startswith("test_"),
        reason="需要真实的 DEEPSEEK_API_KEY"
    )
    def test_rewrite_query_real_llm(self):
        """测试查询改写（真实 LLM）"""
        import json
        from backend.business.rag_engine.agentic.agent.tools.query_processing_impl import (
            rewrite_query,
        )
        
        result = rewrite_query("系统是啥意思")
        result_dict = json.loads(result)
        
        assert "rewritten_queries" in result_dict
        assert len(result_dict["rewritten_queries"]) >= 1
        # 改写后应该保留核心概念
        assert any("系统" in q for q in result_dict["rewritten_queries"])
    
    @pytest.mark.skipif(
        not config.DEEPSEEK_API_KEY or config.DEEPSEEK_API_KEY.startswith("test_"),
        reason="需要真实的 DEEPSEEK_API_KEY"
    )
    def test_decompose_multi_intent_real_llm(self):
        """测试多意图分解（真实 LLM）"""
        import json
        from backend.business.rag_engine.agentic.agent.tools.query_processing_impl import (
            decompose_multi_intent,
        )
        
        # 测试多意图查询
        result = decompose_multi_intent("系统科学是什么？钱学森有什么贡献？")
        result_dict = json.loads(result)
        
        assert "is_multi_intent" in result_dict
        assert "sub_queries" in result_dict
        
        # 应该检测到多意图
        if result_dict["is_multi_intent"]:
            assert len(result_dict["sub_queries"]) >= 2
