"""
DeepSeek LLM 日志包装器
拦截 DeepSeek API 调用，记录请求体和返回值
"""

import json
from typing import Any, Optional, Dict, List
from llama_index.core.llms import CompletionResponse, ChatResponse, LLMMetadata
from llama_index.llms.deepseek import DeepSeek

from src.logger import setup_logger

logger = setup_logger('deepseek_logger')


class DeepSeekLogger:
    """DeepSeek LLM 包装器，记录所有 API 调用
    
    包装 DeepSeek 实例，拦截 complete 和 chat 方法，
    在调用前后记录请求参数和响应结果。
    """
    
    def __init__(self, deepseek_instance: DeepSeek):
        """初始化日志包装器
        
        Args:
            deepseek_instance: DeepSeek 实例
        """
        self._llm = deepseek_instance
        
        # 直接替换方法，而不是依赖 __getattr__
        # 这样确保即使方法已存在也会被拦截
        self.complete = self._complete_with_logging
        self.chat = self._chat_with_logging
        self.stream_complete = self._stream_complete_with_logging
        self.stream_chat = self._stream_chat_with_logging
        
        logger.info("DeepSeek 日志包装器已初始化")
    
    def __getattr__(self, name: str) -> Any:
        """代理所有其他属性和方法到原始 DeepSeek 实例"""
        # 对于未拦截的方法，直接代理到原始实例
        return getattr(self._llm, name)
    
    def _complete_with_logging(self, prompt: str, **kwargs) -> CompletionResponse:
        """包装 complete 方法，记录请求和响应
        
        Args:
            prompt: 提示词
            **kwargs: 其他参数
            
        Returns:
            CompletionResponse: 完成响应
        """
        # 构建请求体
        request_body = {
            "prompt": prompt,
            **kwargs
        }
        
        # 记录请求
        logger.info("=" * 80)
        logger.info("🔵 DeepSeek API 调用 - complete")
        logger.info("-" * 80)
        logger.info(f"📤 请求体:")
        logger.info(f"   模型: {self._llm.model}")
        logger.info(f"   提示词长度: {len(prompt)} 字符")
        logger.info(f"   提示词内容: {prompt[:500]}{'...' if len(prompt) > 500 else ''}")
        if kwargs:
            logger.info(f"   其他参数: {json.dumps(kwargs, ensure_ascii=False, indent=2)}")
        logger.info("-" * 80)
        
        try:
            # 调用原始方法
            response = self._llm.complete(prompt, **kwargs)
            
            # 记录响应
            response_text = response.text if hasattr(response, 'text') else str(response)
            logger.info(f"📥 响应体:")
            logger.info(f"   响应长度: {len(response_text)} 字符")
            logger.info(f"   响应内容: {response_text[:1000]}{'...' if len(response_text) > 1000 else ''}")
            
            # 记录元数据（如果有）
            if hasattr(response, 'raw') and response.raw:
                logger.debug(f"   原始响应: {json.dumps(response.raw, ensure_ascii=False, indent=2)}")
            
            logger.info("=" * 80)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ DeepSeek API 调用失败:")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {str(e)}")
            logger.error("=" * 80)
            raise
    
    def _chat_with_logging(self, messages, **kwargs) -> ChatResponse:
        """包装 chat 方法，记录请求和响应
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            ChatResponse: 聊天响应
        """
        # 构建请求体
        request_body = {
            "messages": messages,
            **kwargs
        }
        
        # 记录请求
        logger.info("=" * 80)
        logger.info("🔵 DeepSeek API 调用 - chat")
        logger.info("-" * 80)
        logger.info(f"📤 请求体:")
        logger.info(f"   模型: {self._llm.model}")
        logger.info(f"   消息数量: {len(messages)}")
        for i, msg in enumerate(messages):
            # 处理 ChatMessage 对象或字典
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
                content = msg.content
            elif isinstance(msg, dict):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
            else:
                role = 'unknown'
                content = str(msg)
            logger.info(f"   消息 {i+1} ({role}): {content[:200]}{'...' if len(content) > 200 else ''}")
        if kwargs:
            logger.info(f"   其他参数: {json.dumps(kwargs, ensure_ascii=False, indent=2)}")
        logger.info("-" * 80)
        
        try:
            # 调用原始方法
            response = self._llm.chat(messages, **kwargs)
            
            # 记录响应
            response_message = response.message if hasattr(response, 'message') else None
            response_text = response_message.content if response_message and hasattr(response_message, 'content') else str(response)
            
            logger.info(f"📥 响应体:")
            logger.info(f"   响应长度: {len(response_text)} 字符")
            logger.info(f"   响应内容: {response_text[:1000]}{'...' if len(response_text) > 1000 else ''}")
            
            # 记录元数据（如果有）
            if hasattr(response, 'raw') and response.raw:
                logger.debug(f"   原始响应: {json.dumps(response.raw, ensure_ascii=False, indent=2)}")
            
            logger.info("=" * 80)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ DeepSeek API 调用失败:")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {str(e)}")
            logger.error("=" * 80)
            raise
    
    def _stream_complete_with_logging(self, prompt: str, **kwargs):
        """包装 stream_complete 方法，记录请求和响应流
        
        Args:
            prompt: 提示词
            **kwargs: 其他参数
            
        Yields:
            CompletionResponse: 流式完成响应
        """
        # 记录请求
        logger.info("=" * 80)
        logger.info("🔵 DeepSeek API 调用 - stream_complete")
        logger.info("-" * 80)
        logger.info(f"📤 请求体:")
        logger.info(f"   模型: {self._llm.model}")
        logger.info(f"   提示词长度: {len(prompt)} 字符")
        logger.info(f"   提示词内容: {prompt[:500]}{'...' if len(prompt) > 500 else ''}")
        if kwargs:
            logger.info(f"   其他参数: {json.dumps(kwargs, ensure_ascii=False, indent=2)}")
        logger.info("-" * 80)
        
        try:
            # 调用原始方法并收集响应
            full_response = ""
            for chunk in self._llm.stream_complete(prompt, **kwargs):
                chunk_text = chunk.text if hasattr(chunk, 'text') else str(chunk)
                full_response += chunk_text
                yield chunk
            
            # 记录完整响应
            logger.info(f"📥 响应体（流式）:")
            logger.info(f"   响应长度: {len(full_response)} 字符")
            logger.info(f"   响应内容: {full_response[:1000]}{'...' if len(full_response) > 1000 else ''}")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ DeepSeek API 调用失败:")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {str(e)}")
            logger.error("=" * 80)
            raise
    
    def _stream_chat_with_logging(self, messages, **kwargs):
        """包装 stream_chat 方法，记录请求和响应流
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            ChatResponse: 流式聊天响应
        """
        # 记录请求
        logger.info("=" * 80)
        logger.info("🔵 DeepSeek API 调用 - stream_chat")
        logger.info("-" * 80)
        logger.info(f"📤 请求体:")
        logger.info(f"   模型: {self._llm.model}")
        logger.info(f"   消息数量: {len(messages)}")
        for i, msg in enumerate(messages):
            # 处理 ChatMessage 对象或字典
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
                content = msg.content
            elif isinstance(msg, dict):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
            else:
                role = 'unknown'
                content = str(msg)
            logger.info(f"   消息 {i+1} ({role}): {content[:200]}{'...' if len(content) > 200 else ''}")
        if kwargs:
            logger.info(f"   其他参数: {json.dumps(kwargs, ensure_ascii=False, indent=2)}")
        logger.info("-" * 80)
        
        try:
            # 调用原始方法并收集响应
            full_response = ""
            for chunk in self._llm.stream_chat(messages, **kwargs):
                chunk_message = chunk.message if hasattr(chunk, 'message') else None
                chunk_text = chunk_message.content if chunk_message and hasattr(chunk_message, 'content') else str(chunk)
                full_response += chunk_text
                yield chunk
            
            # 记录完整响应
            logger.info(f"📥 响应体（流式）:")
            logger.info(f"   响应长度: {len(full_response)} 字符")
            logger.info(f"   响应内容: {full_response[:1000]}{'...' if len(full_response) > 1000 else ''}")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ DeepSeek API 调用失败:")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {str(e)}")
            logger.error("=" * 80)
            raise


def wrap_deepseek(deepseek_instance: DeepSeek) -> DeepSeekLogger:
    """包装 DeepSeek 实例，添加日志记录功能
    
    Args:
        deepseek_instance: DeepSeek 实例
        
    Returns:
        包装后的 DeepSeekLogger 实例
    """
    return DeepSeekLogger(deepseek_instance)

