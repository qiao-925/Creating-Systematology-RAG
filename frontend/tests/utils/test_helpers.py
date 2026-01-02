"""
测试 frontend/utils/helpers.py
对应源文件：frontend/utils/helpers.py
"""

import pytest
from unittest.mock import MagicMock, patch
from frontend.utils.helpers import get_chat_title, display_trace_info


class TestHelpers:
    """测试辅助函数"""
    
    def test_get_chat_title_empty_messages(self):
        """测试空消息列表"""
        result = get_chat_title([])
        assert result is None
    
    def test_get_chat_title_no_user_message(self):
        """测试没有用户消息"""
        messages = [
            {"role": "assistant", "content": "Hello"}
        ]
        result = get_chat_title(messages)
        assert result is None
    
    def test_get_chat_title_short_message(self):
        """测试短消息（<=50字符）"""
        messages = [
            {"role": "user", "content": "What is RAG?"}
        ]
        result = get_chat_title(messages)
        assert result == "What is RAG?"
    
    def test_get_chat_title_long_message(self):
        """测试长消息（>50字符）"""
        long_content = "A" * 60
        messages = [
            {"role": "user", "content": long_content}
        ]
        result = get_chat_title(messages)
        assert result == "A" * 50 + "..."
    
    def test_get_chat_title_exactly_50_chars(self):
        """测试恰好50字符的消息"""
        content = "A" * 50
        messages = [
            {"role": "user", "content": content}
        ]
        result = get_chat_title(messages)
        assert result == content
    
    def test_get_chat_title_first_user_message(self):
        """测试多个消息时取第一个用户消息"""
        messages = [
            {"role": "assistant", "content": "Hello"},
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "Answer"},
            {"role": "user", "content": "Second question"},
        ]
        result = get_chat_title(messages)
        assert result == "First question"
    
    def test_get_chat_title_empty_content(self):
        """测试空内容的消息"""
        messages = [
            {"role": "user", "content": ""}
        ]
        result = get_chat_title(messages)
        assert result is None
    
    @patch('frontend.utils.helpers.st')
    def test_display_trace_info_empty(self, mock_st):
        """测试空追踪信息"""
        display_trace_info({})
        # 应该不显示任何内容
        mock_st.expander.assert_not_called()
    
    @patch('frontend.utils.helpers.st')
    def test_display_trace_info_basic(self, mock_st):
        """测试基本追踪信息"""
        trace_info = {
            'total_time': 1.5,
            'retrieval': {
                'time_cost': 0.5,
                'chunks_retrieved': 10,
                'top_k': 5,
                'avg_score': 0.85,
            },
            'llm_generation': {
                'model': 'test-model',
                'response_length': 100,
            },
        }
        
        mock_expander = MagicMock()
        mock_expander.__enter__ = MagicMock(return_value=mock_expander)
        mock_expander.__exit__ = MagicMock(return_value=False)
        mock_st.expander.return_value = mock_expander
        # st.columns(3) 返回3个列，st.columns(2) 返回2个列
        def columns_side_effect(*args, **kwargs):
            if len(args) > 0 and args[0] == 3:
                return [MagicMock(), MagicMock(), MagicMock()]
            elif len(args) > 0 and args[0] == 2:
                return [MagicMock(), MagicMock()]
            return [MagicMock(), MagicMock(), MagicMock()]
        mock_st.columns.side_effect = columns_side_effect
        
        display_trace_info(trace_info)
        
        # 验证 expander 被调用
        mock_st.expander.assert_called_once()
    
    @patch('frontend.utils.helpers.st')
    def test_display_trace_info_missing_fields(self, mock_st):
        """测试缺少某些字段的追踪信息"""
        trace_info = {
            'total_time': 1.0,
            # 缺少 retrieval 和 llm_generation
        }
        
        mock_expander = MagicMock()
        mock_expander.__enter__ = MagicMock(return_value=mock_expander)
        mock_expander.__exit__ = MagicMock(return_value=False)
        mock_st.expander.return_value = mock_expander
        # st.columns(3) 返回3个列，st.columns(2) 返回2个列
        def columns_side_effect(*args, **kwargs):
            if len(args) > 0 and args[0] == 3:
                return [MagicMock(), MagicMock(), MagicMock()]
            elif len(args) > 0 and args[0] == 2:
                return [MagicMock(), MagicMock()]
            return [MagicMock(), MagicMock(), MagicMock()]
        mock_st.columns.side_effect = columns_side_effect
        
        display_trace_info(trace_info)
        
        # 应该能正常处理，不抛出异常
        mock_st.expander.assert_called_once()

