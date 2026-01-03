"""
聊天输入组件 - 使用 Streamlit 原生组件
使用 st.chat_input() 实现，简化代码并提高可维护性

主要功能：
- simple_chat_input()：使用 st.chat_input() 的简化实现
"""

import streamlit as st
from typing import Optional


def simple_chat_input(placeholder: str = "给系统发送消息", key: str = "chat_input", disabled: bool = False) -> Optional[str]:
    """使用 st.chat_input() 的简化实现
    
    Args:
        placeholder: 占位符文本
        key: Streamlit组件key
        disabled: 是否禁用输入框（思考中时隐藏）
        
    Returns:
        用户输入的文本，如果未输入或未点击发送则返回None
        
    注意：
        - st.chat_input() 原生支持 Enter 发送、Shift+Enter 换行
        - st.chat_input() 原生支持多行输入和自动高度调整
        - st.chat_input() 默认固定在底部，无需额外 CSS
    """
    if disabled:
        return None
    
    user_input = st.chat_input(placeholder, key=key)
    return user_input


# 保持向后兼容的别名
def deepseek_style_chat_input(placeholder: str = "给系统发送消息", key: str = "chat_input", disabled: bool = False, fixed: bool = False) -> Optional[str]:
    """向后兼容的别名函数
    
    注意：fixed 参数已废弃，st.chat_input() 默认固定在底部
    """
    return simple_chat_input(placeholder, key, disabled)
