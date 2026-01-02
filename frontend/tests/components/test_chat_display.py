"""
测试 frontend/components/chat_display.py
对应源文件：frontend/components/chat_display.py
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from frontend.components.chat_display import render_chat_interface, render_chat_history


class TestChatDisplay:
    """测试对话显示组件"""
    
    @patch('frontend.components.chat_display.st')
    @patch('frontend.components.session_loader.load_history_session')
    @patch('frontend.components.chat_display.get_chat_title')
    @patch('frontend.components.chat_display.initialize_sources_map')
    @patch('frontend.components.quick_start.render_quick_start')
    def test_render_chat_interface_no_messages(self, mock_quick_start, mock_init_sources, 
                                                 mock_get_title, mock_load_session, mock_st):
        """测试没有消息时显示快速开始"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({'messages': []})
        mock_get_title.return_value = None
        
        mock_rag_service = MagicMock()
        mock_chat_manager = MagicMock()
        
        render_chat_interface(mock_rag_service, mock_chat_manager)
        
        # 验证快速开始被调用
        mock_quick_start.assert_called_once()
        # 验证历史会话加载被调用
        mock_load_session.assert_called_once_with(mock_chat_manager)
    
    @patch('frontend.components.chat_display.st')
    @patch('frontend.components.session_loader.load_history_session')
    @patch('frontend.components.chat_display.get_chat_title')
    @patch('frontend.components.chat_display.initialize_sources_map')
    @patch('frontend.components.chat_display.render_chat_history')
    def test_render_chat_interface_with_messages(self, mock_render_history, mock_init_sources,
                                                  mock_get_title, mock_load_session, mock_st):
        """测试有消息时显示对话历史"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'messages': [{"role": "user", "content": "test"}],
        })
        mock_get_title.return_value = "Test Title"
        
        mock_rag_service = MagicMock()
        mock_chat_manager = MagicMock()
        
        render_chat_interface(mock_rag_service, mock_chat_manager)
        
        # 验证对话历史被调用
        mock_render_history.assert_called_once()
        # 验证来源映射被初始化
        mock_init_sources.assert_called_once()
    
    @patch('frontend.components.chat_display.st')
    @patch('frontend.components.chat_display.format_answer_with_citation_links')
    @patch('frontend.components.chat_display.display_sources_below_message')
    def test_render_chat_history_user_message(self, mock_display_sources, mock_format_answer, mock_st):
        """测试渲染用户消息"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'messages': [
                {"role": "user", "content": "User question"}
            ],
            'current_sources_map': {},
            'current_reasoning_map': {},
        })
        left_spacer = MagicMock()
        center_col = MagicMock()
        right_spacer = MagicMock()
        mock_st.columns.return_value = [left_spacer, center_col, right_spacer]
        
        # Mock center_col context manager
        center_col.__enter__ = MagicMock(return_value=center_col)
        center_col.__exit__ = MagicMock(return_value=False)
        
        # Mock chat_message context manager
        mock_chat_msg = MagicMock()
        mock_chat_msg_context = MagicMock()
        mock_chat_msg_context.__enter__ = MagicMock(return_value=mock_chat_msg)
        mock_chat_msg_context.__exit__ = MagicMock(return_value=False)
        mock_st.chat_message.return_value = mock_chat_msg_context
        
        # Mock st.markdown (called inside center_col)
        mock_st.markdown = MagicMock()
        
        render_chat_history()
        
        # 验证用户消息被渲染（st.markdown 在 center_col 内部被调用）
        # 由于代码结构是 with center_col: ... st.markdown(...)，我们需要验证 markdown 被调用
        assert mock_st.markdown.called
        # 验证 markdown 被调用时传入了用户消息内容
        mock_st.markdown.assert_any_call("User question")
    
    @patch('frontend.components.chat_display.st')
    @patch('frontend.components.chat_display.format_answer_with_citation_links')
    @patch('frontend.components.chat_display.display_sources_below_message')
    def test_render_chat_history_assistant_message_with_sources(self, mock_display_sources, 
                                                                  mock_format_answer, mock_st):
        """测试渲染带来源的AI消息"""
        from frontend.tests.conftest import SessionStateMock
        message = {
            "role": "assistant",
            "content": "Answer with [1] citation",
            "sources": [{"text": "source1", "score": 0.9}]
        }
        # 计算正确的 message_id
        message_id = f"msg_0_{hash(str(message))}"
        mock_st.session_state = SessionStateMock({
            'messages': [message],
            'current_sources_map': {
                message_id: [{"text": "source1", "score": 0.9, "index": 1}]
            },
            'current_reasoning_map': {},
        })
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_chat_msg = MagicMock()
        mock_chat_msg.__enter__ = MagicMock(return_value=mock_chat_msg)
        mock_chat_msg.__exit__ = MagicMock(return_value=False)
        mock_st.chat_message.return_value = mock_chat_msg
        mock_format_answer.return_value = "Formatted answer"
        
        render_chat_history()
        
        # 验证格式化函数被调用
        mock_format_answer.assert_called_once()
        # 验证来源被显示
        mock_display_sources.assert_called_once()
    
    @patch('frontend.components.chat_display.st')
    @patch('frontend.components.chat_display.format_answer_with_citation_links')
    @patch('frontend.components.chat_display.display_sources_below_message')
    def test_render_chat_history_with_reasoning(self, mock_display_sources, mock_format_answer, mock_st):
        """测试渲染带推理链的消息"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'messages': [
                {
                    "role": "assistant",
                    "content": "Answer",
                    "reasoning_content": "Reasoning chain"
                }
            ],
            'current_sources_map': {},
            'current_reasoning_map': {},
        })
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_chat_msg = MagicMock()
        mock_expander = MagicMock()
        mock_st.chat_message.return_value.__enter__ = MagicMock(return_value=mock_chat_msg)
        mock_st.chat_message.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.expander.return_value.__enter__ = MagicMock(return_value=mock_expander)
        mock_st.expander.return_value.__exit__ = MagicMock(return_value=False)
        
        render_chat_history()
        
        # 验证推理链展开器被调用
        mock_st.expander.assert_called_once()

