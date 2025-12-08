"""
索引构建模块单元测试
"""

import pytest
from pathlib import Path
from llama_index.core import Document
from src.infrastructure.indexer import IndexManager


@pytest.mark.fast
class TestIndexManager:
    """索引管理器测试"""
    
    @pytest.fixture
    def temp_index_manager(self, temp_vector_store):
        """创建临时索引管理器"""
        return IndexManager(
            collection_name="test_collection",
            persist_dir=temp_vector_store,
            chunk_size=256,
            chunk_overlap=20
        )
    
    def test_initialization(self, temp_index_manager):
        """测试初始化"""
        assert temp_index_manager is not None
        assert temp_index_manager.collection_name == "test_collection"
        assert temp_index_manager.chunk_size == 256
        assert temp_index_manager.chunk_overlap == 20
    
    def test_build_index_with_documents(self, temp_index_manager, sample_documents):
        """测试使用文档构建索引"""
        index = temp_index_manager.build_index(sample_documents, show_progress=False)
        
        assert index is not None
        
        # 验证索引统计
        stats = temp_index_manager.get_stats()
        assert stats['document_count'] > 0
        assert stats['collection_name'] == 'test_collection'
    
    def test_build_index_empty_documents(self, temp_index_manager):
        """测试使用空文档列表"""
        index = temp_index_manager.build_index([], show_progress=False)
        
        assert index is not None  # 应该返回索引对象
    
    def test_get_index(self, temp_index_manager, sample_documents):
        """测试获取索引"""
        # 先构建索引
        temp_index_manager.build_index(sample_documents, show_progress=False)
        
        # 获取索引
        index = temp_index_manager.get_index()
        assert index is not None
    
    def test_get_index_before_build(self, temp_index_manager):
        """测试在构建前获取索引"""
        # 即使没有构建，也应该返回索引对象（可能是空的）
        index = temp_index_manager.get_index()
        assert index is not None
    
    def test_get_stats(self, temp_index_manager):
        """测试获取统计信息"""
        stats = temp_index_manager.get_stats()
        
        assert isinstance(stats, dict)
        assert 'collection_name' in stats
        assert 'document_count' in stats
        assert 'embedding_model' in stats
    
    def test_clear_index(self, temp_index_manager, sample_documents):
        """测试清空索引"""
        # 先构建索引
        temp_index_manager.build_index(sample_documents, show_progress=False)
        stats_before = temp_index_manager.get_stats()
        assert stats_before['document_count'] > 0
        
        # 清空索引
        temp_index_manager.clear_index()
        
        # 验证已清空
        stats_after = temp_index_manager.get_stats()
        assert stats_after['document_count'] == 0
    
    def test_search_functionality(self, temp_index_manager, sample_documents):
        """测试搜索功能"""
        temp_index_manager.build_index(sample_documents, show_progress=False)
        
        results = temp_index_manager.search("系统科学", top_k=2)
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # 验证结果格式
        for result in results:
            assert 'text' in result
            assert 'score' in result
            assert 'metadata' in result
            assert isinstance(result['score'], (int, float))
    
    def test_search_with_different_top_k(self, temp_index_manager, sample_documents):
        """测试不同的top_k值"""
        temp_index_manager.build_index(sample_documents, show_progress=False)
        
        results_3 = temp_index_manager.search("科学", top_k=3)
        results_1 = temp_index_manager.search("科学", top_k=1)
        
        assert len(results_1) <= 1
        assert len(results_3) <= 3
    
    def test_incremental_indexing(self, temp_index_manager, sample_documents):
        """测试增量索引"""
        # 第一次构建
        temp_index_manager.build_index(sample_documents[:2], show_progress=False)
        stats1 = temp_index_manager.get_stats()
        count1 = stats1['document_count']
        
        # 增量添加
        temp_index_manager.build_index(sample_documents[2:], show_progress=False)
        stats2 = temp_index_manager.get_stats()
        count2 = stats2['document_count']
        
        # 文档数量应该增加
        assert count2 > count1


@pytest.mark.fast
@pytest.mark.parametrize("chunk_size,chunk_overlap", [
    (512, 50),
    (1024, 100),
    (256, 20),
])
def test_different_chunk_parameters(chunk_size, chunk_overlap, temp_vector_store, sample_documents):
    """参数化测试：不同的分块参数"""
    manager = IndexManager(
        collection_name=f"test_chunk_{chunk_size}",
        persist_dir=temp_vector_store,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    index = manager.build_index(sample_documents, show_progress=False)
    
    assert index is not None
    assert manager.chunk_size == chunk_size
    assert manager.chunk_overlap == chunk_overlap

