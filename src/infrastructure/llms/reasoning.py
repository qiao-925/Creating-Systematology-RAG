"""
推理链处理工具函数：提供推理链内容的提取、清理和验证功能

主要功能：
- extract_reasoning_content()：从响应中提取推理链内容
- extract_reasoning_from_stream_chunk()：从流式响应块中提取推理链
- clean_messages_for_api()：清理消息列表，移除推理链内容
- has_reasoning_content()：检查响应是否包含推理链内容

执行流程：
1. 检查响应对象类型
2. 提取推理链内容
3. 清理和验证
4. 返回处理后的内容

特性：
- 支持多种响应类型
- 流式响应支持
- 消息清理功能
- 完整的错误处理
"""

from typing import Optional, Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from llama_index.core.llms import ChatResponse

from src.infrastructure.logger import get_logger

logger = get_logger('reasoning')


def extract_reasoning_content(response: Any) -> Optional[str]:
    """从响应中提取推理链内容
    
    Args:
        response: LLM 响应对象（ChatResponse 或 CompletionResponse）
        
    Returns:
        推理链内容，如果不存在返回 None
    """
    try:
        # 调试：记录提取过程
        logger.debug(f"🔍 开始提取推理链，响应类型: {type(response)}")
        
        # 处理 LlamaIndex Response 对象（可能包含 response.response 属性）
        if hasattr(response, 'response'):
            inner_response = response.response
            logger.debug(f"🔍 找到 response.response 属性，类型: {type(inner_response)}")
            if hasattr(inner_response, 'message'):
                message = inner_response.message
                logger.debug(f"🔍 response.response.message 类型: {type(message)}")
                if hasattr(message, 'reasoning_content'):
                    logger.debug(f"🔍 response.response.message.reasoning_content 存在: {message.reasoning_content is not None}")
                    if message.reasoning_content:
                        logger.info(f"✅ 从 response.response.message.reasoning_content 提取到推理链（长度: {len(message.reasoning_content)}）")
                        return message.reasoning_content
        
        # 处理 ChatResponse
        if hasattr(response, 'message'):
            message = response.message
            logger.debug(f"🔍 找到 message 属性，类型: {type(message)}")
            if hasattr(message, 'reasoning_content'):
                logger.debug(f"🔍 message.reasoning_content 存在: {message.reasoning_content is not None}")
                if message.reasoning_content:
                    logger.info(f"✅ 从 message.reasoning_content 提取到推理链（长度: {len(message.reasoning_content)}）")
                    return message.reasoning_content
            else:
                logger.debug(f"🔍 message 没有 reasoning_content 属性，message 属性: {dir(message) if hasattr(message, '__dict__') else 'N/A'}")
        
        # 处理 CompletionResponse（如果支持）
        if hasattr(response, 'reasoning_content') and response.reasoning_content:
            return response.reasoning_content
        
        # 处理 LlamaIndex Response 对象的 response 属性（可能是底层的 ChatResponse）
        if hasattr(response, 'response'):
            inner_response = response.response
            logger.debug(f"🔍 检查 response.response.raw")
            if hasattr(inner_response, 'raw') and inner_response.raw:
                raw = inner_response.raw
                logger.debug(f"🔍 response.response.raw 类型: {type(raw)}")
                if isinstance(raw, dict):
                    choices = raw.get('choices', [])
                    logger.debug(f"🔍 response.response.raw 中有 {len(choices)} 个 choices")
                    if choices and len(choices) > 0:
                        choice = choices[0]
                        message = choice.get('message', {})
                        logger.debug(f"🔍 response.response.raw.choice.message 类型: {type(message)}")
                        if isinstance(message, dict):
                            reasoning = message.get('reasoning_content')
                            logger.debug(f"🔍 response.response.raw.choice.message.reasoning_content: {reasoning is not None if reasoning else False}")
                            if reasoning:
                                logger.info(f"✅ 从 response.response.raw.choices[0].message.reasoning_content 提取到推理链（长度: {len(reasoning)}）")
                                return reasoning
        
        # 处理原始响应（raw）
        if hasattr(response, 'raw') and response.raw:
            raw = response.raw
            logger.debug(f"🔍 找到 raw 属性，类型: {type(raw)}")
            # 检查 choices[0].message.reasoning_content
            if isinstance(raw, dict):
                choices = raw.get('choices', [])
                logger.debug(f"🔍 raw 中有 {len(choices)} 个 choices")
                if choices and len(choices) > 0:
                    choice = choices[0]
                    message = choice.get('message', {})
                    logger.debug(f"🔍 choice.message 类型: {type(message)}")
                    if isinstance(message, dict):
                        reasoning = message.get('reasoning_content')
                        logger.debug(f"🔍 message.reasoning_content: {reasoning is not None if reasoning else False}")
                        if reasoning:
                            logger.info(f"✅ 从 raw.choices[0].message.reasoning_content 提取到推理链（长度: {len(reasoning)}）")
                            return reasoning
                    else:
                        logger.debug(f"🔍 message 不是字典类型，无法提取 reasoning_content")
        
        return None
        
    except Exception as e:
        logger.warning(f"提取推理链内容失败: {e}")
        return None


def extract_reasoning_from_stream_chunk(chunk: Any) -> Optional[str]:
    """从流式响应块中提取推理链内容
    
    Args:
        chunk: 流式响应块
        
    Returns:
        推理链内容片段，如果不存在返回 None
    """
    try:
        # 处理 message.delta.reasoning_content
        if hasattr(chunk, 'message'):
            message = chunk.message
            if hasattr(message, 'reasoning_content') and message.reasoning_content:
                return message.reasoning_content
        
        # 处理 delta.reasoning_content
        if hasattr(chunk, 'delta'):
            delta = chunk.delta
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                return delta.reasoning_content
        
        # 处理原始响应（raw）
        if hasattr(chunk, 'raw') and chunk.raw:
            raw = chunk.raw
            if isinstance(raw, dict):
                choices = raw.get('choices', [])
                if choices and len(choices) > 0:
                    choice = choices[0]
                    delta = choice.get('delta', {})
                    if isinstance(delta, dict):
                        reasoning = delta.get('reasoning_content')
                        if reasoning:
                            return reasoning
        
        return None
        
    except Exception as e:
        logger.debug(f"从流式块提取推理链失败: {e}")
        return None


def clean_messages_for_api(messages: List[Any]) -> List[Any]:
    """清理消息列表，确保不包含 reasoning_content
    
    根据 DeepSeek API 文档，如果 messages 中包含 reasoning_content，
    API 会返回 400 错误。此函数确保只传递 role 和 content。
    
    注意：此函数保持 ChatMessage 对象格式，不转换为字典，
    因为 LlamaIndex 的 stream_chat 需要 ChatMessage 对象。
    
    Args:
        messages: 消息列表（ChatMessage 对象或字典）
        
    Returns:
        清理后的消息列表（ChatMessage 对象格式，不包含 reasoning_content）
    """
    from llama_index.core.llms import ChatMessage, MessageRole
    
    cleaned = []
    
    for msg in messages:
        try:
            # 处理 ChatMessage 对象
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                # 如果已经是 ChatMessage 对象，直接使用 role（可能是 MessageRole 枚举）
                role = msg.role
                
                # 如果 role 已经是 MessageRole 类型，直接使用
                if isinstance(role, MessageRole):
                    message_role = role
                else:
                    # 否则尝试转换
                    role_str = str(role).lower()
                    if 'user' in role_str:
                        message_role = MessageRole.USER
                    elif 'assistant' in role_str:
                        message_role = MessageRole.ASSISTANT
                    elif 'system' in role_str:
                        message_role = MessageRole.SYSTEM
                    else:
                        message_role = MessageRole.USER  # 默认
                
                # 获取 content（确保是字符串）
                content = msg.content
                if not isinstance(content, str):
                    content = str(content) if content else ""
                
                # 创建新的 ChatMessage（不包含 reasoning_content）
                cleaned_msg = ChatMessage(
                    role=message_role,
                    content=content
                )
                cleaned.append(cleaned_msg)
            # 处理字典格式
            elif isinstance(msg, dict):
                role_str = msg.get('role', 'user')
                content = msg.get('content', '')
                
                # 转换为 MessageRole
                if role_str == 'user':
                    message_role = MessageRole.USER
                elif role_str == 'assistant':
                    message_role = MessageRole.ASSISTANT
                elif role_str == 'system':
                    message_role = MessageRole.SYSTEM
                else:
                    message_role = MessageRole.USER  # 默认
                
                # 创建 ChatMessage 对象
                cleaned_msg = ChatMessage(
                    role=message_role,
                    content=str(content) if content else ""
                )
                cleaned.append(cleaned_msg)
            else:
                logger.warning(f"无法处理消息类型: {type(msg)}")
                continue
                
        except Exception as e:
            logger.warning(f"清理消息失败: {e}")
            continue
    
    return cleaned


def has_reasoning_content(response: Any) -> bool:
    """检查响应是否包含推理链内容
    
    Args:
        response: LLM 响应对象
        
    Returns:
        如果包含推理链内容返回 True，否则返回 False
    """
    reasoning = extract_reasoning_content(response)
    return reasoning is not None and len(reasoning) > 0

