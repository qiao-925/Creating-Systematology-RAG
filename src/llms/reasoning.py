"""
推理链处理工具函数
提供推理链内容的提取、清理和验证功能
"""

from typing import Optional, Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from llama_index.core.llms import ChatResponse

from src.logger import setup_logger

logger = setup_logger('reasoning')


def extract_reasoning_content(response: Any) -> Optional[str]:
    """从响应中提取推理链内容
    
    Args:
        response: LLM 响应对象（ChatResponse 或 CompletionResponse）
        
    Returns:
        推理链内容，如果不存在返回 None
    """
    try:
        # 处理 ChatResponse
        if hasattr(response, 'message'):
            message = response.message
            if hasattr(message, 'reasoning_content') and message.reasoning_content:
                return message.reasoning_content
        
        # 处理 CompletionResponse（如果支持）
        if hasattr(response, 'reasoning_content') and response.reasoning_content:
            return response.reasoning_content
        
        # 处理原始响应（raw）
        if hasattr(response, 'raw') and response.raw:
            raw = response.raw
            # 检查 choices[0].message.reasoning_content
            if isinstance(raw, dict):
                choices = raw.get('choices', [])
                if choices and len(choices) > 0:
                    choice = choices[0]
                    message = choice.get('message', {})
                    if isinstance(message, dict):
                        reasoning = message.get('reasoning_content')
                        if reasoning:
                            return reasoning
        
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


def clean_messages_for_api(messages: List[Any]) -> List[Dict[str, str]]:
    """清理消息列表，确保不包含 reasoning_content
    
    根据 DeepSeek API 文档，如果 messages 中包含 reasoning_content，
    API 会返回 400 错误。此函数确保只传递 role 和 content。
    
    Args:
        messages: 消息列表（ChatMessage 对象或字典）
        
    Returns:
        清理后的消息列表（字典格式，只包含 role 和 content）
    """
    cleaned = []
    
    for msg in messages:
        try:
            # 处理 ChatMessage 对象
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
                content = msg.content
                cleaned.append({
                    'role': role,
                    'content': content
                })
            # 处理字典格式
            elif isinstance(msg, dict):
                cleaned_msg = {
                    'role': msg.get('role', 'user'),
                    'content': msg.get('content', '')
                }
                # 确保不包含 reasoning_content
                if 'reasoning_content' in msg:
                    logger.debug("移除消息中的 reasoning_content 字段")
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

