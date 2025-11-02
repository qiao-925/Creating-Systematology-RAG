"""
QueryRouter模块单元测试
测试路由决策逻辑和降级机制
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.routers.query_router import QueryRouter
from src.indexer import IndexManager


class TestQueryRouter:
    """QueryRouter测试"""
    
    @pytest.fixture
    def mock_index_manager(self):
        """创建Mock IndexManager"""
        mock_manager = Mock(spec=IndexManager)
        mock_index = Mock()
        mock_retriever = Mock()
        mock_index.as_retriever.return_value = mock_retriever
        mock_manager.get_index.return_value = mock_index
        return mock_manager
    
    def test_query_router_init(self, mock_index_manager):
        """测试QueryRouter初始化"""
        router = QueryRouter(
            index_manager=mock_index_manager,
            enable_auto_routing=True
        )
        
        assert router.index_manager == mock_index_manager
        assert router.enable_auto_routing is True
        assert router._chunk_retriever is None
    
    def test_route_to_chunk_mode(self, mock_index_manager):
        """测试路由到chunk模式"""
        router = QueryRouter(
            index_manager=mock_index_manager,
            enable_auto_routing=True
        )
        
        # 精确查询应该路由到chunk模式（默认）
        query = "系统科学的定义"
        
        retriever, routing_decision = router.route(query)
        
        assert retriever is not None
        assert routing_decision == "chunk"
    
    def test_route_to_files_via_metadata(self, mock_index_manager):
        """测试路由到files_via_metadata模式"""
        router = QueryRouter(
            index_manager=mock_index_manager,
            enable_auto_routing=True
        )
        
        # 文件名查询应该路由到metadata模式
        query = "请查找文件名为system_science.pdf的文档内容"
        
        retriever, routing_decision = router.route(query)
        
        assert retriever is not None
        assert routing_decision == "files_via_metadata"
    
    def test_route_to_files_via_content(self, mock_index_manager):
        """测试路由到files_via_content模式"""
        router = QueryRouter(
            index_manager=mock_index_manager,
            enable_auto_routing=True
        )
        
        # 宽泛主题查询应该路由到content模式
        query = "什么是系统科学？"
        
        retriever, routing_decision = router.route(query)
        
        assert retriever is not None
        assert routing_decision == "files_via_content"
    
    def test_routing_decision_logic(self, mock_index_manager):
        """测试路由决策逻辑"""
        router = QueryRouter(
            index_manager=mock_index_manager,
            enable_auto_routing=True
        )
        
        test_cases = [
            # (query, expected_decision)
            ("系统科学的定义", "chunk"),  # 精确问题，默认chunk
            ("system_science.pdf文件内容", "files_via_metadata"),  # 文件名
            ("什么是系统科学？", "files_via_content"),  # 宽泛主题查询
            ("如何应用系统科学", "files_via_content"),  # 如何开头
        ]
        
        for query, expected_decision in test_cases:
            _, routing_decision = router.route(query)
            assert routing_decision == expected_decision, f"Query: {query}"
    
    def test_fallback_mechanism(self, mock_index_manager):
        """测试降级机制"""
        router = QueryRouter(
            index_manager=mock_index_manager,
            enable_auto_routing=True
        )
        
        # 测试空查询
        query = ""
        retriever, routing_decision = router.route(query)
        
        # 降级到chunk模式
        assert retriever is not None
        assert routing_decision == "chunk"
    
    def test_disable_auto_routing(self, mock_index_manager):
        """测试禁用自动路由"""
        router = QueryRouter(
            index_manager=mock_index_manager,
            enable_auto_routing=False
        )
        
        # 无论什么查询都应该返回chunk模式
        query = "什么是系统科学？"
        retriever, routing_decision = router.route(query)
        
        assert retriever is not None
        assert routing_decision == "chunk"
    
    def test_analyze_query_file_keywords(self, mock_index_manager):
        """测试文件名关键词识别"""
        router = QueryRouter(
            index_manager=mock_index_manager,
            enable_auto_routing=True
        )
        
        file_queries = [
            "system_science.pdf文件",
            "文档.md的内容",
            "test.py文件内容"
        ]
        
        for query in file_queries:
            decision = router._analyze_query(query)
            # 包含文件名关键词且包含"的"、"内容"等，应该路由到metadata
            if "的" in query or "内容" in query:
                assert decision == "files_via_metadata"
    
    def test_analyze_query_broad_indicators(self, mock_index_manager):
        """测试宽泛查询指标识别"""
        router = QueryRouter(
            index_manager=mock_index_manager,
            enable_auto_routing=True
        )
        
        broad_queries = [
            "什么是系统科学",
            "如何应用控制论",
            "介绍一下信息论",
            "总结系统科学的发展"
        ]
        
        for query in broad_queries:
            decision = router._analyze_query(query)
            assert decision == "files_via_content"
    
    def test_get_retriever_caching(self, mock_index_manager):
        """测试检索器缓存"""
        router = QueryRouter(
            index_manager=mock_index_manager,
            enable_auto_routing=True
        )
        
        # 第一次获取
        retriever1 = router._get_chunk_retriever(top_k=5)
        
        # 第二次获取应该返回缓存
        retriever2 = router._get_chunk_retriever(top_k=5)
        
        assert retriever1 is retriever2
        # 验证只调用了一次get_index
        assert mock_index_manager.get_index.call_count == 1
    
    def test_query_router_error_handling(self, mock_index_manager):
        """测试错误处理"""
        router = QueryRouter(
            index_manager=mock_index_manager,
            enable_auto_routing=True
        )
        
        # 测试异常查询（如None）
        try:
            retriever, decision = router.route(None)
            # 如果路由成功，验证返回值
            assert retriever is not None
            assert decision in ["chunk", "files_via_metadata", "files_via_content"]
        except (TypeError, AttributeError):
            # 预期的异常类型（None作为查询可能引发异常）
            pass

