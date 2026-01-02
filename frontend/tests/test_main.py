"""
测试 frontend/main.py
对应源文件：frontend/main.py
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path
from frontend.main import main


class TestMain:
    """测试主入口"""
    
    @patch('frontend.main.st')
    @patch('frontend.main.init_session_state')
    @patch('frontend.main.initialize_app_state')
    @patch('frontend.main.load_rag_service')
    @patch('frontend.main.load_chat_manager')
    @patch('frontend.main.render_sidebar')
    @patch('frontend.main.render_chat_interface')
    @patch('frontend.main.handle_user_queries')
    def test_main_initialization(self, mock_handle_queries, mock_render_chat, 
                                  mock_render_sidebar, mock_load_chat, mock_load_rag,
                                  mock_init_app, mock_init_session, mock_st):
        """测试主函数初始化流程"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({'boot_ready': False})
        mock_st.rerun = MagicMock()
        
        mock_rag_service = MagicMock()
        mock_chat_manager = MagicMock()
        mock_load_rag.return_value = mock_rag_service
        mock_load_chat.return_value = mock_chat_manager
        
        main()
        
        # 验证初始化被调用
        mock_init_session.assert_called_once()
        mock_init_app.assert_called_once()
        # 验证启动阶段会 rerun
        mock_st.rerun.assert_called_once()
    
    @patch('frontend.main.st')
    @patch('frontend.main.init_session_state')
    @patch('frontend.main.initialize_app_state')
    @patch('frontend.main.load_rag_service')
    @patch('frontend.main.load_chat_manager')
    @patch('frontend.main.render_sidebar')
    @patch('frontend.main.render_chat_interface')
    @patch('frontend.main.handle_user_queries')
    def test_main_normal_flow(self, mock_handle_queries, mock_render_chat, 
                              mock_render_sidebar, mock_load_chat, mock_load_rag,
                              mock_init_app, mock_init_session, mock_st):
        """测试主函数正常流程"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({'boot_ready': True})
        
        mock_rag_service = MagicMock()
        mock_chat_manager = MagicMock()
        mock_load_rag.return_value = mock_rag_service
        mock_load_chat.return_value = mock_chat_manager
        
        main()
        
        # 验证组件被调用
        mock_render_sidebar.assert_called_once_with(mock_chat_manager)
        mock_render_chat.assert_called_once_with(mock_rag_service, mock_chat_manager)
        mock_handle_queries.assert_called_once_with(mock_rag_service, mock_chat_manager)
    
    @patch('frontend.main.st')
    @patch('frontend.main.init_session_state')
    @patch('frontend.main.initialize_app_state')
    @patch('frontend.main.load_rag_service')
    def test_main_rag_service_failure(self, mock_load_rag, mock_init_app, 
                                      mock_init_session, mock_st):
        """测试RAG服务初始化失败"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({'boot_ready': True})
        mock_load_rag.return_value = None
        mock_st.error = MagicMock()
        
        main()
        
        # 验证错误消息被显示
        mock_st.error.assert_called_once()
    
    @patch('frontend.main.st')
    def test_main_page_config(self, mock_st):
        """测试页面配置"""
        # 验证 app.py 或 main.py 包含页面配置
        main_file = Path(__file__).parent.parent / "main.py"
        if main_file.exists():
            content = main_file.read_text(encoding='utf-8')
            assert 'st.set_page_config' in content

