"""
DeepSeek LLM 日志包装器
拦截 DeepSeek API 调用，记录请求体和返回值
"""

import json
import time
from typing import Any, Optional, Dict, List
from llama_index.core.llms import CompletionResponse, ChatResponse, LLMMetadata
from llama_index.llms.deepseek import DeepSeek

from backend.infrastructure.logger import get_logger
from backend.infrastructure.llms.reasoning import clean_messages_for_api

logger = get_logger('deepseek_logger')


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
                try:
                    # 尝试序列化原始响应（如果是字典或可序列化对象）
                    if isinstance(response.raw, dict):
                        logger.debug(f"   原始响应: {json.dumps(response.raw, ensure_ascii=False, indent=2)}")
                    else:
                        logger.debug(f"   原始响应类型: {type(response.raw)}")
                except (TypeError, ValueError):
                    # 如果无法序列化（如 ChatCompletion 对象），只记录类型
                    logger.debug(f"   原始响应类型: {type(response.raw)}（无法序列化）")
            
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
            # 清理消息，确保不包含 reasoning_content（符合 DeepSeek API 要求）
            cleaned_messages = clean_messages_for_api(messages)
            
            # 调用原始方法（使用清理后的消息）
            response = self._llm.chat(cleaned_messages, **kwargs)
            
            # 记录响应
            response_message = response.message if hasattr(response, 'message') else None
            response_text = response_message.content if response_message and hasattr(response_message, 'content') else str(response)
            
            # 提取推理链内容（如果存在）
            reasoning_content = None
            if response_message and hasattr(response_message, 'reasoning_content'):
                reasoning_content = response_message.reasoning_content
            
            logger.info(f"📥 响应体:")
            logger.info(f"   响应长度: {len(response_text)} 字符")
            logger.info(f"   响应内容: {response_text[:1000]}{'...' if len(response_text) > 1000 else ''}")
            
            # 记录推理链内容（如果存在）
            if reasoning_content:
                logger.info(f"🧠 推理链内容:")
                logger.info(f"   推理链长度: {len(reasoning_content)} 字符")
                logger.info(f"   推理链内容: {reasoning_content[:1000]}{'...' if len(reasoning_content) > 1000 else ''}")
            
            # 记录元数据（如果有）
            if hasattr(response, 'raw') and response.raw:
                try:
                    # 尝试序列化原始响应（如果是字典或可序列化对象）
                    if isinstance(response.raw, dict):
                        logger.info(f"   原始响应 keys: {list(response.raw.keys())}")
                        # 检查 choices 中是否有 reasoning_content
                        if 'choices' in response.raw and response.raw['choices']:
                            choice = response.raw['choices'][0]
                            if isinstance(choice, dict) and 'message' in choice:
                                msg = choice['message']
                                if isinstance(msg, dict):
                                    logger.info(f"   message keys: {list(msg.keys())}")
                                    if 'reasoning_content' in msg:
                                        logger.info(f"   ✅ 找到 reasoning_content（长度: {len(msg['reasoning_content']) if msg['reasoning_content'] else 0}）")
                                    else:
                                        logger.warning(f"   ⚠️ message 中没有 reasoning_content 字段")
                        logger.debug(f"   原始响应: {json.dumps(response.raw, ensure_ascii=False, indent=2)}")
                    else:
                        logger.debug(f"   原始响应类型: {type(response.raw)}")
                except (TypeError, ValueError) as e:
                    # 如果无法序列化（如 Mock 对象），只记录类型
                    logger.debug(f"   原始响应类型: {type(response.raw)}（无法序列化: {e}）")
            
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
            # 清理消息，确保不包含 reasoning_content（符合 DeepSeek API 要求）
            cleaned_messages = clean_messages_for_api(messages)
            
            # 调用原始方法并收集响应（使用清理后的消息）
            full_response = ""
            full_reasoning = ""
            last_chunk_time = time.time()
            chunk_count = 0
            for chunk in self._llm.stream_chat(cleaned_messages, **kwargs):
                chunk_count += 1
                current_time = time.time()
                time_since_last = current_time - last_chunk_time
                last_chunk_time = current_time
                
                # 立即 yield chunk，确保前端尽快收到数据
                yield chunk
                
                # 在 yield 之后处理日志和内容累积（不阻塞前端接收）
                # 记录每个 chunk 的到达时间（仅在前几个和间隔较长时记录）
                if chunk_count <= 5 or time_since_last > 0.1:
                    logger.debug(f"📦 Chunk #{chunk_count} 到达，间隔: {time_since_last*1000:.1f}ms")
                chunk_message = chunk.message if hasattr(chunk, 'message') else None
                if chunk_message:
                    # 处理推理链内容（流式）
                    if hasattr(chunk_message, 'reasoning_content') and chunk_message.reasoning_content:
                        reasoning_str = str(chunk_message.reasoning_content) if chunk_message.reasoning_content else ""
                        if reasoning_str:
                            full_reasoning += reasoning_str
                    # 处理普通内容（流式）
                    if hasattr(chunk_message, 'content') and chunk_message.content:
                        content_str = str(chunk_message.content) if chunk_message.content else ""
                        if content_str:
                            full_response += content_str
                else:
                    # 处理 delta（流式响应）
                    if hasattr(chunk, 'delta'):
                        delta = chunk.delta
                        if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                            reasoning_str = str(delta.reasoning_content) if delta.reasoning_content else ""
                            if reasoning_str:
                                full_reasoning += reasoning_str
                        if hasattr(delta, 'content') and delta.content:
                            content_str = str(delta.content) if delta.content else ""
                            if content_str:
                                full_response += content_str
                    else:
                        # 降级处理
                        chunk_text = str(chunk)
                        full_response += chunk_text
            
            # 记录完整响应
            logger.info(f"📥 响应体（流式）:")
            logger.info(f"   响应长度: {len(full_response)} 字符")
            logger.info(f"   响应内容: {full_response[:1000]}{'...' if len(full_response) > 1000 else ''}")
            
            # 记录推理链内容（如果存在）
            if full_reasoning:
                logger.info(f"🧠 推理链内容（流式）:")
                logger.info(f"   推理链长度: {len(full_reasoning)} 字符")
                logger.info(f"   推理链内容: {full_reasoning[:1000]}{'...' if len(full_reasoning) > 1000 else ''}")
            
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

