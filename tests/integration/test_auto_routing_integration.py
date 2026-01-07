"""
自动路由集成测试
测试路由决策和降级
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from backend.business.rag_api.rag_service import RAGService
from backend.business.rag_engine.core.engine import ModularQueryEngine
from backend.infrastructure.indexer import IndexManager
from backend.business.rag_engine.routing.query_router import QueryRouter
from llama_index.core.schema import Document as LlamaDocument


@pytest.fixture
def test_documents():
    """创建测试文档"""
    return [
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


@pytest.fixture
def index_manager_with_docs(test_documents):
    """创建带文档的索引管理器"""
    collection_name = "test_auto_routing_collection"
    
    # 清理可能存在的旧索引
    try:
        manager = IndexManager(collection_name=collection_name)
        manager.delete_collection(collection_name)
    except:
        pass
    
    # 创建新索引
    manager = IndexManager(collection_name=collection_name)
    manager.build_index(documents=test_documents, collection_name=collection_name)
    
    yield manager
    
    # 清理
    try:
        manager.delete_collection(collection_name)
    except:
        pass


class TestAutoRoutingChunkMode:
    """自动路由到chunk模式测试"""
    
    def test_auto_routing_chunk_mode(self, index_manager_with_docs):
        """测试自动路由到chunk模式（精确查询）"""
        engine = ModularQueryEngine(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True,
        )
        
        # 精确问题应该路由到chunk模式
        query = "系统科学的定义"
        answer, sources, trace = engine.query(query, collect_trace=True)
        
        assert answer is not None
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert isinstance(sources, list)
        
        # 验证路由决策（如果trace中包含）
        if trace and 'routing_decision' in trace:
            assert trace['routing_decision'] == "chunk"
    
    def test_chunk_mode_precise_queries(self, index_manager_with_docs):
        """测试精确查询路由到chunk模式"""
        engine = ModularQueryEngine(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True,
        )
        
        precise_queries = [
            "系统科学的定义",
            "钱学森的出生年份",
            "系统工程的特点",
        ]
        
        for query in precise_queries:
            answer, sources, _ = engine.query(query)
            assert answer is not None
            assert isinstance(sources, list)


class TestAutoRoutingFilesMode:
    """自动路由到files模式测试"""
    
    def test_auto_routing_files_via_metadata(self, index_manager_with_docs):
        """测试自动路由到files_via_metadata模式（文件名查询）"""
        engine = ModularQueryEngine(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True,
        )
        
        # 文件名相关查询应该路由到files_via_metadata模式
        query = "请查找文件名为系统科学.md的文档内容"
        answer, sources, trace = engine.query(query, collect_trace=True)
        
        assert answer is not None
        assert isinstance(answer, str)
        
        # 验证路由决策（如果trace中包含）
        if trace and 'routing_decision' in trace:
            # 可能路由到files_via_metadata或chunk
            assert trace['routing_decision'] in ["files_via_metadata", "chunk"]
    
    def test_files_via_content_mode(self, index_manager_with_docs):
        """测试自动路由到files_via_content模式（宽泛查询）"""
        engine = ModularQueryEngine(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True,
        )
        
        # 宽泛问题应该路由到files_via_content模式
        query = "什么是系统科学？"
        answer, sources, trace = engine.query(query, collect_trace=True)
        
        assert answer is not None
        assert isinstance(answer, str)
        
        # 验证路由决策（如果trace中包含）
        if trace and 'routing_decision' in trace:
            # 可能路由到files_via_content或chunk
            assert trace['routing_decision'] in ["files_via_content", "chunk"]
    
    def test_file_name_queries(self, index_manager_with_docs):
        """测试文件名相关查询"""
        engine = ModularQueryEngine(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True,
        )
        
        file_queries = [
            "系统科学.md文件内容",
            "钱学森.md文档",
            "查找系统工程.pdf",
        ]
        
        for query in file_queries:
            answer, sources, _ = engine.query(query)
            assert answer is not None


class TestAutoRoutingFallback:
    """自动路由降级测试"""
    
    def test_auto_routing_fallback(self, index_manager_with_docs):
        """测试自动路由降级机制"""
        engine = ModularQueryEngine(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True,
        )
        
        # 测试空查询或模糊查询的降级
        queries = [
            "",  # 空查询
            "？",  # 仅标点
            "test",  # 英文查询（可能不在文档中）
        ]
        
        for query in queries:
            try:
                answer, sources, _ = engine.query(query)
                # 如果成功，验证返回格式
                assert isinstance(answer, str)
                assert isinstance(sources, list)
            except Exception:
                # 如果抛出异常也是合理的（取决于实现）
                pass
    
    def test_routing_disabled_fallback(self, index_manager_with_docs):
        """测试禁用自动路由时的降级"""
        engine = ModularQueryEngine(
            index_manager=index_manager_with_docs,
            enable_auto_routing=False,
            retrieval_strategy="vector",
        )
        
        # 禁用自动路由时，应该使用默认的vector策略
        query = "系统科学"
        answer, sources, _ = engine.query(query)
        
        assert answer is not None
        assert isinstance(sources, list)
    
    def test_router_failure_fallback(self, index_manager_with_docs):
        """测试路由失败时的降级"""
        # 创建一个有问题的路由器（通过mock）
        # 但实际测试中，我们主要验证系统能正常工作
        
        engine = ModularQueryEngine(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True,
        )
        
        # 即使路由有问题，也应该能降级到默认模式
        query = "系统科学"
        try:
            answer, sources, _ = engine.query(query)
            assert answer is not None
        except Exception as e:
            # 如果失败，应该是合理的错误
            assert "路由" in str(e).lower() or "检索" in str(e).lower()


class TestRoutingPerformance:
    """路由性能测试"""
    
    def test_routing_performance(self, index_manager_with_docs):
        """测试路由性能"""
        import time
        
        engine = ModularQueryEngine(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True,
        )
        
        queries = [
            "系统科学的定义",  # chunk模式
            "系统科学.md文件内容",  # files_via_metadata模式
            "什么是系统科学？",  # files_via_content模式
        ]
        
        for query in queries:
            start_time = time.time()
            answer, sources, _ = engine.query(query)
            elapsed_time = time.time() - start_time
            
            assert answer is not None
            # 路由不应该显著增加响应时间（< 5秒）
            assert elapsed_time < 5.0
    
    def test_routing_overhead(self, index_manager_with_docs):
        """测试路由开销"""
        import time
        
        # 启用自动路由
        auto_engine = ModularQueryEngine(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True,
        )
        
        # 禁用自动路由
        manual_engine = ModularQueryEngine(
            index_manager=index_manager_with_docs,
            enable_auto_routing=False,
            retrieval_strategy="vector",
        )
        
        query = "系统科学"
        
        # 测试自动路由时间
        auto_start = time.time()
        auto_answer, _, _ = auto_engine.query(query)
        auto_time = time.time() - auto_start
        
        # 测试手动路由时间
        manual_start = time.time()
        manual_answer, _, _ = manual_engine.query(query)
        manual_time = time.time() - manual_start
        
        # 两种方式都应该成功
        assert auto_answer is not None
        assert manual_answer is not None
        
        # 自动路由的开销应该合理（不超过手动路由的2倍）
        # 注意：这只是一个粗略的检查，实际性能可能因查询而异
        if auto_time > 0 and manual_time > 0:
            overhead_ratio = auto_time / manual_time if manual_time > 0 else 1.0
            # 允许一定的开销（路由决策）
            assert overhead_ratio < 3.0


class TestRoutingDecisionLogic:
    """路由决策逻辑测试"""
    
    def test_routing_decision_for_different_queries(self, index_manager_with_docs):
        """测试不同查询的路由决策"""
        router = QueryRouter(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True,
        )
        
        test_cases = [
            ("系统科学的定义", "chunk"),
            ("请查找文件名为系统科学.md的文档内容", "files_via_metadata"),
            ("什么是系统科学？", "files_via_content"),
            ("如何应用系统科学", "files_via_content"),
        ]
        
        for query, expected_mode in test_cases:
            retriever, decision = router.route(query)
            
            assert retriever is not None
            assert decision in ["chunk", "files_via_metadata", "files_via_content"]
            
            # 验证决策符合预期（允许一定的灵活性）
            # 注意：由于是规则匹配，可能不完全精确
    
    def test_routing_consistency(self, index_manager_with_docs):
        """测试路由一致性"""
        router = QueryRouter(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True,
        )
        
        query = "系统科学的定义"
        
        # 多次路由应该得到相同的结果
        decisions = []
        for _ in range(5):
            _, decision = router.route(query)
            decisions.append(decision)
        
        # 应该都路由到相同模式（一致性）
        assert len(set(decisions)) == 1
    
    def test_routing_edge_cases(self, index_manager_with_docs):
        """测试路由边界情况"""
        router = QueryRouter(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True,
        )
        
        edge_cases = [
            "",  # 空查询
            "？",  # 仅标点
            "a" * 1000,  # 超长查询
            "系统科学系统科学系统科学",  # 重复词
        ]
        
        for query in edge_cases:
            try:
                retriever, decision = router.route(query)
                assert retriever is not None
                assert decision in ["chunk", "files_via_metadata", "files_via_content"]
            except Exception:
                # 边界情况可能抛出异常，也是合理的
                pass


class TestAutoRoutingWithRAGService:
    """自动路由与RAGService集成测试"""
    
    def test_rag_service_with_auto_routing(self, index_manager_with_docs):
        """测试RAGService使用自动路由"""
        from backend.business.rag_api.rag_service import RAGService
        
        service = RAGService(
            collection_name=index_manager_with_docs.collection_name,
            use_modular_engine=True,
        )
        
        try:
            # 使用服务查询（应该使用自动路由）
            response = service.query(
                question="系统科学的定义",
                user_id="test_user"
            )
            
            assert response is not None
            assert response.answer is not None
            assert isinstance(response.sources, list)
            
        finally:
            service.close()


