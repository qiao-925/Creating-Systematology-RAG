"""
RAGService 单元测试
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from backend.business.rag_api.models import ChatResponse, IndexResult, RAGResponse
from backend.business.rag_api.rag_service import RAGService


@pytest.fixture
def mock_index_manager():
    with patch("backend.infrastructure.indexer.IndexManager") as mock:
        yield mock


@pytest.fixture
def mock_query_engine():
    with patch("backend.business.rag_engine.core.engine.ModularQueryEngine") as mock:
        yield mock


@pytest.fixture
def mock_chat_manager():
    with patch("backend.business.chat.ChatManager") as mock:
        yield mock


def make_source(
    *,
    text: str = "测试内容",
    score: float = 0.9,
    file_name: str = "test.md",
) -> dict:
    return {
        "text": text,
        "score": score,
        "metadata": {"file_name": file_name},
        "file_name": file_name,
    }


@pytest.mark.fast
class TestRAGService:
    def test_rag_service_init(self):
        service = RAGService(
            collection_name="test_collection",
            similarity_top_k=5,
            enable_debug=True,
        )

        assert service.collection_name == "test_collection"
        assert service.similarity_top_k == 5
        assert service.enable_debug is True
        assert service._index_manager is None
        assert service._modular_query_engine is None
        assert service._chat_manager is None

    def test_query_success(self, mock_index_manager, mock_query_engine):
        mock_query_engine.return_value.query.return_value = (
            "这是测试答案",
            [make_source()],
            None,
            {},
        )

        service = RAGService(collection_name="test")
        response = service.query("测试问题", user_id="user1")

        assert isinstance(response, RAGResponse)
        assert response.answer == "这是测试答案"
        assert response.has_sources is True
        assert response.sources[0].file_name == "test.md"
        assert response.metadata["user_id"] == "user1"
        assert response.metadata["question"] == "测试问题"
        mock_index_manager.assert_called_once()
        mock_query_engine.assert_called_once()

    def test_query_no_sources(self, mock_query_engine):
        mock_query_engine.return_value.query.return_value = ("答案", [], None, {})

        service = RAGService()
        response = service.query("问题")

        assert response.has_sources is False
        assert response.sources == []

    def test_build_index_local_success(self, mock_index_manager):
        mock_index_manager.return_value.get_stats.return_value = {"document_count": 3}

        with patch(
            "backend.business.rag_api.rag_service_index.load_documents_from_source",
            return_value=([Mock(), Mock(), Mock()], None),
        ):
            service = RAGService(collection_name="test")
            result = service.build_index("./test_data")

        assert isinstance(result, IndexResult)
        assert result.success is True
        assert result.doc_count == 3
        assert result.collection_name == "test"
        assert "3 个文档" in result.message
        mock_index_manager.return_value.build_index.assert_called_once()

    def test_build_index_no_documents(self, mock_index_manager):
        with patch(
            "backend.business.rag_api.rag_service_index.load_documents_from_source",
            return_value=([], None),
        ):
            service = RAGService()
            result = service.build_index("./empty_dir")

        assert result.success is False
        assert result.doc_count == 0
        assert "未找到任何文档" in result.message
        mock_index_manager.return_value.build_index.assert_not_called()

    def test_build_index_error_handling(self, mock_index_manager):
        mock_index_manager.return_value.build_index.side_effect = RuntimeError("构建失败")

        with patch(
            "backend.business.rag_api.rag_service_index.load_documents_from_source",
            return_value=([Mock()], None),
        ):
            service = RAGService()
            result = service.build_index("./test_data")

        assert result.success is False
        assert result.doc_count == 0
        assert "构建失败" in result.message

    def test_build_index_with_collection_name(self, mock_index_manager):
        mock_index_manager.return_value.get_stats.return_value = {"document_count": 2}

        with patch(
            "backend.business.rag_api.rag_service_index.load_documents_from_source",
            return_value=([Mock(), Mock()], None),
        ):
            service = RAGService(collection_name="default_collection")
            result = service.build_index("./test_data", collection_name="custom_collection")

        assert result.success is True
        assert result.collection_name == "custom_collection"
        assert mock_index_manager.return_value.collection_name == "custom_collection"

    def test_chat_new_session(self, mock_chat_manager):
        session = Mock(session_id="new_session")
        session.history = [Mock()]
        mock_chat_manager.return_value.get_current_session.side_effect = [None, session]
        mock_chat_manager.return_value.start_session.return_value = session
        mock_chat_manager.return_value.chat.return_value = ("回答", [make_source()], None)

        service = RAGService(chat_manager=mock_chat_manager.return_value)
        response = service.chat("你好", user_id="user1")

        assert isinstance(response, ChatResponse)
        assert response.answer == "回答"
        assert response.session_id == "new_session"
        assert response.turn_count == 1
        assert len(response.sources) == 1
        mock_chat_manager.return_value.start_session.assert_called_once()

    def test_chat_existing_session(self, mock_chat_manager):
        session = Mock(session_id="existing_session")
        session.history = [Mock(), Mock()]
        mock_chat_manager.return_value.get_current_session.return_value = session
        mock_chat_manager.return_value.chat.return_value = ("继续回答", [], None)

        service = RAGService(chat_manager=mock_chat_manager.return_value)
        response = service.chat("继续问", session_id="existing_session")

        assert response.session_id == "existing_session"
        assert response.turn_count == 2
        mock_chat_manager.return_value.start_session.assert_not_called()

    def test_chat_error_handling(self, mock_chat_manager):
        session = Mock(session_id="session_1")
        session.history = []
        mock_chat_manager.return_value.get_current_session.side_effect = [None, session]
        mock_chat_manager.return_value.start_session.return_value = session
        mock_chat_manager.return_value.chat.side_effect = Exception("对话失败")

        service = RAGService(chat_manager=mock_chat_manager.return_value)

        with pytest.raises(Exception, match="对话失败"):
            service.chat("测试消息")

    def test_lazy_loading_index_manager(self, mock_index_manager):
        service = RAGService()

        _ = service.index_manager
        _ = service.index_manager

        mock_index_manager.assert_called_once()

    def test_lazy_loading_modular_query_engine(self, mock_index_manager, mock_query_engine):
        service = RAGService()

        _ = service.modular_query_engine
        _ = service.modular_query_engine

        mock_index_manager.assert_called_once()
        mock_query_engine.assert_called_once()

    def test_lazy_loading_chat_manager(self, mock_index_manager, mock_chat_manager):
        service = RAGService()

        _ = service.chat_manager
        _ = service.chat_manager

        mock_index_manager.assert_called_once()
        mock_chat_manager.assert_called_once()

    def test_close(self, mock_index_manager):
        service = RAGService()
        _ = service.index_manager

        mock_instance = mock_index_manager.return_value
        service.close()

        mock_instance.close.assert_called_once()
        assert service._index_manager is None
        assert service._modular_query_engine is None
        assert service._chat_manager is None

    def test_context_manager_cleanup(self, mock_index_manager):
        mock_instance = mock_index_manager.return_value

        with RAGService() as service:
            _ = service.index_manager

        mock_instance.close.assert_called_once()
        assert service._index_manager is None

    def test_list_collections(self, mock_index_manager):
        mock_index_manager.return_value.list_collections.return_value = ["col1", "col2", "col3"]

        service = RAGService()
        collections = service.list_collections()

        assert collections == ["col1", "col2", "col3"]

    def test_list_collections_error_handling(self, mock_index_manager):
        mock_index_manager.return_value.list_collections.side_effect = Exception("列出失败")

        service = RAGService()
        collections = service.list_collections()

        assert collections == []

    def test_delete_collection(self, mock_index_manager):
        service = RAGService()
        result = service.delete_collection("test_collection")

        assert result is True
        mock_index_manager.return_value.delete_collection.assert_called_once_with("test_collection")

    def test_delete_collection_error_handling(self, mock_index_manager):
        mock_index_manager.return_value.delete_collection.side_effect = Exception("删除失败")

        service = RAGService()
        result = service.delete_collection("test_collection")

        assert result is False

    def test_query_error_handling(self, mock_query_engine):
        mock_query_engine.return_value.query.side_effect = Exception("查询失败")
        service = RAGService()

        with pytest.raises(Exception, match="查询失败"):
            service.query("测试问题")


@pytest.mark.fast
class TestResponseModels:
    def test_rag_response_creation(self):
        response = RAGResponse(
            answer="测试答案",
            sources=[make_source(file_name="response.md")],
            metadata={"key": "value"},
        )

        assert response.answer == "测试答案"
        assert response.sources[0].file_name == "response.md"
        assert response.metadata["key"] == "value"
        assert response.has_sources is True

    def test_rag_response_no_sources(self):
        response = RAGResponse(answer="答案", sources=[])
        assert response.has_sources is False

    def test_index_result_success(self):
        result = IndexResult(
            success=True,
            collection_name="test",
            doc_count=10,
            message="成功",
        )

        assert result.success is True
        assert result.collection_name == "test"
        assert result.doc_count == 10
        assert result.message == "成功"

    def test_chat_response_creation(self):
        response = ChatResponse(
            answer="对话回答",
            sources=[make_source(score=0.7)],
            session_id="session1",
            turn_count=3,
        )

        assert response.answer == "对话回答"
        assert response.session_id == "session1"
        assert response.turn_count == 3
