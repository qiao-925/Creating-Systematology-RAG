"""
测试 frontend/components/query_handler/streaming.py
对应源文件：frontend/components/query_handler/streaming.py
"""

import pytest
from unittest.mock import MagicMock, patch, Mock, AsyncMock
from frontend.components.query_handler.streaming import handle_streaming_query


class TestStreaming:
    """测试流式查询处理"""
    
    @patch('frontend.components.query_handler.streaming.st')
    @patch('frontend.components.query_handler.streaming.asyncio')
    def test_handle_streaming_query_success(self, mock_asyncio, mock_st):
        """测试成功处理流式查询"""
        from frontend.tests.conftest import SessionStateMock
        from unittest.mock import AsyncMock
        mock_st.session_state = SessionStateMock({
            'messages': [],
            'current_sources_map': {},
            'current_reasoning_map': {},
        })
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_chat_msg = MagicMock()
        mock_placeholder = MagicMock()
        mock_chat_msg.__enter__ = MagicMock(return_value=mock_chat_msg)
        mock_chat_msg.__exit__ = MagicMock(return_value=False)
        mock_st.chat_message.return_value = mock_chat_msg
        mock_st.empty.return_value = mock_placeholder
        
        # Mock 异步流
        async def mock_stream():
            yield {'type': 'token', 'data': 'Test '}
            yield {'type': 'token', 'data': 'answer'}
            yield {'type': 'sources', 'data': [{"text": "source1", "score": 0.9}]}
            yield {'type': 'done', 'data': {'answer': 'Test answer'}}
        
        mock_chat_manager = MagicMock()
        mock_chat_manager.stream_chat = AsyncMock(return_value=mock_stream())
        
        # Mock asyncio.run
        mock_asyncio.run = MagicMock()
        
        handle_streaming_query(mock_chat_manager, "Test question")
        
        # 验证基本组件被调用
        mock_st.columns.assert_called_once()
        mock_st.chat_message.assert_called_once_with("assistant")
        mock_st.empty.assert_called_once()
    
    @patch('frontend.components.query_handler.streaming.st')
    @patch('frontend.components.query_handler.streaming.asyncio')
    @patch('builtins.__import__')
    def test_handle_streaming_query_with_reasoning(self, mock_import, mock_asyncio, mock_st):
        """测试带推理链的流式查询"""
        from frontend.tests.conftest import SessionStateMock
        from unittest.mock import AsyncMock
        # Mock nest_asyncio import to raise ImportError (simulating it's not installed)
        def import_side_effect(name, *args, **kwargs):
            if name == 'nest_asyncio':
                raise ImportError("No module named 'nest_asyncio'")
            return __import__(name, *args, **kwargs)
        mock_import.side_effect = import_side_effect
        
        mock_st.session_state = SessionStateMock({
            'messages': [],
            'current_sources_map': {},
            'current_reasoning_map': {},
        })
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_chat_msg = MagicMock()
        mock_placeholder = MagicMock()
        mock_chat_msg.__enter__ = MagicMock(return_value=mock_chat_msg)
        mock_chat_msg.__exit__ = MagicMock(return_value=False)
        mock_st.chat_message.return_value = mock_chat_msg
        mock_st.empty.return_value = mock_placeholder
        
        # Mock 异步流（包含推理链）
        async def mock_stream():
            yield {'type': 'token', 'data': 'Test '}
            yield {'type': 'reasoning', 'data': 'Reasoning chain'}
            yield {'type': 'done', 'data': {'answer': 'Test answer'}}
        
        mock_chat_manager = MagicMock()
        mock_chat_manager.stream_chat = AsyncMock(return_value=mock_stream())
        
        mock_asyncio.run = MagicMock()
        
        handle_streaming_query(mock_chat_manager, "Test question")
        
        # 验证基本组件被调用
        mock_st.columns.assert_called_once()
    
    @patch('frontend.components.query_handler.streaming.st')
    @patch('frontend.components.query_handler.streaming.asyncio')
    @patch('builtins.__import__')
    def test_handle_streaming_query_error(self, mock_import, mock_asyncio, mock_st):
        """测试流式查询错误处理"""
        from frontend.tests.conftest import SessionStateMock
        from unittest.mock import AsyncMock
        # Mock nest_asyncio import to raise ImportError (simulating it's not installed)
        def import_side_effect(name, *args, **kwargs):
            if name == 'nest_asyncio':
                raise ImportError("No module named 'nest_asyncio'")
            return __import__(name, *args, **kwargs)
        mock_import.side_effect = import_side_effect
        
        mock_st.session_state = SessionStateMock({
            'messages': [],
            'current_sources_map': {},
            'current_reasoning_map': {},
        })
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_chat_msg = MagicMock()
        mock_placeholder = MagicMock()
        mock_chat_msg.__enter__ = MagicMock(return_value=mock_chat_msg)
        mock_chat_msg.__exit__ = MagicMock(return_value=False)
        mock_st.chat_message.return_value = mock_chat_msg
        mock_st.empty.return_value = mock_placeholder
        mock_st.error = MagicMock()
        
        # Mock 抛出异常
        mock_chat_manager = MagicMock()
        mock_chat_manager.stream_chat = AsyncMock(side_effect=Exception("Stream error"))
        
        mock_asyncio.run = MagicMock()
        
        handle_streaming_query(mock_chat_manager, "Test question")
        
        # 验证错误处理
        mock_st.error.assert_called()

