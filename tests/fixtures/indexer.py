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
    from backend.infrastructure.indexer import IndexManager
    
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
        from backend.infrastructure.indexer import IndexManager
        return IndexManager(
            collection_name=collection_name,
            persist_dir=persist_dir
        )
    
    @staticmethod
    def create_with_documents(documents, collection_name: str = "test", persist_dir: Path = None):
        """创建并构建索引的索引管理器"""
        from backend.infrastructure.indexer import IndexManager
        
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


# ==================== Query Engine Mocks ====================

@pytest.fixture
def mock_agentic_query_engine(mocker):
    """Mock AgenticQueryEngine"""
    from backend.business.rag_engine.agentic import AgenticQueryEngine
    
    mock_engine = mocker.Mock(spec=AgenticQueryEngine)
    mock_engine.query.return_value = (
        "Mock答案",
        [{"file_name": "test.md", "content": "测试内容"}],
        None,  # reasoning_content
        {}  # metadata
    )
    
    # Mock stream_query
    async def mock_stream():
        yield {'type': 'token', 'data': 'Mock'}
        yield {'type': 'token', 'data': '答案'}
        yield {'type': 'sources', 'data': [{"file_name": "test.md"}]}
        yield {'type': 'done', 'data': {'answer': 'Mock答案'}}
    
    mock_engine.stream_query = mock_stream
    return mock_engine


@pytest.fixture
def mock_modular_query_engine(mocker):
    """Mock ModularQueryEngine"""
    from backend.business.rag_engine.core.engine import ModularQueryEngine
    
    mock_engine = mocker.Mock(spec=ModularQueryEngine)
    mock_engine.query.return_value = (
        "Mock答案",
        [{"file_name": "test.md", "content": "测试内容"}],
        None,  # reasoning_content
        {}  # metadata
    )
    
    # Mock stream_query
    async def mock_stream(query):
        yield {'type': 'token', 'data': 'Mock'}
        yield {'type': 'token', 'data': '答案'}
        yield {'type': 'sources', 'data': [{"file_name": "test.md"}]}
        yield {'type': 'done', 'data': {'answer': 'Mock答案'}}
    
    mock_engine.stream_query = mock_stream
    return mock_engine
