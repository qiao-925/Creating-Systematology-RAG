"""
测试 frontend/components/quick_start.py
对应源文件：frontend/components/quick_start.py
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from frontend.components.quick_start import render_quick_start


class TestQuickStart:
    """测试 render_quick_start 函数"""
    
    @patch('frontend.components.quick_start.st')
    @patch('frontend.components.quick_start.deepseek_style_chat_input')
    def test_render_quick_start_structure(self, mock_chat_input, mock_st):
        """测试快速开始界面结构"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({'messages': []})
        # st.columns([2, 6, 2]) 返回3个列，需要正确解包
        left_spacer = MagicMock()
        center_col = MagicMock()
        right_spacer = MagicMock()
        # 第一次调用返回3个列，第二次调用（在center_col内部）返回2个列
        def columns_side_effect(*args, **kwargs):
            if len(args) > 0 and isinstance(args[0], list) and len(args[0]) == 3:
                return [left_spacer, center_col, right_spacer]
            elif len(args) > 0 and (args[0] == 2 or (isinstance(args[0], list) and len(args[0]) == 2)):
                return [MagicMock(), MagicMock()]
            return [MagicMock(), MagicMock(), MagicMock()]
        mock_st.columns.side_effect = columns_side_effect
        mock_st.button.return_value = False
        mock_chat_input.return_value = None
        
        render_quick_start()
        
        # 验证基本组件被调用
        mock_st.markdown.assert_called()
        mock_st.columns.assert_called()
        mock_st.caption.assert_called_once()
    
    @patch('frontend.components.quick_start.st')
    @patch('frontend.components.quick_start.deepseek_style_chat_input')
    def test_render_quick_start_default_questions(self, mock_chat_input, mock_st):
        """测试默认问题按钮"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({'messages': []})
        left_spacer = MagicMock()
        center_col = MagicMock()
        right_spacer = MagicMock()
        def columns_side_effect(*args, **kwargs):
            if len(args) > 0 and isinstance(args[0], list) and len(args[0]) == 3:
                return [left_spacer, center_col, right_spacer]
            elif len(args) > 0 and (args[0] == 2 or (isinstance(args[0], list) and len(args[0]) == 2)):
                return [MagicMock(), MagicMock()]
            return [MagicMock(), MagicMock(), MagicMock()]
        mock_st.columns.side_effect = columns_side_effect
        mock_chat_input.return_value = None
        
        # 模拟按钮被点击
        call_count = [0]
        def button_side_effect(*args, **kwargs):
            if kwargs.get('key', '').startswith('default_q_'):
                call_count[0] += 1
                return call_count[0] == 1  # 只让第一个按钮返回True
        
        mock_st.button.side_effect = button_side_effect
        mock_st.rerun = MagicMock()
        
        render_quick_start()
        
        # 验证按钮被调用（4个默认问题）
        assert mock_st.button.call_count >= 4
    
    @patch('frontend.components.quick_start.st')
    @patch('frontend.components.quick_start.deepseek_style_chat_input')
    def test_render_quick_start_question_click(self, mock_chat_input, mock_st):
        """测试点击默认问题"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({'messages': []})
        left_spacer = MagicMock()
        center_col = MagicMock()
        right_spacer = MagicMock()
        def columns_side_effect(*args, **kwargs):
            if len(args) > 0 and isinstance(args[0], list) and len(args[0]) == 3:
                return [left_spacer, center_col, right_spacer]
            elif len(args) > 0 and (args[0] == 2 or (isinstance(args[0], list) and len(args[0]) == 2)):
                return [MagicMock(), MagicMock()]
            return [MagicMock(), MagicMock(), MagicMock()]
        mock_st.columns.side_effect = columns_side_effect
        mock_chat_input.return_value = None
        mock_st.rerun = MagicMock()
        
        question = "什么是系统科学？它的核心思想是什么？"
        
        # 模拟第一个按钮被点击
        def button_side_effect(*args, **kwargs):
            if kwargs.get('key') == 'default_q_0':
                return True
            return False
        
        mock_st.button.side_effect = button_side_effect
        
        render_quick_start()
        
        # 验证消息被添加
        assert len(mock_st.session_state['messages']) == 1
        assert mock_st.session_state['messages'][0]['role'] == 'user'
        assert mock_st.session_state['messages'][0]['content'] == question
        assert mock_st.session_state['selected_question'] == question
        mock_st.rerun.assert_called_once()
    
    @patch('frontend.components.quick_start.st')
    @patch('frontend.components.quick_start.deepseek_style_chat_input')
    def test_render_quick_start_chat_input(self, mock_chat_input, mock_st):
        """测试输入框输入"""
        from frontend.tests.conftest import SessionStateMock
        mock_st.session_state = SessionStateMock({'messages': []})
        left_spacer = MagicMock()
        center_col = MagicMock()
        right_spacer = MagicMock()
        def columns_side_effect(*args, **kwargs):
            if len(args) > 0 and isinstance(args[0], list) and len(args[0]) == 3:
                return [left_spacer, center_col, right_spacer]
            elif len(args) > 0 and (args[0] == 2 or (isinstance(args[0], list) and len(args[0]) == 2)):
                return [MagicMock(), MagicMock()]
            return [MagicMock(), MagicMock(), MagicMock()]
        mock_st.columns.side_effect = columns_side_effect
        mock_st.button.return_value = False
        mock_st.rerun = MagicMock()
        
        user_input = "用户输入的问题"
        mock_chat_input.return_value = user_input
        
        render_quick_start()
        
        # 验证消息被添加
        assert len(mock_st.session_state['messages']) == 1
        assert mock_st.session_state['messages'][0]['role'] == 'user'
        assert mock_st.session_state['messages'][0]['content'] == user_input
        assert mock_st.session_state['pending_query'] == user_input
        mock_st.rerun.assert_called_once()

