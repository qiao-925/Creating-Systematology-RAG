"""
RAGService单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.business.services import RAGService, RAGResponse, IndexResult, ChatResponse


class TestRAGService:
    """RAGService单元测试"""
    
    @pytest.fixture
    def mock_index_manager(self):
        """Mock IndexManager"""
        with patch('src.business.services.rag_service.IndexManager') as mock:
            yield mock
    
    @pytest.fixture
    def mock_query_engine(self):
        """Mock QueryEngine"""
        with patch('src.business.services.rag_service.QueryEngine') as mock:
            yield mock
    
    @pytest.fixture
    def mock_chat_manager(self):
        """Mock ChatManager"""
        with patch('src.business.services.rag_service.ChatManager') as mock:
            yield mock
    
    def test_rag_service_init(self):
        """测试RAGService初始化"""
        service = RAGService(
            collection_name="test_collection",
            similarity_top_k=5,
            enable_debug=True
        )
        
        assert service.collection_name == "test_collection"
        assert service.similarity_top_k == 5
        assert service.enable_debug is True
        assert service._index_manager is None  # 延迟加载
        assert service._query_engine is None
        assert service._chat_manager is None
    
    def test_query_success(self, mock_index_manager, mock_query_engine):
        """测试查询成功"""
        # Mock QueryEngine.query返回值
        mock_query_instance = mock_query_engine.return_value
        mock_query_instance.query.return_value = (
            "这是测试答案",
            [{"file_name": "test.md", "content": "测试内容"}]
        )
        
        service = RAGService(collection_name="test")
        response = service.query("测试问题", user_id="user1")
        
        assert isinstance(response, RAGResponse)
        assert response.answer == "这是测试答案"
        assert len(response.sources) == 1
        assert response.sources[0]["file_name"] == "test.md"
        assert response.metadata["user_id"] == "user1"
        assert response.metadata["question"] == "测试问题"
        assert response.has_sources is True
    
    def test_query_no_sources(self, mock_index_manager, mock_query_engine):
        """测试查询无来源"""
        mock_query_instance = mock_query_engine.return_value
        mock_query_instance.query.return_value = ("答案", [])
        
        service = RAGService()
        response = service.query("问题")
        
        assert response.has_sources is False
        assert len(response.sources) == 0
    
    def test_build_index_local_success(self, mock_index_manager):
        """测试本地索引构建成功"""
        # Mock IndexManager
        mock_instance = mock_index_manager.return_value
        
        # Mock DataSource
        with patch('src.business.services.rag_service.LocalDataSource') as mock_ds:
            mock_ds_instance = mock_ds.return_value
            mock_ds_instance.load_documents.return_value = [
                Mock(text="doc1"), Mock(text="doc2"), Mock(text="doc3")
            ]
            
            service = RAGService(collection_name="test")
            result = service.build_index("./test_data")
            
            assert isinstance(result, IndexResult)
            assert result.success is True
            assert result.doc_count == 3
            assert result.collection_name == "test"
            assert "成功索引 3 个文档" in result.message
    
    def test_build_index_no_documents(self, mock_index_manager):
        """测试索引构建无文档"""
        with patch('src.business.services.rag_service.LocalDataSource') as mock_ds:
            mock_ds_instance = mock_ds.return_value
            mock_ds_instance.load_documents.return_value = []
            
            service = RAGService()
            result = service.build_index("./empty_dir")
            
            assert result.success is False
            assert result.doc_count == 0
            assert "未找到文档" in result.message
    
    def test_build_index_github_url(self, mock_index_manager):
        """测试GitHub仓库索引"""
        with patch('src.business.services.rag_service.GitHubDataSource') as mock_gh:
            mock_gh_instance = mock_gh.return_value
            mock_gh_instance.load_documents.return_value = [Mock(text="doc")]
            
            service = RAGService()
            result = service.build_index("https://github.com/user/repo")
            
            assert result.success is True
            mock_gh.assert_called_once()
    
    def test_chat_new_session(self, mock_index_manager, mock_chat_manager):
        """测试新对话会话"""
        # Mock ChatManager
        mock_cm_instance = mock_chat_manager.return_value
        
        # Mock Session
        mock_session = Mock()
        mock_session.session_id = "new_session"
        mock_session.history = [Mock()]
        
        mock_cm_instance.create_session.return_value = mock_session
        mock_cm_instance.chat.return_value = ("回答", [{"file": "test.md"}])
        
        service = RAGService()
        response = service.chat("你好", user_id="user1")
        
        assert isinstance(response, ChatResponse)
        assert response.answer == "回答"
        assert response.session_id == "new_session"
        assert response.turn_count == 1
        assert len(response.sources) == 1
    
    def test_chat_existing_session(self, mock_index_manager, mock_chat_manager):
        """测试已有对话会话"""
        mock_cm_instance = mock_chat_manager.return_value
        
        # Mock 已存在的Session
        mock_session = Mock()
        mock_session.session_id = "existing_session"
        mock_session.history = [Mock(), Mock()]  # 已有2轮对话
        
        mock_cm_instance.get_session.return_value = mock_session
        mock_cm_instance.chat.return_value = ("继续回答", [])
        
        service = RAGService()
        response = service.chat("继续问", session_id="existing_session")
        
        assert response.session_id == "existing_session"
        assert response.turn_count == 2
    
    def test_lazy_loading(self, mock_index_manager, mock_query_engine, mock_chat_manager):
        """测试延迟加载机制"""
        service = RAGService()
        
        # 初始状态
        assert service._index_manager is None
        assert service._query_engine is None
        assert service._chat_manager is None
        
        # 访问index_manager触发加载
        _ = service.index_manager
        assert service._index_manager is not None
        mock_index_manager.assert_called_once()
        
        # 第二次访问不会重新创建
        _ = service.index_manager
        assert mock_index_manager.call_count == 1  # 仍然是1次
    
    def test_context_manager(self, mock_index_manager):
        """测试上下文管理器"""
        mock_instance = mock_index_manager.return_value
        
        with RAGService() as service:
            assert service is not None
        
        # 退出时应调用close
        # 注意：close内部会调用index_manager.close()
    
    def test_close(self, mock_index_manager):
        """测试资源关闭"""
        service = RAGService()
        
        # 触发延迟加载
        _ = service.index_manager
        mock_instance = mock_index_manager.return_value
        
        # 关闭服务
        service.close()
        
        # 验证close被调用
        mock_instance.close.assert_called_once()
        
        # 验证内部引用被清空
        assert service._index_manager is None
        assert service._query_engine is None
        assert service._chat_manager is None
    
    def test_list_collections(self, mock_index_manager):
        """测试列出集合"""
        mock_instance = mock_index_manager.return_value
        mock_instance.list_collections.return_value = ["col1", "col2", "col3"]
        
        service = RAGService()
        collections = service.list_collections()
        
        assert len(collections) == 3
        assert "col1" in collections
    
    def test_delete_collection(self, mock_index_manager):
        """测试删除集合"""
        mock_instance = mock_index_manager.return_value
        mock_instance.delete_collection.return_value = None
        
        service = RAGService()
        result = service.delete_collection("test_collection")
        
        assert result is True
        mock_instance.delete_collection.assert_called_once_with("test_collection")
    
    def test_clear_chat_history(self, mock_index_manager, mock_chat_manager):
        """测试清空对话历史"""
        mock_cm_instance = mock_chat_manager.return_value
        
        service = RAGService()
        result = service.clear_chat_history("session1")
        
        assert result is True
        mock_cm_instance.reset_session.assert_called_once_with("session1")


class TestRAGResponse:
    """RAGResponse数据类测试"""
    
    def test_rag_response_creation(self):
        """测试创建响应"""
        response = RAGResponse(
            answer="测试答案",
            sources=[{"file": "test.md"}],
            metadata={"key": "value"}
        )
        
        assert response.answer == "测试答案"
        assert len(response.sources) == 1
        assert response.metadata["key"] == "value"
        assert response.has_sources is True
    
    def test_rag_response_no_sources(self):
        """测试无来源响应"""
        response = RAGResponse(answer="答案", sources=[])
        assert response.has_sources is False


class TestIndexResult:
    """IndexResult数据类测试"""
    
    def test_index_result_success(self):
        """测试成功结果"""
        result = IndexResult(
            success=True,
            collection_name="test",
            doc_count=10,
            message="成功"
        )
        
        assert result.success is True
        assert result.collection_name == "test"
        assert result.doc_count == 10
        assert result.message == "成功"
    
    def test_index_result_failure(self):
        """测试失败结果"""
        result = IndexResult(
            success=False,
            collection_name="test",
            doc_count=0,
            message="失败原因"
        )
        
        assert result.success is False
        assert result.doc_count == 0


class TestChatResponse:
    """ChatResponse数据类测试"""
    
    def test_chat_response_creation(self):
        """测试创建对话响应"""
        response = ChatResponse(
            answer="对话回答",
            sources=[],
            session_id="session1",
            turn_count=3
        )
        
        assert response.answer == "对话回答"
        assert response.session_id == "session1"
        assert response.turn_count == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
