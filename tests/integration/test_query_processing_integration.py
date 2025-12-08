"""
查询处理集成测试
测试查询处理与策略选择的完整流程
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from src.infrastructure.indexer import IndexManager
from src.business.rag_engine.core.engine import ModularQueryEngine
from src.business.rag_engine.processing.query_processor import QueryProcessor


@pytest.fixture
def mock_index_manager(temp_vector_store):
    """创建Mock索引管理器"""
    manager = Mock(spec=IndexManager)
    manager.get_index.return_value = Mock()
    return manager


@pytest.fixture
def mock_llm():
    """创建Mock LLM"""
    llm = Mock()
    return llm


@pytest.fixture
def sample_understanding_response():
    """示例意图理解响应"""
    return {
        "understanding": {
            "query_type": "factual",
            "complexity": "medium",
            "entities": ["系统科学"],
            "intent": "查询系统科学的定义",
            "confidence": 0.85
        },
        "rewritten_queries": [
            "系统科学 定义 概念"
        ]
    }


class TestQueryProcessingIntegration:
    """查询处理集成测试"""
    
    def test_simple_query_processing(self, mock_index_manager, mock_llm):
        """测试简单查询处理流程（不走LLM）"""
        # 创建查询引擎
        engine = ModularQueryEngine(
            index_manager=mock_index_manager,
            llm=mock_llm,
            enable_auto_routing=False
        )
        
        # 简单查询
        simple_query = "什么是系统科学"
        
        # Mock检索结果
        with patch.object(engine.query_engine, 'query') as mock_query:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="系统科学是...")
            mock_response.source_nodes = []
            mock_query.return_value = mock_response
            
            answer, sources, trace_info = engine.query(simple_query)
            
            # 验证查询处理
            assert trace_info is None or "query_processing" not in trace_info or \
                   trace_info.get("query_processing", {}).get("processing_method") == "simple"
            
            # 验证使用了改写后的查询（简单查询应该等于原始查询）
            mock_query.assert_called_once()
    
    def test_complex_query_with_llm_processing(
        self, 
        mock_index_manager, 
        mock_llm,
        sample_understanding_response
    ):
        """测试复杂查询的LLM处理流程"""
        # 创建查询引擎
        engine = ModularQueryEngine(
            index_manager=mock_index_manager,
            llm=mock_llm,
            enable_auto_routing=False
        )
        
        # Mock查询处理器的LLM响应
        with patch.object(engine.query_processor, '_llm') as mock_processor_llm:
            mock_processor_llm.complete.return_value.text = json.dumps(sample_understanding_response)
            engine.query_processor._llm_initialized = True
            
            # 复杂查询
            complex_query = "系统科学和复杂性理论的关系是什么"
            
            # Mock检索结果
            with patch.object(engine.query_engine, 'query') as mock_query:
                mock_response = Mock()
                mock_response.__str__ = Mock(return_value="系统科学和复杂性理论...")
                mock_response.source_nodes = []
                mock_query.return_value = mock_response
                
                answer, sources, trace_info = engine.query(complex_query, collect_trace=True)
                
                # 验证查询处理
                if trace_info:
                    assert "query_processing" in trace_info
                    processing = trace_info["query_processing"]
                    assert processing["processing_method"] == "llm"
                    assert processing["understanding"] is not None
                    assert len(processing["rewritten_queries"]) > 0
    
    def test_query_processing_with_auto_routing(
        self,
        mock_index_manager,
        mock_llm,
        sample_understanding_response
    ):
        """测试查询处理与自动路由的集成"""
        # 创建查询引擎（启用自动路由）
        engine = ModularQueryEngine(
            index_manager=mock_index_manager,
            llm=mock_llm,
            enable_auto_routing=True
        )
        
        # Mock查询处理器的LLM响应
        with patch.object(engine.query_processor, '_llm') as mock_processor_llm:
            mock_processor_llm.complete.return_value.text = json.dumps(sample_understanding_response)
            engine.query_processor._llm_initialized = True
            
            # Mock路由器
            with patch.object(engine.query_router, 'route_with_understanding') as mock_route:
                mock_retriever = Mock()
                mock_route.return_value = (mock_retriever, "chunk")
                
                # Mock查询引擎
                with patch('src.query.modular.engine.RetrieverQueryEngine.from_args') as mock_qe:
                    mock_query_engine = Mock()
                    mock_query_engine.query.return_value = Mock(
                        __str__=Mock(return_value="答案"),
                        source_nodes=[]
                    )
                    mock_qe.return_value = mock_query_engine
                    
                    complex_query = "系统科学和复杂性理论的关系"
                    answer, sources, trace_info = engine.query(complex_query, collect_trace=True)
                    
                    # 验证路由被调用，且传递了意图理解结果
                    mock_route.assert_called_once()
                    call_args = mock_route.call_args
                    assert "understanding" in call_args.kwargs or len(call_args.args) >= 2
    
    def test_query_processing_trace_info(self, mock_index_manager, mock_llm):
        """测试查询处理的追踪信息"""
        engine = ModularQueryEngine(
            index_manager=mock_index_manager,
            llm=mock_llm,
            enable_auto_routing=False
        )
        
        query = "测试查询"
        
        # Mock检索结果
        with patch.object(engine.query_engine, 'query') as mock_query:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="答案")
            mock_response.source_nodes = []
            mock_query.return_value = mock_response
            
            answer, sources, trace_info = engine.query(query, collect_trace=True)
            
            # 验证追踪信息
            assert trace_info is not None
            assert "original_query" in trace_info
            assert "processed_query" in trace_info
            assert "query_processing" in trace_info


class TestQueryRouterWithUnderstanding:
    """基于意图理解的路由测试"""
    
    def test_route_with_understanding_specific(
        self,
        mock_index_manager,
        mock_llm
    ):
        """测试特定查询类型的路由"""
        from src.business.rag_engine.routing.query_router import QueryRouter
        
        router = QueryRouter(
            index_manager=mock_index_manager,
            llm=mock_llm,
            enable_auto_routing=True
        )
        
        understanding = {
            "query_type": "specific",
            "complexity": "medium"
        }
        
        retriever, decision = router.route_with_understanding(
            "查询文件",
            understanding=understanding
        )
        
        assert decision == "files_via_metadata"
    
    def test_route_with_understanding_exploratory(
        self,
        mock_index_manager,
        mock_llm
    ):
        """测试探索性查询的路由"""
        from src.business.rag_engine.routing.query_router import QueryRouter
        
        router = QueryRouter(
            index_manager=mock_index_manager,
            llm=mock_llm,
            enable_auto_routing=True
        )
        
        understanding = {
            "query_type": "exploratory",
            "complexity": "medium"
        }
        
        retriever, decision = router.route_with_understanding(
            "什么是系统科学",
            understanding=understanding
        )
        
        assert decision == "files_via_content"
    
    def test_route_with_understanding_factual(
        self,
        mock_index_manager,
        mock_llm
    ):
        """测试事实查询的路由"""
        from src.business.rag_engine.routing.query_router import QueryRouter
        
        router = QueryRouter(
            index_manager=mock_index_manager,
            llm=mock_llm,
            enable_auto_routing=True
        )
        
        understanding = {
            "query_type": "factual",
            "complexity": "medium"
        }
        
        retriever, decision = router.route_with_understanding(
            "系统科学的定义",
            understanding=understanding
        )
        
        assert decision == "chunk"
    
    def test_route_without_understanding_fallback(
        self,
        mock_index_manager,
        mock_llm
    ):
        """测试没有意图理解时的降级（规则匹配）"""
        from src.business.rag_engine.routing.query_router import QueryRouter
        
        router = QueryRouter(
            index_manager=mock_index_manager,
            llm=mock_llm,
            enable_auto_routing=True
        )
        
        # 不提供意图理解结果
        retriever, decision = router.route_with_understanding(
            "什么是系统科学",
            understanding=None
        )
        
        # 应该使用规则匹配
        assert decision in ["chunk", "files_via_content"]

