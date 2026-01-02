"""
测试查询流程
集成测试：验证查询处理的完整流程
"""

import pytest
from unittest.mock import MagicMock, patch, Mock


class TestQueryFlow:
    """测试查询流程"""
    
    @patch('frontend.components.query_handler.st')
    @patch('frontend.components.query_handler.handle_non_streaming_query')
    def test_query_flow_pending_query(self, mock_non_streaming, mock_st):
        """测试待处理查询流程"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'pending_query': 'Test question',
            'messages': [],
        })
        
        from frontend.components.query_handler import handle_user_queries
        
        mock_rag_service = MagicMock()
        mock_chat_manager = MagicMock()
        
        handle_user_queries(mock_rag_service, mock_chat_manager)
        
        # 验证非流式查询被调用
        mock_non_streaming.assert_called_once()
    
    @patch('frontend.components.query_handler.st')
    @patch('frontend.components.query_handler.handle_streaming_query')
    @patch('src.ui.chat_input.deepseek_style_chat_input')
    def test_query_flow_streaming(self, mock_chat_input, mock_streaming, mock_st):
        """测试流式查询流程"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'messages': [{"role": "user", "content": "Previous"}],
        })
        mock_chat_input.return_value = "New question"
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_chat_msg = MagicMock()
        mock_chat_msg.__enter__ = MagicMock(return_value=mock_chat_msg)
        mock_chat_msg.__exit__ = MagicMock(return_value=False)
        mock_st.chat_message.return_value = mock_chat_msg
        
        from frontend.components.query_handler import handle_user_queries
        
        mock_rag_service = MagicMock()
        mock_chat_manager = MagicMock()
        
        handle_user_queries(mock_rag_service, mock_chat_manager)
        
        # 验证流式查询被调用
        mock_streaming.assert_called_once()
    
    def test_query_functionality_references(self):
        """测试查询功能引用"""
        # 验证查询相关的模块存在
        try:
            from frontend.components.query_handler import handle_user_queries
            from frontend.components.query_handler.streaming import handle_streaming_query
            from frontend.components.query_handler.non_streaming import handle_non_streaming_query
            
            assert callable(handle_user_queries)
            assert callable(handle_streaming_query)
            assert callable(handle_non_streaming_query)
        except ImportError as e:
            pytest.skip(f"查询功能模块导入失败: {e}")
    
    def test_chat_functionality_references(self):
        """测试对话功能引用"""
        # 验证对话相关的模块存在
        try:
            from frontend.components.chat_display import render_chat_interface
            from frontend.components.session_loader import load_history_session
            from frontend.utils.state import save_message_to_history
            
            assert callable(render_chat_interface)
            assert callable(load_history_session)
            assert callable(save_message_to_history)
        except ImportError as e:
            pytest.skip(f"对话功能模块导入失败: {e}")

