"""
查询引擎模块单元测试
"""

import pytest
from src.query_engine import (
    QueryEngine,
    SimpleQueryEngine,
    format_sources
)


class TestQueryEngine:
    """查询引擎测试（使用Mock）"""
    
    @pytest.fixture
    def mock_query_engine(self, temp_vector_store, sample_documents, mocker):
        """创建Mock的查询引擎"""
        from src.indexer import IndexManager
        
        # 创建索引
        index_manager = IndexManager(
            collection_name="query_test",
            persist_dir=temp_vector_store,
            chunk_size=256
        )
        index_manager.build_index(sample_documents, show_progress=False)
        
        # Mock OpenAI LLM
        mock_llm = mocker.Mock()
        mock_response = mocker.Mock()
        mock_response.__str__ = lambda self: "系统科学是研究系统的一般规律和方法的科学。[1]"
        mock_response.source_nodes = []
        mock_llm.complete.return_value = mock_response
        
        mocker.patch('src.query_engine.OpenAI', return_value=mock_llm)
        
        return QueryEngine(index_manager)
    
    def test_query_engine_initialization(self, mock_query_engine):
        """测试查询引擎初始化"""
        assert mock_query_engine is not None
        assert mock_query_engine.query_engine is not None
    
    def test_query_returns_answer_and_sources(self, mock_query_engine, mocker):
        """测试查询返回答案和来源"""
        # Mock query方法的返回值
        mock_response = mocker.Mock()
        mock_response.__str__ = lambda self: "测试答案"
        
        # Mock source nodes
        mock_node = mocker.Mock()
        mock_node.node.text = "测试来源文本"
        mock_node.node.metadata = {"title": "测试文档"}
        mock_node.score = 0.95
        
        mock_response.source_nodes = [mock_node]
        mock_query_engine.query_engine.query = mocker.Mock(return_value=mock_response)
        
        answer, sources = mock_query_engine.query("测试问题")
        
        assert isinstance(answer, str)
        assert isinstance(sources, list)
        assert len(sources) > 0
    
    def test_query_with_no_sources(self, mock_query_engine, mocker):
        """测试没有引用来源的情况"""
        mock_response = mocker.Mock()
        mock_response.__str__ = lambda self: "测试答案"
        mock_response.source_nodes = []
        
        mock_query_engine.query_engine.query = mocker.Mock(return_value=mock_response)
        
        answer, sources = mock_query_engine.query("测试问题")
        
        assert isinstance(answer, str)
        assert isinstance(sources, list)
        assert len(sources) == 0


class TestSimpleQueryEngine:
    """简单查询引擎测试"""
    
    @pytest.fixture
    def mock_simple_engine(self, temp_vector_store, sample_documents, mocker):
        """创建Mock的简单查询引擎"""
        from src.indexer import IndexManager
        
        index_manager = IndexManager(
            collection_name="simple_test",
            persist_dir=temp_vector_store
        )
        index_manager.build_index(sample_documents, show_progress=False)
        
        # Mock OpenAI
        mock_llm = mocker.Mock()
        mock_response = mocker.Mock()
        mock_response.__str__ = lambda self: "简单答案"
        mock_llm.complete.return_value = mock_response
        
        mocker.patch('src.query_engine.OpenAI', return_value=mock_llm)
        
        return SimpleQueryEngine(index_manager)
    
    def test_simple_query_returns_string(self, mock_simple_engine, mocker):
        """测试简单查询返回字符串"""
        mock_response = mocker.Mock()
        mock_response.__str__ = lambda self: "测试回答"
        mock_simple_engine.query_engine.query = mocker.Mock(return_value=mock_response)
        
        answer = mock_simple_engine.query("测试问题")
        
        assert isinstance(answer, str)
        assert len(answer) > 0


class TestFormatSources:
    """测试引用来源格式化"""
    
    def test_format_empty_sources(self):
        """测试格式化空来源列表"""
        result = format_sources([])
        assert "无引用来源" in result
    
    def test_format_sources_with_data(self):
        """测试格式化有数据的来源"""
        sources = [
            {
                'index': 1,
                'text': '这是第一个引用来源的内容。' * 10,
                'score': 0.95,
                'metadata': {'title': '文档1', 'file_name': 'doc1.md'}
            },
            {
                'index': 2,
                'text': '这是第二个引用来源。',
                'score': 0.85,
                'metadata': {'url': 'https://example.com'}
            }
        ]
        
        result = format_sources(sources)
        
        assert "引用来源" in result
        assert "[1]" in result
        assert "[2]" in result
        assert "文档1" in result or "doc1.md" in result
        assert "相似度" in result
    
    def test_format_sources_without_score(self):
        """测试格式化没有分数的来源"""
        sources = [
            {
                'index': 1,
                'text': '测试内容',
                'score': None,
                'metadata': {'title': '测试'}
            }
        ]
        
        result = format_sources(sources)
        assert result is not None
        assert "[1]" in result


# ==================== 需要真实API的测试 ====================

@pytest.mark.slow
@pytest.mark.requires_real_api
class TestQueryEngineWithRealAPI:
    """使用真实API的查询引擎测试（需要DEEPSEEK_API_KEY）"""
    
    @pytest.fixture
    def real_query_engine(self, temp_vector_store, sample_documents):
        """创建真实的查询引擎（需要API密钥）"""
        from src.indexer import IndexManager
        
        index_manager = IndexManager(
            collection_name="real_api_test",
            persist_dir=temp_vector_store
        )
        index_manager.build_index(sample_documents, show_progress=False)
        
        return QueryEngine(index_manager)
    
    def test_real_query(self, real_query_engine):
        """测试真实的查询（需要API）"""
        question = "什么是系统科学？"
        answer, sources = real_query_engine.query(question)
        
        # 基本验证
        assert isinstance(answer, str)
        assert len(answer) > 10
        assert isinstance(sources, list)

