"""
测试 frontend/components/query_handler/non_streaming.py
对应源文件：frontend/components/query_handler/non_streaming.py
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from frontend.components.query_handler.non_streaming import handle_non_streaming_query


class TestNonStreaming:
    """测试非流式查询处理"""
    
    @patch('frontend.components.query_handler.non_streaming.st')
    @patch('frontend.components.query_handler.non_streaming.convert_sources_to_dict')
    @patch('frontend.components.query_handler.non_streaming.save_message_to_history')
    @patch('frontend.components.query_handler.non_streaming.format_answer_with_citation_links')
    @patch('frontend.components.query_handler.non_streaming.display_sources_below_message')
    def test_handle_non_streaming_query_success(self, mock_display_sources, mock_format_answer,
                                                  mock_save_history, mock_convert, mock_st):
        """测试成功处理非流式查询"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'messages': [],
            'current_sources_map': {},
            'current_reasoning_map': {},
        })
        mock_chat_msg = MagicMock()
        mock_spinner = MagicMock()
        mock_st.chat_message.return_value.__enter__ = MagicMock(return_value=mock_chat_msg)
        mock_st.chat_message.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.spinner.return_value.__enter__ = MagicMock(return_value=mock_spinner)
        mock_st.spinner.return_value.__exit__ = MagicMock(return_value=False)
        
        # Mock RAGService 响应
        mock_response = MagicMock()
        mock_response.answer = "Test answer"
        mock_response.sources = [{"text": "source1", "score": 0.9}]
        mock_response.metadata = {}
        
        mock_rag_service = MagicMock()
        mock_rag_service.query.return_value = mock_response
        
        mock_chat_manager = MagicMock()
        mock_chat_manager.current_session = None
        mock_chat_manager.auto_save = False
        
        handle_non_streaming_query(mock_rag_service, mock_chat_manager, "Test question")
        
        # 验证查询被调用
        mock_rag_service.query.assert_called_once()
        # 验证消息被保存
        mock_save_history.assert_called_once()
        # 验证答案被显示（可能通过 format_answer_with_citation_links 或直接 markdown）
        assert mock_chat_msg.markdown.called or mock_format_answer.called
    
    @patch('frontend.components.query_handler.non_streaming.st')
    @patch('frontend.components.query_handler.non_streaming.convert_sources_to_dict')
    @patch('frontend.components.query_handler.non_streaming.save_message_to_history')
    @patch('frontend.components.query_handler.non_streaming.format_answer_with_citation_links')
    @patch('frontend.components.query_handler.non_streaming.display_sources_below_message')
    def test_handle_non_streaming_query_with_sources(self, mock_display_sources, mock_format_answer,
                                                      mock_save_history, mock_convert, mock_st):
        """测试带来源的非流式查询"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'messages': [],
            'current_sources_map': {},
            'current_reasoning_map': {},
        })
        mock_chat_msg = MagicMock()
        mock_spinner = MagicMock()
        mock_st.chat_message.return_value.__enter__ = MagicMock(return_value=mock_chat_msg)
        mock_st.chat_message.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.spinner.return_value.__enter__ = MagicMock(return_value=mock_spinner)
        mock_st.spinner.return_value.__exit__ = MagicMock(return_value=False)
        
        mock_sources = [{"text": "source1", "score": 0.9, "index": 1}]
        mock_convert.return_value = mock_sources
        mock_format_answer.return_value = "Formatted answer with [1]"
        
        mock_response = MagicMock()
        mock_response.answer = "Test answer"
        mock_response.sources = [{"text": "source1", "score": 0.9}]
        mock_response.metadata = {}
        
        mock_rag_service = MagicMock()
        mock_rag_service.query.return_value = mock_response
        
        mock_chat_manager = MagicMock()
        mock_chat_manager.current_session = None
        mock_chat_manager.auto_save = False
        
        handle_non_streaming_query(mock_rag_service, mock_chat_manager, "Test question")
        
        # 验证来源被显示
        mock_display_sources.assert_called_once()
        mock_format_answer.assert_called_once()
    
    @patch('frontend.components.query_handler.non_streaming.st')
    @patch('frontend.components.query_handler.non_streaming.convert_sources_to_dict')
    @patch('frontend.components.query_handler.non_streaming.save_message_to_history')
    def test_handle_non_streaming_query_error(self, mock_save_history, mock_convert, mock_st):
        """测试非流式查询错误处理"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'messages': [],
            'current_sources_map': {},
            'current_reasoning_map': {},
        })
        mock_chat_msg = MagicMock()
        mock_spinner = MagicMock()
        mock_st.chat_message.return_value.__enter__ = MagicMock(return_value=mock_chat_msg)
        mock_st.chat_message.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.spinner.return_value.__enter__ = MagicMock(return_value=mock_spinner)
        mock_st.spinner.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.error = MagicMock()
        
        mock_rag_service = MagicMock()
        mock_rag_service.query.side_effect = Exception("Query error")
        
        mock_chat_manager = MagicMock()
        
        handle_non_streaming_query(mock_rag_service, mock_chat_manager, "Test question")
        
        # 验证错误被显示
        assert mock_st.error.call_count >= 1

