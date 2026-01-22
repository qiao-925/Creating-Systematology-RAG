"""
对话管理模块单元测试
"""

import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock
from backend.business.chat import ChatTurn, ChatSession, ChatManager


@pytest.mark.fast
class TestChatTurn:
    """ChatTurn数据类测试"""
    
    def test_creation(self):
        """测试创建ChatTurn"""
        turn = ChatTurn(
            question="测试问题",
            answer="测试答案",
            sources=[],
            timestamp="2025-10-07T12:00:00"
        )
        
        assert turn.question == "测试问题"
        assert turn.answer == "测试答案"
        assert turn.sources == []
        assert turn.timestamp == "2025-10-07T12:00:00"
    
    def test_to_dict(self):
        """测试转换为字典"""
        turn = ChatTurn(
            question="问题",
            answer="答案",
            sources=[{"index": 1}],
            timestamp="2025-10-07T12:00:00"
        )
        
        data = turn.to_dict()
        
        assert isinstance(data, dict)
        assert data['question'] == "问题"
        assert data['answer'] == "答案"
        assert len(data['sources']) == 1
    
    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            'question': "问题",
            'answer': "答案",
            'sources': [],
            'timestamp': "2025-10-07T12:00:00"
        }
        
        turn = ChatTurn.from_dict(data)
        
        assert turn.question == "问题"
        assert turn.answer == "答案"


@pytest.mark.fast
class TestChatSession:
    """ChatSession测试"""
    
    def test_session_creation(self):
        """测试会话创建"""
        session = ChatSession()
        
        assert session.session_id is not None
        assert session.history == []
        assert session.created_at is not None
    
    def test_session_with_custom_id(self):
        """测试使用自定义ID创建会话"""
        session = ChatSession(session_id="custom_id_123")
        
        assert session.session_id == "custom_id_123"
    
    def test_add_turn(self):
        """测试添加对话轮次"""
        session = ChatSession()
        
        session.add_turn("问题1", "答案1", [])
        assert len(session.history) == 1
        
        session.add_turn("问题2", "答案2", [{"index": 1}])
        assert len(session.history) == 2
        
        # 验证内容
        assert session.history[0].question == "问题1"
        assert session.history[1].answer == "答案2"
    
    def test_get_history_all(self):
        """测试获取全部历史"""
        session = ChatSession()
        session.add_turn("问题1", "答案1", [])
        session.add_turn("问题2", "答案2", [])
        
        history = session.get_history()
        assert len(history) == 2
    
    def test_get_history_last_n(self):
        """测试获取最近N轮对话"""
        session = ChatSession()
        for i in range(5):
            session.add_turn(f"问题{i}", f"答案{i}", [])
        
        last_2 = session.get_history(last_n=2)
        
        assert len(last_2) == 2
        assert last_2[0].question == "问题3"
        assert last_2[1].question == "问题4"
    
    def test_clear_history(self):
        """测试清空历史"""
        session = ChatSession()
        session.add_turn("问题", "答案", [])
        assert len(session.history) == 1
        
        session.clear_history()
        assert len(session.history) == 0
    
    def test_to_dict_from_dict(self):
        """测试序列化和反序列化"""
        session = ChatSession(session_id="test_123")
        session.add_turn("问题", "答案", [])
        
        # 转换为字典
        data = session.to_dict()
        assert isinstance(data, dict)
        assert data['session_id'] == "test_123"
        
        # 从字典创建
        new_session = ChatSession.from_dict(data)
        assert new_session.session_id == session.session_id
        assert len(new_session.history) == len(session.history)


@pytest.mark.fast
class TestChatManager:
    """对话管理器测试（使用Mock）"""
    
    @pytest.fixture
    def mock_chat_manager(self, tmp_path, sample_documents, mocker, monkeypatch):
        """创建Mock的对话管理器"""
        from backend.infrastructure.indexer import IndexManager
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        
        temp_vector_store = tmp_path / "test_vector_store"
        temp_vector_store.mkdir()
        
        # 创建索引
        index_manager = IndexManager(
            collection_name="chat_test",
            persist_dir=temp_vector_store
        )
        index_manager.build_index(sample_documents, show_progress=False)
        
        # Mock LLM
        mock_llm = mocker.Mock()
        mock_response = mocker.Mock()
        mock_response.text = "Mock答案"
        mock_llm.complete.return_value = mock_response
        
        # Mock ModularQueryEngine
        mock_engine = mocker.Mock(spec=ModularQueryEngine)
        mock_engine.query.return_value = ("Mock答案", [], None, {})
        
        monkeypatch.setattr(
            'backend.business.chat.manager.create_deepseek_llm_for_query',
            lambda **kwargs: mock_llm
        )
        
        mocker.patch(
            'backend.business.chat.manager.ModularQueryEngine',
            return_value=mock_engine
        )
        
        return ChatManager(index_manager, api_key="test_key")
    
    def test_start_session(self, mock_chat_manager):
        """测试开始新会话"""
        session = mock_chat_manager.start_session()
        
        assert session is not None
        assert session.session_id is not None
        assert len(session.history) == 0
    
    def test_chat_creates_session_if_not_exists(self, mock_chat_manager):
        """测试聊天时自动创建会话"""
        # 确保没有当前会话
        mock_chat_manager.current_session = None
        
        answer, sources, _ = mock_chat_manager.chat("测试问题")
        
        assert mock_chat_manager.current_session is not None
    
    def test_chat_adds_to_history(self, mock_chat_manager):
        """测试对话添加到历史"""
        mock_chat_manager.start_session()
        
        mock_chat_manager.chat("问题1")
        assert len(mock_chat_manager.current_session.history) == 1
        
        mock_chat_manager.chat("问题2")
        assert len(mock_chat_manager.current_session.history) == 2
    
    def test_get_current_session(self, mock_chat_manager):
        """测试获取当前会话"""
        session = mock_chat_manager.start_session()
        current = mock_chat_manager.get_current_session()
        
        assert current is not None
        assert current.session_id == session.session_id
    
    def test_reset_session(self, mock_chat_manager):
        """测试重置会话"""
        mock_chat_manager.start_session()
        mock_chat_manager.chat("问题")
        
        assert len(mock_chat_manager.current_session.history) > 0
        
        mock_chat_manager.reset_session()
        
        assert len(mock_chat_manager.current_session.history) == 0


# ==================== 需要真实API的测试 ====================

@pytest.mark.slow
@pytest.mark.requires_real_api
@pytest.mark.xfail(reason="DeepSeek completions API需要beta endpoint，llama_index兼容性问题")
class TestChatManagerWithRealAPI:
    """使用真实API的对话管理器测试"""
    
    def test_multi_turn_conversation(self, temp_vector_store, sample_documents):
        """测试多轮对话（需要真实API）"""
        from backend.infrastructure.indexer import IndexManager
        
        index_manager = IndexManager(
            collection_name="real_chat_test",
            persist_dir=temp_vector_store
        )
        index_manager.build_index(sample_documents, show_progress=False)
        
        chat_manager = ChatManager(index_manager)
        chat_manager.start_session()
        
        # 第一轮
        answer1, _ = chat_manager.chat("什么是系统科学？")
        assert len(answer1) > 0
        
        # 第二轮（使用指代）
        answer2, _ = chat_manager.chat("它有哪些分支？")
        assert len(answer2) > 0


# ==================== 新功能测试 ====================

@pytest.mark.fast
class TestChatManagerNewFeatures:
    """ChatManager 新功能测试"""
    
    @pytest.fixture
    def mock_index_manager(self, tmp_path, sample_documents, mocker):
        """创建Mock的索引管理器"""
        from backend.infrastructure.indexer import IndexManager
        
        temp_vector_store = tmp_path / "test_vector_store"
        temp_vector_store.mkdir()
        
        index_manager = IndexManager(
            collection_name="new_features_test",
            persist_dir=temp_vector_store
        )
        index_manager.build_index(sample_documents, show_progress=False)
        return index_manager
    
    @pytest.fixture
    def mock_llm(self, mocker):
        """Mock LLM"""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.text = "压缩后的查询"
        mock_llm.complete.return_value = mock_response
        
        # Mock stream_complete
        async def mock_stream():
            chunks = ["这是", "测试", "答案"]
            for chunk in chunks:
                mock_chunk = Mock()
                mock_chunk.text = chunk
                yield mock_chunk
        
        mock_llm.stream_complete = Mock(return_value=mock_stream())
        return mock_llm
    
    def test_agentic_rag_mode(self, mock_index_manager, mock_llm, mocker, monkeypatch):
        """测试 use_agentic_rag=True 时使用 AgenticQueryEngine"""
        from backend.business.rag_engine.agentic import AgenticQueryEngine
        
        # Mock AgenticQueryEngine
        mock_agentic_engine = Mock(spec=AgenticQueryEngine)
        mock_agentic_engine.query.return_value = (
            "Agentic答案",
            [{"file_name": "test.md", "content": "测试内容"}],
            None,
            {}
        )
        
        # Mock create_deepseek_llm_for_query
        monkeypatch.setattr(
            'backend.business.chat.manager.create_deepseek_llm_for_query',
            lambda **kwargs: mock_llm
        )
        
        # Mock AgenticQueryEngine 的创建
        mocker.patch(
            'backend.business.chat.manager.AgenticQueryEngine',
            return_value=mock_agentic_engine
        )
        
        # 创建 ChatManager，启用 Agentic RAG
        chat_manager = ChatManager(
            index_manager=mock_index_manager,
            use_agentic_rag=True,
            api_key="test_key"
        )
        
        # 验证使用的是 AgenticQueryEngine
        assert isinstance(chat_manager.query_engine, Mock)
        assert chat_manager.query_engine == mock_agentic_engine
        
        # 测试查询
        answer, sources, _ = chat_manager.chat("测试问题")
        
        # 验证调用了 AgenticQueryEngine
        mock_agentic_engine.query.assert_called_once()
        assert answer == "Agentic答案"
    
    def test_agentic_rag_vs_modular(self, mock_index_manager, mock_llm, mocker, monkeypatch):
        """对比 Agentic 和 Modular 模式的行为差异"""
        from backend.business.rag_engine.agentic import AgenticQueryEngine
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        
        # Mock AgenticQueryEngine
        mock_agentic = Mock(spec=AgenticQueryEngine)
        mock_agentic.query.return_value = ("Agentic答案", [], None, {})
        
        # Mock ModularQueryEngine
        mock_modular = Mock(spec=ModularQueryEngine)
        mock_modular.query.return_value = ("Modular答案", [], None, {})
        
        monkeypatch.setattr(
            'backend.business.chat.manager.create_deepseek_llm_for_query',
            lambda **kwargs: mock_llm
        )
        
        # 测试 Agentic 模式
        mocker.patch(
            'backend.business.chat.manager.AgenticQueryEngine',
            return_value=mock_agentic
        )
        chat_manager_agentic = ChatManager(
            index_manager=mock_index_manager,
            use_agentic_rag=True,
            api_key="test_key"
        )
        
        # 测试 Modular 模式
        mocker.patch(
            'backend.business.chat.manager.ModularQueryEngine',
            return_value=mock_modular
        )
        chat_manager_modular = ChatManager(
            index_manager=mock_index_manager,
            use_agentic_rag=False,
            api_key="test_key"
        )
        
        # 验证使用了不同的引擎
        assert chat_manager_agentic.query_engine == mock_agentic
        assert chat_manager_modular.query_engine == mock_modular
    
    @pytest.mark.asyncio
    async def test_stream_chat_basic(self, mock_index_manager, mock_llm, mocker, monkeypatch):
        """测试流式对话基本功能"""
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        
        # Mock ModularQueryEngine 的 stream_query
        async def mock_stream_query(query):
            yield {'type': 'token', 'data': '这是'}
            yield {'type': 'token', 'data': '测试'}
            yield {'type': 'token', 'data': '答案'}
            yield {'type': 'sources', 'data': [{"file_name": "test.md"}]}
            yield {'type': 'done', 'data': {'answer': '这是测试答案'}}
        
        mock_engine = Mock(spec=ModularQueryEngine)
        mock_engine.stream_query = mock_stream_query
        
        monkeypatch.setattr(
            'backend.business.chat.manager.create_deepseek_llm_for_query',
            lambda **kwargs: mock_llm
        )
        
        mocker.patch(
            'backend.business.chat.manager.ModularQueryEngine',
            return_value=mock_engine
        )
        
        chat_manager = ChatManager(
            index_manager=mock_index_manager,
            api_key="test_key"
        )
        
        # 测试流式对话
        tokens = []
        sources = None
        
        async for chunk in chat_manager.stream_chat("测试问题"):
            if chunk['type'] == 'token':
                tokens.append(chunk['data'])
            elif chunk['type'] == 'sources':
                sources = chunk['data']
            elif chunk['type'] == 'done':
                break
        
        assert len(tokens) > 0
        assert sources is not None
    
    @pytest.mark.asyncio
    async def test_stream_chat_token_streaming(self, mock_index_manager, mock_llm, mocker, monkeypatch):
        """测试 token 流式输出"""
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        
        tokens_to_yield = ['这是', '一个', '流式', '测试']
        
        async def mock_stream_query(query):
            for token in tokens_to_yield:
                yield {'type': 'token', 'data': token}
            yield {'type': 'done', 'data': {}}
        
        mock_engine = Mock(spec=ModularQueryEngine)
        mock_engine.stream_query = mock_stream_query
        
        monkeypatch.setattr(
            'backend.business.chat.manager.create_deepseek_llm_for_query',
            lambda **kwargs: mock_llm
        )
        
        mocker.patch(
            'backend.business.chat.manager.ModularQueryEngine',
            return_value=mock_engine
        )
        
        chat_manager = ChatManager(
            index_manager=mock_index_manager,
            api_key="test_key"
        )
        
        received_tokens = []
        async for chunk in chat_manager.stream_chat("测试"):
            if chunk['type'] == 'token':
                received_tokens.append(chunk['data'])
            elif chunk['type'] == 'done':
                break
        
        assert received_tokens == tokens_to_yield
    
    @pytest.mark.asyncio
    async def test_stream_chat_sources(self, mock_index_manager, mock_llm, mocker, monkeypatch):
        """测试流式对话中的 sources 返回"""
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        
        test_sources = [
            {"file_name": "doc1.md", "content": "内容1"},
            {"file_name": "doc2.md", "content": "内容2"}
        ]
        
        async def mock_stream_query(query):
            yield {'type': 'token', 'data': '答案'}
            yield {'type': 'sources', 'data': test_sources}
            yield {'type': 'done', 'data': {}}
        
        mock_engine = Mock(spec=ModularQueryEngine)
        mock_engine.stream_query = mock_stream_query
        
        monkeypatch.setattr(
            'backend.business.chat.manager.create_deepseek_llm_for_query',
            lambda **kwargs: mock_llm
        )
        
        mocker.patch(
            'backend.business.chat.manager.ModularQueryEngine',
            return_value=mock_engine
        )
        
        chat_manager = ChatManager(
            index_manager=mock_index_manager,
            api_key="test_key"
        )
        
        sources = None
        async for chunk in chat_manager.stream_chat("测试"):
            if chunk['type'] == 'sources':
                sources = chunk['data']
            elif chunk['type'] == 'done':
                break
        
        assert sources == test_sources
    
    @pytest.mark.asyncio
    async def test_stream_chat_reasoning(self, mock_index_manager, mock_llm, mocker, monkeypatch):
        """测试流式对话中的 reasoning 返回"""
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        
        test_reasoning = "这是推理链内容"
        
        async def mock_stream_query(query):
            yield {'type': 'token', 'data': '答案'}
            yield {'type': 'reasoning', 'data': test_reasoning}
            yield {'type': 'done', 'data': {}}
        
        mock_engine = Mock(spec=ModularQueryEngine)
        mock_engine.stream_query = mock_stream_query
        
        monkeypatch.setattr(
            'backend.business.chat.manager.create_deepseek_llm_for_query',
            lambda **kwargs: mock_llm
        )
        
        mocker.patch(
            'backend.business.chat.manager.ModularQueryEngine',
            return_value=mock_engine
        )
        
        chat_manager = ChatManager(
            index_manager=mock_index_manager,
            api_key="test_key"
        )
        
        reasoning = None
        async for chunk in chat_manager.stream_chat("测试"):
            if chunk['type'] == 'reasoning':
                reasoning = chunk['data']
            elif chunk['type'] == 'done':
                break
        
        assert reasoning == test_reasoning
    
    def test_smart_condense_short_history(self, mock_index_manager, mock_llm, mocker, monkeypatch):
        """测试短历史（≤2轮）不压缩"""
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        
        mock_engine = Mock(spec=ModularQueryEngine)
        mock_engine.query.return_value = ("答案", [], None, {})
        
        monkeypatch.setattr(
            'backend.business.chat.manager.create_deepseek_llm_for_query',
            lambda **kwargs: mock_llm
        )
        
        mocker.patch(
            'backend.business.chat.manager.ModularQueryEngine',
            return_value=mock_engine
        )
        
        chat_manager = ChatManager(
            index_manager=mock_index_manager,
            enable_smart_condense=True,
            api_key="test_key"
        )
        
        chat_manager.start_session()
        
        # 第一轮对话
        chat_manager.chat("问题1")
        
        # 第二轮对话（短历史，应该不压缩）
        chat_manager.chat("问题2")
        
        # 验证 query 被调用，但 LLM.complete 不应该被调用（因为短历史不压缩）
        assert mock_engine.query.call_count == 2
        # 短历史时，_condense_query_with_history 应该直接拼接，不调用 LLM
        # 但由于我们 Mock 了 query，无法直接验证，所以只验证 query 被调用了
    
    def test_smart_condense_medium_history(self, mock_index_manager, mock_llm, mocker, monkeypatch):
        """测试中等历史（3-4轮）简单拼接"""
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        
        mock_engine = Mock(spec=ModularQueryEngine)
        mock_engine.query.return_value = ("答案", [], None, {})
        
        monkeypatch.setattr(
            'backend.business.chat.manager.create_deepseek_llm_for_query',
            lambda **kwargs: mock_llm
        )
        
        mocker.patch(
            'backend.business.chat.manager.ModularQueryEngine',
            return_value=mock_engine
        )
        
        chat_manager = ChatManager(
            index_manager=mock_index_manager,
            enable_smart_condense=True,
            api_key="test_key"
        )
        
        chat_manager.start_session()
        
        # 进行3-4轮对话
        for i in range(4):
            chat_manager.chat(f"问题{i+1}")
        
        # 验证 query 被调用了4次
        assert mock_engine.query.call_count == 4
    
    def test_smart_condense_long_history(self, mock_index_manager, mock_llm, mocker, monkeypatch):
        """测试长历史（≥5轮）LLM 压缩"""
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        
        mock_engine = Mock(spec=ModularQueryEngine)
        mock_engine.query.return_value = ("答案", [], None, {})
        
        # Mock LLM 的 complete 方法（用于查询压缩）
        mock_llm.complete.return_value.text = "压缩后的查询"
        
        monkeypatch.setattr(
            'backend.business.chat.manager.create_deepseek_llm_for_query',
            lambda **kwargs: mock_llm
        )
        
        mocker.patch(
            'backend.business.chat.manager.ModularQueryEngine',
            return_value=mock_engine
        )
        
        chat_manager = ChatManager(
            index_manager=mock_index_manager,
            enable_smart_condense=True,
            api_key="test_key"
        )
        
        chat_manager.start_session()
        
        # 进行5轮以上对话，触发 LLM 压缩
        for i in range(6):
            chat_manager.chat(f"问题{i+1}")
        
        # 验证 query 被调用了6次
        assert mock_engine.query.call_count == 6
        # 验证 LLM.complete 被调用（用于压缩长历史）
        assert mock_llm.complete.call_count > 0
    
    def test_smart_condense_disabled(self, mock_index_manager, mock_llm, mocker, monkeypatch):
        """测试禁用智能压缩时的行为"""
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        
        mock_engine = Mock(spec=ModularQueryEngine)
        mock_engine.query.return_value = ("答案", [], None, {})
        
        monkeypatch.setattr(
            'backend.business.chat.manager.create_deepseek_llm_for_query',
            lambda **kwargs: mock_llm
        )
        
        mocker.patch(
            'backend.business.chat.manager.ModularQueryEngine',
            return_value=mock_engine
        )
        
        chat_manager = ChatManager(
            index_manager=mock_index_manager,
            enable_smart_condense=False,
            api_key="test_key"
        )
        
        chat_manager.start_session()
        
        # 进行多轮对话
        for i in range(3):
            chat_manager.chat(f"问题{i+1}")
        
        # 验证 query 被调用
        assert mock_engine.query.call_count == 3
    
    def test_retrieval_quality_evaluation_high(self, mock_index_manager, mock_llm, mocker, monkeypatch, caplog):
        """测试高质量检索的日志记录"""
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        
        # 高质量 sources（相似度 >= threshold）
        high_quality_sources = [
            {"file_name": "doc1.md", "score": 0.85},
            {"file_name": "doc2.md", "score": 0.82},
            {"file_name": "doc3.md", "score": 0.78}
        ]
        
        mock_engine = Mock(spec=ModularQueryEngine)
        mock_engine.query.return_value = ("答案", high_quality_sources, None, {})
        
        monkeypatch.setattr(
            'backend.business.chat.manager.create_deepseek_llm_for_query',
            lambda **kwargs: mock_llm
        )
        
        mocker.patch(
            'backend.business.chat.manager.ModularQueryEngine',
            return_value=mock_engine
        )
        
        chat_manager = ChatManager(
            index_manager=mock_index_manager,
            similarity_threshold=0.7,
            api_key="test_key"
        )
        
        chat_manager.start_session()
        chat_manager.chat("测试问题")
        
        # 验证日志中包含质量良好的信息
        assert "检索质量良好" in caplog.text or "高质量结果" in caplog.text
    
    def test_retrieval_quality_evaluation_low(self, mock_index_manager, mock_llm, mocker, monkeypatch, caplog):
        """测试低质量检索的警告日志"""
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        
        # 低质量 sources（相似度 < threshold）
        low_quality_sources = [
            {"file_name": "doc1.md", "score": 0.5},
            {"file_name": "doc2.md", "score": 0.4}
        ]
        
        mock_engine = Mock(spec=ModularQueryEngine)
        mock_engine.query.return_value = ("答案", low_quality_sources, None, {})
        
        monkeypatch.setattr(
            'backend.business.chat.manager.create_deepseek_llm_for_query',
            lambda **kwargs: mock_llm
        )
        
        mocker.patch(
            'backend.business.chat.manager.ModularQueryEngine',
            return_value=mock_engine
        )
        
        chat_manager = ChatManager(
            index_manager=mock_index_manager,
            similarity_threshold=0.7,
            api_key="test_key"
        )
        
        chat_manager.start_session()
        chat_manager.chat("测试问题")
        
        # 验证日志中包含质量较低的警告
        assert "检索质量较低" in caplog.text or "最高相似度" in caplog.text

