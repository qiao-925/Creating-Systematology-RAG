"""
测试 frontend/components/session_loader.py
对应源文件：frontend/components/session_loader.py
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from frontend.components.session_loader import load_history_session


class TestSessionLoader:
    """测试 load_history_session 函数"""
    
    @patch('frontend.components.session_loader.st')
    def test_load_history_session_no_load_id(self, mock_st):
        """测试没有加载ID时不执行加载"""
        mock_st.session_state = {}
        
        mock_chat_manager = MagicMock()
        
        load_history_session(mock_chat_manager)
        
        # 验证没有调用任何加载逻辑
        mock_chat_manager.assert_not_called()
    
    @patch('frontend.components.session_loader.st')
    @patch('src.business.chat.load_session_from_file')
    @patch('frontend.components.session_loader.convert_sources_to_dict')
    def test_load_history_session_success(self, mock_convert, mock_load, mock_st):
        """测试成功加载历史会话"""
        from frontend.tests.conftest import SessionStateMock
        mock_session = MagicMock()
        mock_session.title = "Test Session"
        mock_turn = MagicMock()
        mock_turn.question = "Test question"
        mock_turn.answer = "Test answer"
        mock_turn.sources = [{"text": "source1", "score": 0.9}]
        mock_turn.reasoning_content = None
        mock_session.history = [mock_turn]
        
        mock_load.return_value = mock_session
        mock_convert.return_value = [{"text": "source1", "score": 0.9, "index": 1}]
        
        mock_st.session_state = SessionStateMock({
            'load_session_id': 'session_123',
            'load_session_path': '/path/to/session.json',
            'messages': [],
            'current_sources_map': {},
        })
        mock_st.rerun = MagicMock()
        mock_st.success = MagicMock()
        
        mock_chat_manager = MagicMock()
        mock_chat_manager.current_session = None
        
        load_history_session(mock_chat_manager)
        
        # 验证会话被加载
        assert mock_chat_manager.current_session == mock_session
        # 验证消息被添加
        assert len(mock_st.session_state['messages']) == 2  # user + assistant
        assert mock_st.session_state['messages'][0]['role'] == 'user'
        assert mock_st.session_state['messages'][1]['role'] == 'assistant'
        # 验证加载标记被清除
        assert 'load_session_id' not in mock_st.session_state
        assert 'load_session_path' not in mock_st.session_state
        mock_st.rerun.assert_called_once()
        mock_st.success.assert_called_once()
    
    @patch('frontend.components.session_loader.st')
    @patch('frontend.components.session_loader.load_session_from_file')
    @patch('frontend.components.session_loader.convert_sources_to_dict')
    def test_load_history_session_with_reasoning(self, mock_convert, mock_load, mock_st):
        """测试加载包含推理链的会话"""
        from frontend.tests.conftest import SessionStateMock
        mock_session = MagicMock()
        mock_session.title = "Test Session"
        mock_turn = MagicMock()
        mock_turn.question = "Test question"
        mock_turn.answer = "Test answer"
        mock_turn.sources = []
        mock_turn.reasoning_content = "Reasoning chain"
        mock_session.history = [mock_turn]
        
        mock_load.return_value = mock_session
        mock_convert.return_value = []
        
        mock_st.session_state = SessionStateMock({
            'load_session_id': 'session_123',
            'load_session_path': '/path/to/session.json',
            'messages': [],
            'current_sources_map': {},
        })
        mock_st.rerun = MagicMock()
        mock_st.success = MagicMock()
        
        mock_chat_manager = MagicMock()
        mock_chat_manager.current_session = None
        
        load_history_session(mock_chat_manager)
        
        # 验证推理链被添加到消息中
        assistant_msg = mock_st.session_state['messages'][1]
        assert assistant_msg['reasoning_content'] == "Reasoning chain"
    
    @patch('frontend.components.session_loader.st')
    @patch('frontend.components.session_loader.load_session_from_file')
    def test_load_history_session_failure(self, mock_load, mock_st):
        """测试加载失败"""
        mock_load.return_value = None
        
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'load_session_id': 'session_123',
            'load_session_path': '/path/to/session.json',
        })
        mock_st.rerun = MagicMock()
        mock_st.error = MagicMock()
        
        mock_chat_manager = MagicMock()
        
        load_history_session(mock_chat_manager)
        
        # 验证错误消息被显示
        mock_st.error.assert_called_once()
        # 验证加载标记被清除
        assert 'load_session_id' not in mock_st.session_state
        assert 'load_session_path' not in mock_st.session_state
        mock_st.rerun.assert_called_once()

