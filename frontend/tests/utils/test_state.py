"""
测试 frontend/utils/state.py
对应源文件：frontend/utils/state.py
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from frontend.utils.state import (
    initialize_app_state,
    initialize_sources_map,
    save_message_to_history,
)


class TestState:
    """测试状态管理函数"""
    
    @patch('frontend.utils.state.st')
    def test_initialize_app_state_new(self, mock_st):
        """测试初始化新的应用状态"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock()
        
        initialize_app_state()
        
        assert 'boot_ready' in mock_st.session_state
        assert mock_st.session_state['boot_ready'] is False
        assert 'messages' in mock_st.session_state
        assert mock_st.session_state['messages'] == []
    
    @patch('frontend.utils.state.st')
    def test_initialize_app_state_existing(self, mock_st):
        """测试已存在状态时不覆盖"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'boot_ready': True,
            'messages': [{"role": "user", "content": "test"}],
        })
        
        initialize_app_state()
        
        # 应该保持原有值
        assert mock_st.session_state['boot_ready'] is True
        assert len(mock_st.session_state['messages']) == 1
    
    @patch('frontend.utils.state.st')
    def test_initialize_sources_map_empty(self, mock_st):
        """测试初始化空的来源映射"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'messages': [],
        })
        
        initialize_sources_map()
        
        assert 'current_sources_map' in mock_st.session_state
        assert 'current_reasoning_map' in mock_st.session_state
        assert mock_st.session_state['current_sources_map'] == {}
        assert mock_st.session_state['current_reasoning_map'] == {}
    
    @patch('frontend.utils.state.st')
    @patch('frontend.utils.state.convert_sources_to_dict')
    def test_initialize_sources_map_with_sources(self, mock_convert, mock_st):
        """测试从历史消息中提取来源"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'messages': [
                {
                    "role": "assistant",
                    "content": "Answer",
                    "sources": [{"text": "source1", "score": 0.9}],
                }
            ],
        })
        mock_convert.return_value = [{"text": "source1", "score": 0.9, "index": 1}]
        
        initialize_sources_map()
        
        assert 'current_sources_map' in mock_st.session_state
        # 验证来源被提取（通过检查 map 不为空）
        assert len(mock_st.session_state['current_sources_map']) > 0
    
    @patch('frontend.utils.state.st')
    def test_initialize_sources_map_with_reasoning(self, mock_st):
        """测试从历史消息中提取推理链"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'messages': [
                {
                    "role": "assistant",
                    "content": "Answer",
                    "reasoning_content": "Reasoning chain",
                }
            ],
        })
        
        initialize_sources_map()
        
        assert 'current_reasoning_map' in mock_st.session_state
        # 验证推理链被提取
        assert len(mock_st.session_state['current_reasoning_map']) > 0
    
    @patch('frontend.utils.state.st')
    def test_save_message_to_history(self, mock_st):
        """测试保存消息到历史"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'messages': [],
            'current_sources_map': {},
            'current_reasoning_map': {},
        })
        
        answer = "Test answer"
        sources = [{"text": "source1", "score": 0.9}]
        
        save_message_to_history(answer, sources)
        
        assert len(mock_st.session_state['messages']) == 1
        msg = mock_st.session_state['messages'][0]
        assert msg['role'] == "assistant"
        assert msg['content'] == answer
        assert msg['sources'] == sources
    
    @patch('frontend.utils.state.st')
    def test_save_message_to_history_with_reasoning(self, mock_st):
        """测试保存带推理链的消息"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'messages': [],
            'current_sources_map': {},
            'current_reasoning_map': {},
        })
        
        answer = "Test answer"
        sources = [{"text": "source1", "score": 0.9}]
        reasoning = "Reasoning chain"
        
        save_message_to_history(answer, sources, reasoning)
        
        assert len(mock_st.session_state['messages']) == 1
        msg = mock_st.session_state['messages'][0]
        assert msg['role'] == "assistant"
        assert msg['content'] == answer
        assert msg['sources'] == sources
        assert msg['reasoning_content'] == reasoning
        assert len(mock_st.session_state['current_reasoning_map']) > 0

