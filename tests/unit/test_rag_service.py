"""
RAGService单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from backend.business.rag_api.rag_service import RAGService
from backend.business.rag_api.models import RAGResponse, IndexResult, ChatResponse


@pytest.mark.fast


@pytest.mark.fast
class TestRAGService:
    """RAGService单元测试"""
    
    @pytest.fixture
    def mock_index_manager(self):
        """Mock IndexManager"""
        with patch('src.business.rag_api.rag_service.IndexManager') as mock:
            yield mock
    
    @pytest.fixture
    def mock_query_engine(self):
        """Mock QueryEngine"""
        with patch('src.business.rag_api.rag_service.ModularQueryEngine') as mock:
            yield mock
    
    @pytest.fixture
    def mock_chat_manager(self):
        """Mock ChatManager"""
        with patch('src.business.rag_api.rag_service.ChatManager') as mock:
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
        assert service._modular_query_engine is None
        assert service._chat_manager is None
    
    def test_query_success(self, mock_index_manager, mock_query_engine):
        """测试查询成功"""
        # Mock ModularQueryEngine.query返回值
        mock_query_instance = mock_query_engine.return_value
        mock_query_instance.query.return_value = (
            "这是测试答案",
            [{"file_name": "test.md", "content": "测试内容"}],
            None,  # reasoning_content
            {}  # metadata
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
        mock_query_instance.query.return_value = ("答案", [], None, {})
        
        service = RAGService()
        response = service.query("问题")
        
        assert response.has_sources is False
        assert len(response.sources) == 0
    
    def test_build_index_local_success(self, mock_index_manager):
        """测试本地索引构建成功"""
        # Mock IndexManager
        mock_instance = mock_index_manager.return_value
        
        # Mock DataImportService
        with patch('src.business.rag_api.rag_service.DataImportService') as mock_service:
            mock_service_instance = mock_service.return_value
            mock_result = Mock()
            mock_result.success = True
            mock_result.documents = [
                Mock(text="doc1"), Mock(text="doc2"), Mock(text="doc3")
            ]
            mock_service_instance.import_from_directory.return_value = mock_result
            
            service = RAGService(collection_name="test")
            result = service.build_index("./test_data")
            
            assert isinstance(result, IndexResult)
            assert result.success is True
            assert result.doc_count == 3
            assert result.collection_name == "test"
            assert "成功索引 3 个文档" in result.message
    
    def test_build_index_no_documents(self, mock_index_manager):
        """测试索引构建无文档"""
        with patch('src.business.rag_api.rag_service.DataImportService') as mock_service:
            mock_service_instance = mock_service.return_value
            mock_result = Mock()
            mock_result.success = True
            mock_result.documents = []
            mock_service_instance.import_from_directory.return_value = mock_result
            
            service = RAGService()
            result = service.build_index("./empty_dir")
            
            assert result.success is False
            assert result.doc_count == 0
            assert "未找到文档" in result.message
    
    def test_build_index_github_url(self, mock_index_manager):
        """测试GitHub仓库索引"""
        with patch('src.business.rag_api.rag_service.DataImportService') as mock_service:
            mock_service_instance = mock_service.return_value
            mock_result = Mock()
            mock_result.success = True
            mock_result.documents = [Mock(text="doc")]
            mock_service_instance.import_from_github.return_value = mock_result
            
            service = RAGService()
            result = service.build_index("https://github.com/user/repo")
            
            assert result.success is True
            mock_service_instance.import_from_github.assert_called_once()
    
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
        assert service._modular_query_engine is None
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
        assert service._modular_query_engine is None
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
    
    
    def test_modular_query_engine_usage(self, mock_index_manager):
        """测试使用模块化查询引擎"""
        from unittest.mock import Mock, patch
        
        with patch('src.business.rag_api.rag_service.ModularQueryEngine') as mock_modular:
            mock_modular_instance = mock_modular.return_value
            mock_modular_instance.query.return_value = (
                "模块化引擎答案",
                [{"file": "test.md"}],
                {}
            )
            
            service = RAGService()
            response = service.query("测试问题")
            
            assert isinstance(response, RAGResponse)
            assert response.answer == "模块化引擎答案"
            mock_modular.assert_called_once()
    
    def test_query_error_handling(self, mock_index_manager, mock_query_engine):
        """测试查询错误处理"""
        mock_query_instance = mock_query_engine.return_value
        mock_query_instance.query.side_effect = Exception("查询失败")
        
        service = RAGService()
        
        with pytest.raises(Exception, match="查询失败"):
            service.query("测试问题")
    
    def test_build_index_error_handling(self, mock_index_manager):
        """测试索引构建错误处理"""
        with patch('src.business.rag_api.rag_service.DataImportService') as mock_service:
            mock_service_instance = mock_service.return_value
            mock_result = Mock()
            mock_result.success = False
            mock_result.documents = []
            mock_service_instance.import_from_directory.return_value = mock_result
            
            service = RAGService()
            result = service.build_index("./test_data")
            
            assert result.success is False
            assert result.doc_count == 0
    
    def test_chat_error_handling(self, mock_index_manager, mock_chat_manager):
        """测试对话错误处理"""
        mock_cm_instance = mock_chat_manager.return_value
        mock_cm_instance.chat.side_effect = Exception("对话失败")
        
        service = RAGService()
        
        with pytest.raises(Exception, match="对话失败"):
            service.chat("测试消息")
    
    def test_lazy_loading_query_engine(self, mock_index_manager):
        """测试查询引擎懒加载"""
        service = RAGService()
        
        # 初始状态
        assert service._modular_query_engine is None
        
        # 访问modular_query_engine触发加载
        _ = service.modular_query_engine
        assert service._modular_query_engine is not None
        
        # 第二次访问不会重新创建
        _ = service.modular_query_engine
        # 验证IndexManager只初始化一次（通过mock验证）
    
    def test_lazy_loading_modular_engine(self, mock_index_manager):
        """测试模块化查询引擎懒加载"""
        with patch('src.business.rag_api.rag_service.ModularQueryEngine') as mock_modular:
            service = RAGService()
            
            # 初始状态
            assert service._modular_query_engine is None
            
            # 访问modular_query_engine触发加载
            _ = service.modular_query_engine
            assert service._modular_query_engine is not None
            
            # 第二次访问不会重新创建
            _ = service.modular_query_engine
            assert mock_modular.call_count == 1
    
    def test_lazy_loading_chat_manager(self, mock_index_manager):
        """测试对话管理器懒加载"""
        with patch('src.business.rag_api.rag_service.ChatManager') as mock_chat:
            service = RAGService()
            
            # 初始状态
            assert service._chat_manager is None
            
            # 访问chat_manager触发加载
            _ = service.chat_manager
            assert service._chat_manager is not None
            
            # 第二次访问不会重新创建
            _ = service.chat_manager
            assert mock_chat.call_count == 1
    
    def test_query_with_modular_engine_fallback(self, mock_index_manager):
        """测试模块化引擎错误处理"""
        from unittest.mock import Mock, patch
        
        # 模拟modular_engine查询失败的情况
        with patch('src.business.rag_api.rag_service.ModularQueryEngine') as mock_query:
            mock_query_instance = mock_query.return_value
            mock_query_instance.query.side_effect = Exception("查询失败")
            
            service = RAGService()
            
            # 如果查询失败，应该抛出异常
            with pytest.raises(Exception):
                service.query("测试问题")
    
    def test_build_index_with_collection_name(self, mock_index_manager):
        """测试使用指定集合名称构建索引"""
        with patch('src.business.rag_api.rag_service.DataImportService') as mock_service:
            mock_service_instance = mock_service.return_value
            mock_result = Mock()
            mock_result.success = True
            mock_result.documents = [Mock(text="doc1"), Mock(text="doc2")]
            mock_service_instance.import_from_directory.return_value = mock_result
            
            mock_instance = mock_index_manager.return_value
            service = RAGService(collection_name="default_collection")
            
            result = service.build_index("./test_data", collection_name="custom_collection")
            
            assert result.success is True
            assert result.collection_name == "custom_collection"
            # 验证使用了指定的集合名称
            mock_instance.build_index.assert_called_once()
    
    def test_context_manager_cleanup(self, mock_index_manager):
        """测试上下文管理器清理资源"""
        mock_instance = mock_index_manager.return_value
        
        with RAGService() as service:
            # 触发延迟加载
            _ = service.index_manager
        
        # 退出上下文时应调用close
        mock_instance.close.assert_called_once()
    
    def test_close_with_none_components(self):
        """测试关闭时组件为None的情况"""
        service = RAGService()
        
        # 组件都是None，关闭不应该出错
        service.close()
        
        assert service._index_manager is None
        assert service._modular_query_engine is None
        assert service._chat_manager is None
    
    def test_list_collections_error_handling(self, mock_index_manager):
        """测试列出集合的错误处理"""
        mock_instance = mock_index_manager.return_value
        mock_instance.list_collections.side_effect = Exception("列出失败")
        
        service = RAGService()
        collections = service.list_collections()
        
        # 应该返回空列表而不是抛出异常
        assert isinstance(collections, list)
        assert len(collections) == 0
    
    def test_delete_collection_error_handling(self, mock_index_manager):
        """测试删除集合的错误处理"""
        mock_instance = mock_index_manager.return_value
        mock_instance.delete_collection.side_effect = Exception("删除失败")
        
        service = RAGService()
        result = service.delete_collection("test_collection")
        
        # 应该返回False而不是抛出异常
        assert result is False


@pytest.mark.fast
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


@pytest.mark.fast
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


@pytest.mark.fast
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
