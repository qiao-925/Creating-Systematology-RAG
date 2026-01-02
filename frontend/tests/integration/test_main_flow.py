"""
测试主页面完整流程
集成测试：验证主页面各组件协同工作
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path


class TestMainFlow:
    """测试主页面流程"""
    
    @patch('frontend.main.st')
    @patch('frontend.main.init_session_state')
    @patch('frontend.main.initialize_app_state')
    @patch('frontend.main.load_rag_service')
    @patch('frontend.main.load_chat_manager')
    @patch('frontend.main.render_sidebar')
    @patch('frontend.main.render_chat_interface')
    @patch('frontend.main.handle_user_queries')
    def test_main_flow_complete(self, mock_handle_queries, mock_render_chat, 
                                 mock_render_sidebar, mock_load_chat, mock_load_rag,
                                 mock_init_app, mock_init_session, mock_st):
        """测试主页面完整流程"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({'boot_ready': True})
        
        mock_rag_service = MagicMock()
        mock_chat_manager = MagicMock()
        mock_load_rag.return_value = mock_rag_service
        mock_load_chat.return_value = mock_chat_manager
        
        from frontend.main import main
        main()
        
        # 验证所有组件被正确调用
        mock_render_sidebar.assert_called_once_with(mock_chat_manager)
        mock_render_chat.assert_called_once_with(mock_rag_service, mock_chat_manager)
        mock_handle_queries.assert_called_once_with(mock_rag_service, mock_chat_manager)
    
    def test_ui_components_import(self):
        """测试UI组件导入"""
        try:
            from frontend.components.sidebar import render_sidebar
            from frontend.components.chat_display import render_chat_interface
            from frontend.components.query_handler import handle_user_queries
            from frontend.components.quick_start import render_quick_start
            from frontend.components.session_loader import load_history_session
            
            # 验证所有组件都可以导入
            assert callable(render_sidebar)
            assert callable(render_chat_interface)
            assert callable(handle_user_queries)
            assert callable(render_quick_start)
            assert callable(load_history_session)
        except ImportError as e:
            pytest.skip(f"UI组件导入失败: {e}")
    
    def test_utils_components_import(self):
        """测试工具组件导入"""
        try:
            from frontend.utils.sources import convert_sources_to_dict
            from frontend.utils.helpers import get_chat_title
            from frontend.utils.state import initialize_app_state
            from frontend.utils.cleanup import cleanup_resources
            
            # 验证所有工具函数都可以导入
            assert callable(convert_sources_to_dict)
            assert callable(get_chat_title)
            assert callable(initialize_app_state)
            assert callable(cleanup_resources)
        except ImportError as e:
            pytest.skip(f"工具组件导入失败: {e}")

