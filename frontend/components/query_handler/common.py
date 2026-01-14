"""
查询处理公共逻辑
提取流式和非流式查询处理的公共代码
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from frontend.components.sources_panel import display_sources_below_message


def display_reasoning(reasoning_content: Optional[str]) -> None:
    """显示推理链
    
    Args:
        reasoning_content: 推理链内容
    """
    if reasoning_content:
        with st.expander("🧠 推理过程", expanded=False):
            st.markdown(f"```\n{reasoning_content}\n```")


def display_sources(sources: List[Dict[str, Any]], message_id: str) -> None:
    """显示引用来源
    
    Args:
        sources: 引用来源列表
        message_id: 消息唯一ID
    """
    if sources:
        st.markdown("#### 📚 引用来源")
        display_sources_below_message(sources, message_id=message_id)


def save_to_chat_manager(chat_manager, prompt: str, answer: str, 
                        sources: List[Dict[str, Any]], 
                        reasoning_content: Optional[str] = None) -> None:
    """保存到ChatManager会话
    
    Args:
        chat_manager: 对话管理器实例
        prompt: 用户查询
        answer: AI回答
        sources: 引用来源列表
        reasoning_content: 推理链内容（可选）
    """
    if chat_manager and answer:
        if not chat_manager.current_session:
            chat_manager.start_session()
        if reasoning_content:
            chat_manager.current_session.add_turn(prompt, answer, sources, reasoning_content)
        else:
            chat_manager.current_session.add_turn(prompt, answer, sources)

