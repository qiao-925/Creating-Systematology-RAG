"""
测试 frontend/components/query_handler.py
对应源文件：frontend/components/query_handler.py
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from frontend.components.query_handler import handle_user_queries


class TestQueryHandler:
    """测试查询处理路由"""
    
    @patch('frontend.components.query_handler.st')
    @patch('frontend.components.query_handler.handle_non_streaming_query')
    def test_handle_user_queries_pending_query(self, mock_non_streaming, mock_st):
        """测试处理待处理的查询"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'pending_query': 'Test question',
            'messages': [],
        })
        
        mock_rag_service = MagicMock()
        mock_chat_manager = MagicMock()
        
        handle_user_queries(mock_rag_service, mock_chat_manager)
        
        # 验证非流式查询被调用
        mock_non_streaming.assert_called_once_with(mock_rag_service, mock_chat_manager, 'Test question')
        # 验证待处理标记被清除
        assert 'pending_query' not in mock_st.session_state
    
    @patch('frontend.components.query_handler.st')
    @patch('frontend.components.query_handler.handle_non_streaming_query')
    def test_handle_user_queries_selected_question(self, mock_non_streaming, mock_st):
        """测试处理选中的问题"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'selected_question': 'Selected question',
            'messages': [],
        })
        
        mock_rag_service = MagicMock()
        mock_chat_manager = MagicMock()
        
        handle_user_queries(mock_rag_service, mock_chat_manager)
        
        # 验证非流式查询被调用
        mock_non_streaming.assert_called_once_with(mock_rag_service, mock_chat_manager, 'Selected question')
        # 验证选中问题被清除
        assert mock_st.session_state['selected_question'] is None
    
    @patch('frontend.components.query_handler.st')
    @patch('src.ui.chat_input.deepseek_style_chat_input')
    @patch('frontend.components.query_handler.handle_streaming_query')
    def test_handle_user_queries_user_input(self, mock_streaming, mock_chat_input, mock_st):
        """测试处理用户输入（流式）"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'messages': [{"role": "user", "content": "Previous message"}],
        })
        mock_chat_input.return_value = "User input"
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_chat_msg = MagicMock()
        mock_st.chat_message.return_value.__enter__ = MagicMock(return_value=mock_chat_msg)
        mock_st.chat_message.return_value.__exit__ = MagicMock(return_value=False)
        
        mock_rag_service = MagicMock()
        mock_chat_manager = MagicMock()
        
        handle_user_queries(mock_rag_service, mock_chat_manager)
        
        # 验证流式查询被调用
        mock_streaming.assert_called_once_with(mock_chat_manager, "User input")
        # 验证用户消息被添加
        assert len(mock_st.session_state['messages']) == 2
        assert mock_st.session_state['messages'][1]['role'] == 'user'
        assert mock_st.session_state['messages'][1]['content'] == "User input"
    
    @patch('frontend.components.query_handler.st')
    @patch('src.ui.chat_input.deepseek_style_chat_input')
    def test_handle_user_queries_no_input(self, mock_chat_input, mock_st):
        """测试没有用户输入时不处理"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'messages': [{"role": "user", "content": "Previous message"}],
        })
        mock_chat_input.return_value = None
        
        mock_rag_service = MagicMock()
        mock_chat_manager = MagicMock()
        
        handle_user_queries(mock_rag_service, mock_chat_manager)
        
        # 验证没有调用任何查询处理函数
        # （这里无法直接验证，但可以通过检查状态来间接验证）

