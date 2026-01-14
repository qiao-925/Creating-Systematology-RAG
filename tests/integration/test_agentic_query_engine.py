"""
AgenticQueryEngine 集成测试

测试任务 5.1：验证 AgenticQueryEngine 功能正常
- API 兼容性测试
- 工具调用测试
- Agent 决策测试
"""

import pytest
from llama_index.core.schema import Document as LlamaDocument

from backend.business.rag_engine.agentic import AgenticQueryEngine
from backend.business.rag_engine.core.engine import ModularQueryEngine
from backend.infrastructure.indexer import IndexManager
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
    manager = IndexManager(collection_name="test_agentic_engine")
    manager.build_index(test_documents)
    return manager


@pytest.fixture
def agentic_engine(index_manager):
    """创建 AgenticQueryEngine 实例"""
    return AgenticQueryEngine(
        index_manager=index_manager,
        similarity_top_k=3,
        enable_markdown_formatting=False,
        max_iterations=3,  # 限制迭代次数以加快测试
        timeout_seconds=30
    )


@pytest.fixture
def modular_engine(index_manager):
    """创建 ModularQueryEngine 实例（用于对比）"""
    return ModularQueryEngine(
        index_manager=index_manager,
        retrieval_strategy="vector",
        similarity_top_k=3,
        enable_markdown_formatting=False
    )


class TestAgenticQueryEngineAPICompatibility:
    """API 兼容性测试"""
    
    def test_query_method_signature(self, agentic_engine):
        """测试 query 方法签名与 ModularQueryEngine 一致"""
        import inspect
        
        agentic_sig = inspect.signature(agentic_engine.query)
        modular_sig = inspect.signature(ModularQueryEngine.query)
        
        # 检查参数名称一致
        agentic_params = list(agentic_sig.parameters.keys())
        modular_params = list(modular_sig.parameters.keys())
        
        assert agentic_params == modular_params, "参数名称应该一致"
    
    def test_query_return_format(self, agentic_engine):
        """测试 query 方法返回格式与 ModularQueryEngine 一致"""
        # 注意：这个测试可能需要真实 LLM，如果 API key 不可用会跳过
        try:
            answer, sources, reasoning, trace = agentic_engine.query(
                "系统科学是什么？",
                collect_trace=False
            )
            
            # 验证返回格式
            assert isinstance(answer, str)
            assert isinstance(sources, list)
            assert reasoning is None or isinstance(reasoning, str)
            assert trace is None or isinstance(trace, dict)
            
            # 验证 sources 格式
            if sources:
                for source in sources:
                    assert isinstance(source, dict)
                    assert 'text' in source or 'metadata' in source
        except Exception as e:
            # 如果没有真实 API key，跳过测试
            if "API" in str(e) or "key" in str(e).lower():
                pytest.skip(f"需要真实 API key: {e}")
            raise
    
    def test_stream_query_method_exists(self, agentic_engine):
        """测试 stream_query 方法存在"""
        assert hasattr(agentic_engine, 'stream_query')
        assert callable(agentic_engine.stream_query)


class TestAgenticQueryEngineFunctionality:
    """功能测试"""
    
    @pytest.mark.skipif(
        not config.DEEPSEEK_API_KEY or config.DEEPSEEK_API_KEY.startswith("test_"),
        reason="需要真实的 DEEPSEEK_API_KEY"
    )
    def test_basic_query(self, agentic_engine):
        """测试基本查询功能"""
        answer, sources, reasoning, trace = agentic_engine.query(
            "系统科学是什么？",
            collect_trace=False
        )
        
        assert answer is not None
        assert len(answer) > 0
        assert isinstance(sources, list)
    
    @pytest.mark.skipif(
        not config.DEEPSEEK_API_KEY or config.DEEPSEEK_API_KEY.startswith("test_"),
        reason="需要真实的 DEEPSEEK_API_KEY"
    )
    def test_query_with_trace(self, agentic_engine):
        """测试查询时收集追踪信息"""
        answer, sources, reasoning, trace = agentic_engine.query(
            "钱学森的贡献是什么？",
            collect_trace=True
        )
        
        assert trace is not None
        assert isinstance(trace, dict)
        # 追踪信息可能包含策略选择、工具调用等信息
    
    def test_fallback_on_error(self, agentic_engine, mocker):
        """测试错误时的降级策略"""
        # Mock Agent 调用失败
        mocker.patch.object(
            agentic_engine,
            '_agent',
            side_effect=Exception("Agent error")
        )
        
        # 应该降级到 ModularQueryEngine
        answer, sources, reasoning, trace = agentic_engine.query(
            "测试问题",
            collect_trace=False
        )
        
        # 降级后应该仍然返回结果
        assert answer is not None
        assert isinstance(sources, list)


class TestAgenticQueryEngineComparison:
    """与 ModularQueryEngine 对比测试"""
    
    @pytest.mark.skipif(
        not config.DEEPSEEK_API_KEY or config.DEEPSEEK_API_KEY.startswith("test_"),
        reason="需要真实的 DEEPSEEK_API_KEY"
    )
    def test_same_query_different_engines(self, agentic_engine, modular_engine):
        """测试相同查询在不同引擎上的行为"""
        question = "系统科学是什么？"
        
        # AgenticQueryEngine 查询
        agentic_answer, agentic_sources, _, _ = agentic_engine.query(
            question,
            collect_trace=False
        )
        
        # ModularQueryEngine 查询
        modular_answer, modular_sources, _ = modular_engine.query(
            question,
            collect_trace=False
        )
        
        # 两种引擎都应该返回答案
        assert agentic_answer is not None
        assert modular_answer is not None
        
        # 返回格式应该一致
        assert isinstance(agentic_sources, list)
        assert isinstance(modular_sources, list)

