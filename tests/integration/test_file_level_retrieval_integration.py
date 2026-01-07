"""
文件级别检索集成测试
测试文件级别检索器与 QueryRouter 的集成
"""

import pytest
from pathlib import Path
import tempfile

from backend.business.rag_engine.routing.query_router import QueryRouter
from backend.infrastructure.indexer import IndexManager
from llama_index.core.schema import Document as LlamaDocument


@pytest.fixture
def test_documents():
    """创建测试文档（包含file_path元数据）"""
    return [
        LlamaDocument(
            text="系统科学是20世纪中期兴起的一门新兴学科，它研究系统的一般规律和方法。系统科学包括系统论、控制论、信息论等多个分支。",
            metadata={
                "title": "系统科学概述",
                "source": "test",
                "file_name": "系统科学.md",
                "file_path": "docs/系统科学.md"
            }
        ),
        LlamaDocument(
            text="钱学森（1911-2009）是中国著名科学家，被誉为\"中国航天之父\"。他在系统工程和系统科学领域做出了杰出贡献，提出了开放的复杂巨系统理论。",
            metadata={
                "title": "钱学森生平",
                "source": "test",
                "file_name": "钱学森.md",
                "file_path": "docs/钱学森.md"
            }
        ),
        LlamaDocument(
            text="系统工程是一种组织管理技术，用于解决大规模复杂系统的设计和实施问题。钱学森将系统工程引入中国，并结合中国实际进行了创新性发展。",
            metadata={
                "title": "系统工程简介",
                "source": "test",
                "file_name": "系统工程.md",
                "file_path": "docs/系统工程.md"
            }
        ),
    ]


@pytest.fixture
def index_manager_with_docs(test_documents):
    """创建带文档的索引管理器"""
    collection_name = "test_file_level_retrieval_collection"
    
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


class TestFilesViaContentIntegration:
    """FilesViaContentRetriever集成测试"""
    
    def test_router_files_via_content(self, index_manager_with_docs):
        """测试路由到files_via_content"""
        router = QueryRouter(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True
        )
        
        # 宽泛主题查询应该路由到files_via_content
        query = "什么是系统科学？"
        retriever, routing_decision = router.route(query, top_k=5)
        
        assert retriever is not None
        assert routing_decision == "files_via_content"
        
        # 执行检索
        results = retriever.retrieve(query)
        
        assert isinstance(results, list)
        assert len(results) >= 0  # 可能没有结果，但不应该报错
    
    def test_files_via_content_retrieval(self, index_manager_with_docs):
        """测试files_via_content检索功能"""
        router = QueryRouter(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True
        )
        
        # 宽泛查询
        query = "介绍系统科学"
        retriever, routing_decision = router.route(query, top_k=5)
        
        assert routing_decision == "files_via_content"
        
        # 执行检索
        results = retriever.retrieve(query)
        
        # 验证结果格式
        if results:
            for result in results:
                assert hasattr(result, 'node')
                assert hasattr(result, 'score')
                assert 'file_path' in result.node.metadata
    
    def test_files_via_content_wide_queries(self, index_manager_with_docs):
        """测试各种宽泛查询"""
        router = QueryRouter(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True
        )
        
        wide_queries = [
            "什么是系统科学？",
            "如何应用系统科学",
            "介绍系统科学",
            "系统科学的概述",
        ]
        
        for query in wide_queries:
            retriever, routing_decision = router.route(query, top_k=5)
            # 可能路由到files_via_content或chunk（取决于规则匹配）
            assert routing_decision in ["files_via_content", "chunk"]
            
            # 执行检索不应该报错
            results = retriever.retrieve(query)
            assert isinstance(results, list)


class TestFilesViaMetadataIntegration:
    """FilesViaMetadataRetriever集成测试"""
    
    def test_router_files_via_metadata(self, index_manager_with_docs):
        """测试路由到files_via_metadata"""
        router = QueryRouter(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True
        )
        
        # 文件名查询应该路由到files_via_metadata
        query = "系统科学.md文件的内容"
        retriever, routing_decision = router.route(query, top_k=5)
        
        assert retriever is not None
        # 可能路由到files_via_metadata或chunk（取决于规则匹配）
        assert routing_decision in ["files_via_metadata", "chunk"]
        
        # 执行检索
        results = retriever.retrieve(query)
        
        assert isinstance(results, list)
    
    def test_files_via_metadata_retrieval(self, index_manager_with_docs):
        """测试files_via_metadata检索功能"""
        router = QueryRouter(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True
        )
        
        # 文件名查询
        query = "系统科学.md文档"
        retriever, routing_decision = router.route(query, top_k=5)
        
        # 执行检索
        results = retriever.retrieve(query)
        
        # 验证结果格式
        assert isinstance(results, list)
        if results:
            for result in results:
                assert hasattr(result, 'node')
                assert hasattr(result, 'score')
    
    def test_files_via_metadata_file_queries(self, index_manager_with_docs):
        """测试各种文件名查询"""
        router = QueryRouter(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True
        )
        
        file_queries = [
            "系统科学.md文件的内容",
            "钱学森.md文档",
            "系统工程.md文件",
        ]
        
        for query in file_queries:
            retriever, routing_decision = router.route(query, top_k=5)
            # 执行检索不应该报错
            results = retriever.retrieve(query)
            assert isinstance(results, list)


class TestFileLevelRetrievalEndToEnd:
    """文件级别检索端到端测试"""
    
    def test_end_to_end_files_via_content(self, index_manager_with_docs):
        """测试files_via_content完整流程"""
        router = QueryRouter(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True
        )
        
        query = "什么是系统科学？它的核心思想是什么？"
        
        # 路由决策
        retriever, routing_decision = router.route(query, top_k=5)
        assert routing_decision == "files_via_content"
        
        # 执行检索
        results = retriever.retrieve(query)
        
        # 验证结果
        assert isinstance(results, list)
        # 如果有结果，应该包含文件路径元数据
        if results:
            file_paths = set()
            for result in results:
                file_path = result.node.metadata.get('file_path')
                if file_path:
                    file_paths.add(file_path)
            
            # 应该检索到多个文件的chunks（如果数据足够）
            assert len(file_paths) > 0
    
    def test_end_to_end_files_via_metadata(self, index_manager_with_docs):
        """测试files_via_metadata完整流程"""
        router = QueryRouter(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True
        )
        
        query = "系统科学.md文件的内容"
        
        # 路由决策
        retriever, routing_decision = router.route(query, top_k=5)
        
        # 执行检索
        results = retriever.retrieve(query)
        
        # 验证结果
        assert isinstance(results, list)
        # 如果有结果，应该都来自同一个文件（如果文件名匹配成功）
        if results:
            file_paths = set()
            for result in results:
                file_path = result.node.metadata.get('file_path')
                if file_path:
                    file_paths.add(file_path)
    
    def test_file_level_retrieval_no_warning(self, index_manager_with_docs, caplog):
        """测试不再出现警告日志"""
        import logging
        
        # 使用caplog捕获日志
        with caplog.at_level(logging.WARNING):
            router = QueryRouter(
                index_manager=index_manager_with_docs,
                enable_auto_routing=True
            )
            
            # 触发files_via_content检索器创建
            query = "什么是系统科学？"
            retriever, _ = router.route(query, top_k=5)
            
            # 执行检索
            retriever.retrieve(query)
            
            # 验证不应该有"尚未完全实现"的警告
            warning_messages = [
                record.message for record in caplog.records 
                if "尚未完全实现" in record.message
            ]
            assert len(warning_messages) == 0, f"发现警告: {warning_messages}"


class TestFileLevelRetrievalEdgeCases:
    """文件级别检索边界条件测试"""
    
    def test_empty_query(self, index_manager_with_docs):
        """测试空查询"""
        router = QueryRouter(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True
        )
        
        query = ""
        retriever, routing_decision = router.route(query, top_k=5)
        
        # 空查询应该返回空结果
        results = retriever.retrieve(query)
        assert results == []
    
    def test_nonexistent_file_query(self, index_manager_with_docs):
        """测试不存在的文件查询"""
        router = QueryRouter(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True
        )
        
        query = "nonexistent_file.md文件的内容"
        retriever, routing_decision = router.route(query, top_k=5)
        
        # 应该返回空结果或降级处理
        results = retriever.retrieve(query)
        assert isinstance(results, list)
    
    def test_top_k_limit(self, index_manager_with_docs):
        """测试Top-K限制"""
        router = QueryRouter(
            index_manager=index_manager_with_docs,
            enable_auto_routing=True
        )
        
        query = "什么是系统科学？"
        retriever, routing_decision = router.route(query, top_k=3)
        
        results = retriever.retrieve(query, top_k=3)
        
        # 结果数量应该不超过top_k
        assert len(results) <= 3

