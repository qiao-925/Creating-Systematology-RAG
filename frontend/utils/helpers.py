"""
辅助函数模块

主要功能：
- generate_message_id()：生成消息唯一ID
- generate_default_message_id()：生成默认消息ID
- get_chat_title()：从消息列表提取标题
"""

from typing import Optional, List, Dict, Any


def generate_message_id(message_idx: int, content: str) -> str:
    """生成消息唯一ID
    
    Args:
        message_idx: 消息索引
        content: 消息内容（用于生成hash）
        
    Returns:
        消息唯一ID字符串，格式：msg_{idx}_{hash}
    """
    return f"msg_{message_idx}_{hash(str(content))}"


def generate_default_message_id() -> str:
    """生成默认消息ID（当没有提供消息索引和内容时使用）
    
    Returns:
        默认消息唯一ID字符串
    """
    import time
    return f"msg_0_{hash(str(time.time()))}"


def get_chat_title(messages: List[Dict[str, Any]]) -> Optional[str]:
    """从第一个用户消息中提取标题
    
    Args:
        messages: 消息列表
        
    Returns:
        标题字符串，如果没有用户消息则返回None
    """
    if not messages:
        return None
    
    # 找到第一个用户消息
    for message in messages:
        if message.get("role") == "user":
            content = message.get("content", "")
            if content:
                # 截取前50个字符作为标题
                title = content[:50].strip()
                # 如果超过50个字符，添加省略号
                if len(content) > 50:
                    title += "..."
                return title
    
    return None

