"""
对话管理模块单元测试
"""

import pytest
import json
from pathlib import Path
from src.chat_manager import ChatTurn, ChatSession, ChatManager


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
    
    def test_save_and_load(self, tmp_path):
        """测试保存和加载会话"""
        # 创建会话
        session = ChatSession(session_id="test_session")
        session.add_turn("问题1", "答案1", [{"index": 1}])
        session.add_turn("问题2", "答案2", [])
        
        # 保存
        save_dir = tmp_path / "sessions"
        session.save(save_dir)
        
        # 验证文件存在
        file_path = save_dir / "test_session.json"
        assert file_path.exists()
        
        # 加载
        loaded_session = ChatSession.load(file_path)
        
        # 验证内容
        assert loaded_session.session_id == "test_session"
        assert len(loaded_session.history) == 2
        assert loaded_session.history[0].question == "问题1"
        assert loaded_session.history[1].answer == "答案2"
    
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


class TestChatManager:
    """对话管理器测试（使用Mock）"""
    
    @pytest.fixture
    def mock_chat_manager(self, temp_vector_store, sample_documents, mocker):
        """创建Mock的对话管理器"""
        from src.indexer import IndexManager
        
        # 创建索引
        index_manager = IndexManager(
            collection_name="chat_test",
            persist_dir=temp_vector_store
        )
        index_manager.build_index(sample_documents, show_progress=False)
        
        # Mock DeepSeek LLM
        mock_llm = mocker.Mock()
        mocker.patch('src.chat.manager.DeepSeek', return_value=mock_llm)
        
        # Mock ChatEngine
        mock_engine = mocker.Mock()
        mock_response = mocker.Mock()
        mock_response.__str__ = lambda self: "Mock答案"
        mock_response.source_nodes = []
        mock_engine.chat.return_value = mock_response
        
        mocker.patch(
            'src.chat.manager.CondensePlusContextChatEngine.from_defaults',
            return_value=mock_engine
        )
        
        return ChatManager(index_manager)
    
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
        
        answer, sources = mock_chat_manager.chat("测试问题")
        
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
    
    def test_save_current_session(self, mock_chat_manager, tmp_path):
        """测试保存当前会话"""
        mock_chat_manager.start_session()
        mock_chat_manager.chat("测试问题")
        
        save_dir = tmp_path / "sessions"
        mock_chat_manager.save_current_session(save_dir=save_dir)
        
        # 验证文件被创建
        assert save_dir.exists()
        assert len(list(save_dir.glob("*.json"))) == 1
    
    def test_load_session(self, mock_chat_manager, tmp_path):
        """测试加载会话"""
        # 创建并保存会话
        session = ChatSession(session_id="load_test")
        session.add_turn("问题1", "答案1", [])
        save_dir = tmp_path / "sessions"
        session.save(save_dir)
        
        # 加载会话
        file_path = save_dir / "load_test.json"
        mock_chat_manager.load_session(file_path)
        
        # 验证
        current = mock_chat_manager.get_current_session()
        assert current.session_id == "load_test"
        assert len(current.history) == 1
    
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
        from src.indexer import IndexManager
        
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

