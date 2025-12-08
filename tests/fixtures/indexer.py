"""
索引相关 Fixtures

提供索引管理器、向量存储等测试 fixtures。
"""

import pytest
from pathlib import Path


@pytest.fixture
def temp_vector_store(tmp_path):
    """临时向量存储目录"""
    store_path = tmp_path / "test_vector_store"
    store_path.mkdir()
    return store_path


@pytest.fixture(scope="module")  # 优化：module 级别，减少重复初始化
def prepared_index_manager(tmp_path_factory, sample_documents):
    """准备好的索引管理器（已构建索引）"""
    from src.infrastructure.indexer import IndexManager
    
    # 使用 tmp_path_factory 创建 module 级别的临时目录
    temp_vector_store = tmp_path_factory.mktemp("test_vector_store")
    
    manager = IndexManager(
        collection_name="global_test",
        persist_dir=temp_vector_store
    )
    manager.build_index(sample_documents, show_progress=False)
    
    yield manager
    
    # 清理
    try:
        manager.clear_index()
    except Exception:
        pass


# ==================== 索引管理器工厂 ====================

class IndexManagerFactory:
    """索引管理器工厂"""
    
    @staticmethod
    def create_empty(collection_name: str = "test", persist_dir: Path = None):
        """创建空的索引管理器"""
        from src.infrastructure.indexer import IndexManager
        return IndexManager(
            collection_name=collection_name,
            persist_dir=persist_dir
        )
    
    @staticmethod
    def create_with_documents(documents, collection_name: str = "test", persist_dir: Path = None):
        """创建并构建索引的索引管理器"""
        from src.infrastructure.indexer import IndexManager
        
        manager = IndexManager(
            collection_name=collection_name,
            persist_dir=persist_dir
        )
        manager.build_index(documents, show_progress=False)
        return manager


@pytest.fixture
def index_manager_factory():
    """索引管理器工厂 fixture"""
    return IndexManagerFactory
