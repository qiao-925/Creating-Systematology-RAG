"""
对话显示组件
"""

import streamlit as st
from typing import Optional
from frontend.utils.helpers import get_chat_title
from frontend.utils.sources import convert_sources_to_dict
from frontend.utils.state import initialize_sources_map
from frontend.utils.sources import format_answer_with_citation_links
from frontend.components.sources_panel import display_sources_below_message
from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger('app')


def render_chat_interface(rag_service, chat_manager) -> None:
    """渲染对话界面
    
    优化：统一处理会话加载和rerun，减少重复渲染。
    
    Args:
        rag_service: RAG服务实例
        chat_manager: 对话管理器实例
    """
    # 处理历史会话加载（统一处理，避免多次rerun）
    from frontend.components.session_loader import load_history_session
    
    # 检查是否有待加载的会话
    if st.session_state.get('session_loading_pending', False) or 'load_session_id' in st.session_state:
        # 加载会话（同步执行，不立即rerun）
        session_loaded = load_history_session(chat_manager)
        
        if session_loaded:
            # 显示成功消息
            st.success("✅ 会话已加载")
            # 统一rerun一次（合并多次rerun）
            st.rerun()
        else:
            # 加载失败
            st.error("❌ 加载会话失败")
            # 清除标记后rerun
            st.rerun()
        return
    
    # 显示标题
    chat_title = get_chat_title(st.session_state.messages)
    if chat_title:
        st.subheader(chat_title)
        st.markdown("---")
    
    # 初始化来源映射
    initialize_sources_map()
    
    # 无对话历史：显示快速开始
    if not st.session_state.messages:
        from frontend.components.quick_start import render_quick_start
        render_quick_start()
        return
    
    # 有对话历史：显示对话
    render_chat_history()


def render_chat_history() -> None:
    """渲染对话历史"""
    # 显示对话历史
    from frontend.utils.helpers import generate_message_id
    for idx, message in enumerate(st.session_state.messages):
        message_id = generate_message_id(idx, message)
        with st.chat_message(message["role"]):
            # 如果是AI回答且包含引用，使用带链接的格式
            if message["role"] == "assistant" and "sources" in message and message["sources"]:
                formatted_content = format_answer_with_citation_links(
                    message["content"],
                    message["sources"],
                    message_id=message_id
                )
                st.markdown(formatted_content, unsafe_allow_html=True)
            else:
                st.markdown(message["content"])
            
            # 显示推理链（始终显示，如果存在）
            if message["role"] == "assistant":
                reasoning_content = message.get("reasoning_content")
                # 调试：检查推理链是否存在
                if reasoning_content:
                    with st.expander("🧠 推理过程", expanded=False):
                        st.markdown(f"```\n{reasoning_content}\n```")
                else:
                    # 调试：显示为什么没有推理链
                    if config.DEEPSEEK_ENABLE_REASONING_DISPLAY:
                        # 只在启用显示时才显示调试信息
                        logger.debug(f"消息 {message_id} 没有推理链内容")
        
        # 在消息下方显示引用来源（如果有）
        if message["role"] == "assistant":
            sources = st.session_state.current_sources_map.get(message_id, [])
            if sources:
                # 显示引用来源标题
                st.markdown("#### 📚 引用来源")
                # 显示引用来源详情
                display_sources_below_message(sources, message_id=message_id)
        
        # 更新session_state中的映射（确保同步）
        st.session_state.current_sources_map = st.session_state.current_sources_map
        st.session_state.current_reasoning_map = st.session_state.current_reasoning_map

