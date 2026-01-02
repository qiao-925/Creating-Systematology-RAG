"""
测试 frontend/components/sidebar.py
对应源文件：frontend/components/sidebar.py
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from frontend.components.sidebar import render_sidebar


class TestSidebar:
    """测试 render_sidebar 函数"""
    
    @patch('frontend.components.sidebar.st')
    @patch('frontend.components.sidebar.config')
    @patch('frontend.components.sidebar.display_session_history')
    @patch('frontend.components.sidebar.show_settings_dialog')
    def test_render_sidebar_structure(self, mock_show_dialog, mock_display_history, mock_config, mock_st):
        """测试侧边栏渲染结构"""
        mock_config.APP_TITLE = "Test App"
        mock_st.sidebar.__enter__ = MagicMock(return_value=mock_st.sidebar)
        mock_st.sidebar.__exit__ = MagicMock(return_value=False)
        mock_st.button.return_value = False
        mock_st.session_state = {}
        
        mock_chat_manager = MagicMock()
        mock_chat_manager.current_session = None
        
        render_sidebar(mock_chat_manager)
        
        # 验证基本组件被调用
        mock_st.title.assert_called_once()
        mock_st.caption.assert_called_once()
        mock_st.button.assert_called()
    
    @patch('frontend.components.sidebar.st')
    @patch('frontend.components.sidebar.config')
    @patch('frontend.components.sidebar.display_session_history')
    @patch('frontend.components.sidebar.show_settings_dialog')
    def test_render_sidebar_new_chat_button(self, mock_show_dialog, mock_display_history, mock_config, mock_st):
        """测试新对话按钮"""
        mock_config.APP_TITLE = "Test App"
        mock_st.sidebar.__enter__ = MagicMock(return_value=mock_st.sidebar)
        mock_st.sidebar.__exit__ = MagicMock(return_value=False)
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'messages': [{"role": "user", "content": "test"}],
            'current_sources_map': {"key": "value"},
            'current_reasoning_map': {"key": "value"},
        })
        
        # 模拟按钮被点击
        def button_side_effect(*args, **kwargs):
            if kwargs.get('key') == 'new_chat_top':
                return True
            return False
        
        mock_st.button.side_effect = button_side_effect
        mock_st.rerun = MagicMock()
        
        mock_chat_manager = MagicMock()
        mock_chat_manager.start_session = MagicMock()
        mock_chat_manager.current_session = None
        
        render_sidebar(mock_chat_manager)
        
        # 验证新会话被创建
        mock_chat_manager.start_session.assert_called_once()
        # 验证消息被清空
        assert mock_st.session_state['messages'] == []
        assert mock_st.session_state['current_sources_map'] == {}
        assert mock_st.session_state['current_reasoning_map'] == {}
    
    @patch('frontend.components.sidebar.st')
    @patch('frontend.components.sidebar.config')
    @patch('frontend.components.sidebar.display_session_history')
    @patch('frontend.components.sidebar.show_settings_dialog')
    def test_render_sidebar_settings_button(self, mock_show_dialog, mock_display_history, mock_config, mock_st):
        """测试设置按钮"""
        mock_config.APP_TITLE = "Test App"
        mock_st.sidebar.__enter__ = MagicMock(return_value=mock_st.sidebar)
        mock_st.sidebar.__exit__ = MagicMock(return_value=False)
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({
            'show_settings_dialog': False,
        })
        
        # 模拟设置按钮被点击
        def button_side_effect(*args, **kwargs):
            if kwargs.get('key') == 'settings_button':
                mock_st.session_state['show_settings_dialog'] = True
                return True
            return False
        
        mock_st.button.side_effect = button_side_effect
        
        mock_chat_manager = MagicMock()
        mock_chat_manager.current_session = None
        
        render_sidebar(mock_chat_manager)
        
        # 验证设置对话框被调用
        mock_show_dialog.assert_called_once()
    
    @patch('frontend.components.sidebar.st')
    @patch('frontend.components.sidebar.config')
    @patch('frontend.components.sidebar.display_session_history')
    @patch('frontend.components.sidebar.show_settings_dialog')
    def test_render_sidebar_with_current_session(self, mock_show_dialog, mock_display_history, mock_config, mock_st):
        """测试有当前会话时的渲染"""
        mock_config.APP_TITLE = "Test App"
        mock_st.sidebar.__enter__ = MagicMock(return_value=mock_st.sidebar)
        mock_st.sidebar.__exit__ = MagicMock(return_value=False)
        mock_st.button.return_value = False
        mock_st.session_state = {}
        
        mock_session = MagicMock()
        mock_session.session_id = "session_123"
        
        mock_chat_manager = MagicMock()
        mock_chat_manager.current_session = mock_session
        
        render_sidebar(mock_chat_manager)
        
        # 验证 display_session_history 被调用，并传入了当前会话ID
        mock_display_history.assert_called_once_with(
            user_email=None,
            current_session_id="session_123"
        )

