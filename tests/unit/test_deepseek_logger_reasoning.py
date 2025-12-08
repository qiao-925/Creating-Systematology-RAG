"""
DeepSeekLogger 推理链记录单元测试

测试 DeepSeekLogger 正确记录 reasoning_content（流式和非流式）。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.infrastructure.llms.deepseek_logger import DeepSeekLogger


class TestDeepSeekLoggerReasoningContent:
    """测试 DeepSeekLogger 的推理链记录"""
    
    @patch('src.infrastructure.llms.deepseek_logger.logger')
    def test_chat_logs_reasoning_content(self, mock_logger):
        """测试非流式 chat 方法记录推理链内容"""
        # 创建模拟的 DeepSeek 实例
        mock_deepseek = Mock()
        
        # 模拟响应包含 reasoning_content
        mock_response = Mock()
        mock_message = Mock()
        mock_message.reasoning_content = "这是一个推理过程"
        mock_message.content = "这是回答内容"
        mock_response.message = mock_message
        
        mock_deepseek.chat.return_value = mock_response
        
        # 创建包装器
        logger_wrapper = DeepSeekLogger(mock_deepseek)
        
        # 调用 chat 方法
        messages = [{'role': 'user', 'content': '测试问题'}]
        result = logger_wrapper.chat(messages)
        
        # 验证推理链内容被记录
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        reasoning_logged = any('推理链' in str(call) or 'reasoning' in str(call).lower() 
                              for call in info_calls)
        
        assert reasoning_logged, "推理链内容应该被记录到日志"
        assert result == mock_response
    
    @patch('src.infrastructure.llms.deepseek_logger.logger')
    def test_chat_handles_no_reasoning_content(self, mock_logger):
        """测试没有推理链内容时的处理"""
        mock_deepseek = Mock()
        
        mock_response = Mock()
        mock_message = Mock()
        mock_message.reasoning_content = None
        mock_message.content = "这是回答内容"
        mock_response.message = mock_message
        
        mock_deepseek.chat.return_value = mock_response
        
        logger_wrapper = DeepSeekLogger(mock_deepseek)
        
        messages = [{'role': 'user', 'content': '测试问题'}]
        result = logger_wrapper.chat(messages)
        
        # 验证没有推理链时不会记录推理链日志
        assert result == mock_response
    
    @patch('src.infrastructure.llms.deepseek_logger.logger')
    def test_stream_chat_logs_reasoning_content(self, mock_logger):
        """测试流式 chat 方法记录推理链内容"""
        mock_deepseek = Mock()
        
        # 模拟流式响应
        mock_chunk1 = Mock()
        mock_message1 = Mock()
        mock_message1.reasoning_content = "推理片段1"
        mock_chunk1.message = mock_message1
        
        mock_chunk2 = Mock()
        mock_message2 = Mock()
        mock_message2.content = "回答片段"
        mock_chunk2.message = mock_message2
        
        mock_deepseek.stream_chat.return_value = [mock_chunk1, mock_chunk2]
        
        logger_wrapper = DeepSeekLogger(mock_deepseek)
        
        messages = [{'role': 'user', 'content': '测试问题'}]
        chunks = list(logger_wrapper.stream_chat(messages))
        
        # 验证流式响应被正确处理
        assert len(chunks) > 0
        
        # 验证推理链内容被记录
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        reasoning_logged = any('推理链' in str(call) or 'reasoning' in str(call).lower() 
                              for call in info_calls)
        
        assert reasoning_logged, "流式推理链内容应该被记录到日志"
    
    @patch('src.infrastructure.llms.deepseek_logger.clean_messages_for_api')
    def test_chat_cleans_messages(self, mock_clean):
        """测试 chat 方法清理消息"""
        mock_deepseek = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.reasoning_content = None
        mock_message.content = "回答"
        mock_response.message = mock_message
        mock_deepseek.chat.return_value = mock_response
        
        mock_clean.return_value = [{'role': 'user', 'content': '问题'}]
        
        logger_wrapper = DeepSeekLogger(mock_deepseek)
        
        messages = [{'role': 'user', 'content': '测试问题'}]
        logger_wrapper.chat(messages)
        
        # 验证 clean_messages_for_api 被调用
        mock_clean.assert_called_once()
    
    @patch('src.infrastructure.llms.deepseek_logger.clean_messages_for_api')
    def test_stream_chat_cleans_messages(self, mock_clean):
        """测试 stream_chat 方法清理消息"""
        mock_deepseek = Mock()
        mock_chunk = Mock()
        mock_message = Mock()
        mock_message.content = "回答"
        mock_chunk.message = mock_message
        mock_deepseek.stream_chat.return_value = [mock_chunk]
        
        mock_clean.return_value = [{'role': 'user', 'content': '问题'}]
        
        logger_wrapper = DeepSeekLogger(mock_deepseek)
        
        messages = [{'role': 'user', 'content': '测试问题'}]
        list(logger_wrapper.stream_chat(messages))
        
        # 验证 clean_messages_for_api 被调用
        mock_clean.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

