"""
辅助函数模块
"""

from typing import Optional, List, Dict, Any, Tuple
import streamlit as st
from streamlit.delta_generator import DeltaGenerator


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


def create_centered_columns() -> Tuple[DeltaGenerator, DeltaGenerator, DeltaGenerator]:
    """创建居中的列布局（左右留白，中间内容区域）
    
    Returns:
        三元组 (left_spacer, center_col, right_spacer)
    """
    left_spacer, center_col, right_spacer = st.columns([2, 6, 2])
    return left_spacer, center_col, right_spacer


def handle_error(error: Exception, context: str = "", show_to_user: bool = True, log_error: bool = True) -> None:
    """统一错误处理函数
    
    Args:
        error: 异常对象
        context: 错误上下文描述
        show_to_user: 是否在UI中显示错误（使用 st.error）
        log_error: 是否记录日志（使用 logger.error）
    """
    error_message = str(error)
    full_message = f"{context}: {error_message}" if context else error_message
    
    if show_to_user:
        st.error(f"❌ {full_message}")
    
    if log_error:
        from backend.infrastructure.logger import get_logger
        logger = get_logger('frontend.error_handler')
        logger.error(full_message, exc_info=True)


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

