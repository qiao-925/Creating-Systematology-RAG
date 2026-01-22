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
from frontend.components.observability_summary import render_observability_summary
from frontend.components.observer_renderers import render_llamadebug_full_info, render_ragas_full_info
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
    # 统一处理会话加载（优化：减少 rerun 次数）
    if st.session_state.get('session_loading_pending') or st.session_state.get('load_session_id'):
        from frontend.components.session_loader import load_history_session
        if load_history_session(chat_manager):
            st.rerun()
    
    # 注入全局JavaScript脚本（仅一次，必须在渲染任何消息前）
    if not st.session_state.get('citation_script_injected', False):
        from frontend.utils.sources import inject_citation_script
        st.markdown(inject_citation_script(), unsafe_allow_html=True)
        st.session_state.citation_script_injected = True
    
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
            # 如果是AI回答，先显示观察器信息
            if message["role"] == "assistant":
                _render_observer_info(idx)
            
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


def _render_observer_info(message_index: int) -> None:
    """渲染观察器信息（在答案前显示）
    
    Args:
        message_index: 消息索引（assistant消息的索引）
    """
    # 初始化日志存储
    if 'llama_debug_logs' not in st.session_state:
        st.session_state.llama_debug_logs = []
    if 'ragas_logs' not in st.session_state:
        st.session_state.ragas_logs = []
    
    # 获取观察器日志
    debug_logs = st.session_state.llama_debug_logs
    ragas_logs = st.session_state.ragas_logs
    
    # 计算assistant消息的数量（用于匹配日志）
    assistant_count = sum(1 for msg in st.session_state.messages[:message_index+1] if msg.get("role") == "assistant")
    
    # 找到对应的日志（通过assistant消息数量匹配）
    debug_log = None
    ragas_log = None
    
    # 如果日志数量足够，使用对应的日志
    if len(debug_logs) >= assistant_count:
        debug_log = debug_logs[assistant_count - 1]
    elif len(debug_logs) > 0:
        # 否则使用最新的日志
        debug_log = debug_logs[-1]
    
    if len(ragas_logs) >= assistant_count:
        ragas_log = ragas_logs[assistant_count - 1]
    elif len(ragas_logs) > 0:
        ragas_log = ragas_logs[-1]
    
    # 显示观察器信息（如果有）- 分层展示
    if debug_log or ragas_log:
        # L0 + L1: 智能摘要（始终显示，集成 RAGAS）
        if debug_log:
            render_observability_summary(debug_log, ragas_log=ragas_log, show_l2=False)
        
        # L2: 完整链路（折叠，供开发者调试）
        with st.expander("🔬 完整链路详情（开发者）", expanded=False):
            if debug_log:
                render_llamadebug_full_info(debug_log)
            
            if ragas_log:
                st.divider()
                render_ragas_full_info(ragas_log)

