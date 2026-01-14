"""
Agentic RAG 检索工具封装单元测试

测试任务 1.2：验证工具封装功能正常
"""

import pytest
from llama_index.core.schema import Document as LlamaDocument
from llama_index.core.tools import QueryEngineTool

from backend.business.rag_engine.agentic.agent.tools.retrieval_tools import create_retrieval_tools
from backend.infrastructure.indexer import IndexManager
from backend.infrastructure.llms import create_deepseek_llm_for_query
from backend.infrastructure.config import config


@pytest.fixture
def test_documents():
    """创建测试文档"""
    docs = [
        LlamaDocument(
            text="系统科学是20世纪中期兴起的一门新兴学科，它研究系统的一般规律和方法。系统科学包括系统论、控制论、信息论等多个分支。",
            metadata={"title": "系统科学概述", "source": "test", "file_name": "系统科学.md"}
        ),
        LlamaDocument(
            text="钱学森（1911-2009）是中国著名科学家，被誉为\"中国航天之父\"。他在系统工程和系统科学领域做出了杰出贡献，提出了开放的复杂巨系统理论。",
            metadata={"title": "钱学森生平", "source": "test", "file_name": "钱学森.md"}
        ),
        LlamaDocument(
            text="系统工程是一种组织管理技术，用于解决大规模复杂系统的设计和实施问题。钱学森将系统工程引入中国，并结合中国实际进行了创新性发展。",
            metadata={"title": "系统工程简介", "source": "test", "file_name": "系统工程.md"}
        ),
    ]
    return docs


@pytest.fixture
def index_manager(test_documents):
    """创建测试索引"""
    manager = IndexManager(collection_name="test_agentic_tools")
    manager.build_index(test_documents)
    return manager


@pytest.fixture
def llm():
    """创建测试 LLM"""
    return create_deepseek_llm_for_query(
        api_key=config.DEEPSEEK_API_KEY,
        model=config.LLM_MODEL
    )


class TestRetrievalTools:
    """检索工具封装测试"""
    
    def test_create_retrieval_tools_returns_list(self, index_manager, llm):
        """测试创建检索工具返回列表"""
        tools = create_retrieval_tools(
            index_manager=index_manager,
            llm=llm
        )
        
        assert isinstance(tools, list)
        assert len(tools) == 3  # vector, hybrid, multi
    
    def test_tools_are_query_engine_tools(self, index_manager, llm):
        """测试工具是 QueryEngineTool 实例"""
        tools = create_retrieval_tools(
            index_manager=index_manager,
            llm=llm
        )
        
        for tool in tools:
            assert isinstance(tool, QueryEngineTool)
    
    def test_tools_have_correct_names(self, index_manager, llm):
        """测试工具名称正确"""
        tools = create_retrieval_tools(
            index_manager=index_manager,
            llm=llm
        )
        
        tool_names = [tool.metadata.name for tool in tools]
        assert "vector_search" in tool_names
        assert "hybrid_search" in tool_names
        assert "multi_search" in tool_names
    
    def test_tools_have_descriptions(self, index_manager, llm):
        """测试工具有描述信息"""
        tools = create_retrieval_tools(
            index_manager=index_manager,
            llm=llm
        )
        
        for tool in tools:
            assert tool.metadata.description is not None
            assert len(tool.metadata.description) > 0
    
    def test_tools_can_be_called(self, index_manager, llm):
        """测试工具可以调用（需要真实 LLM，可能跳过）"""
        tools = create_retrieval_tools(
            index_manager=index_manager,
            llm=llm
        )
        
        # 测试工具调用接口存在
        for tool in tools:
            assert hasattr(tool, 'call')
            assert callable(tool.call)
    
    def test_tools_with_custom_params(self, index_manager, llm):
        """测试使用自定义参数创建工具"""
        tools = create_retrieval_tools(
            index_manager=index_manager,
            llm=llm,
            similarity_top_k=5,
            similarity_cutoff=0.7,
            enable_rerank=False
        )
        
        assert len(tools) == 3
        for tool in tools:
            assert isinstance(tool, QueryEngineTool)

