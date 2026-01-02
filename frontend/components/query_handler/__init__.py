"""
查询处理组件模块
"""

import streamlit as st
from frontend.components.query_handler.streaming import handle_streaming_query
from frontend.components.query_handler.non_streaming import handle_non_streaming_query


def handle_user_queries(rag_service, chat_manager) -> None:
    """处理用户查询（路由分发器）
    
    Args:
        rag_service: RAG服务实例
        chat_manager: 对话管理器实例
    """
    # 处理待处理的查询（快速开始）
    if 'pending_query' in st.session_state and st.session_state.pending_query:
        prompt = st.session_state.pending_query
        del st.session_state.pending_query  # 清除待处理标记
        handle_non_streaming_query(rag_service, chat_manager, prompt)
        return
    
    # 处理默认问题点击
    if 'selected_question' in st.session_state and st.session_state.selected_question:
        prompt = st.session_state.selected_question
        st.session_state.selected_question = None  # 清除状态
        handle_non_streaming_query(rag_service, chat_manager, prompt)
        return
    
    # 处理用户输入（流式）
    if st.session_state.messages:
        from frontend.components.chat_input import deepseek_style_chat_input
        prompt = deepseek_style_chat_input("给系统发送消息", key="main_chat_input", fixed=True)
        
        if prompt:
            st.session_state.is_thinking = True
            # 显示用户消息
            left_spacer, center_col, right_spacer = st.columns([2, 6, 2])
            with center_col:
                with st.chat_message("user"):
                    st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # 流式处理
            handle_streaming_query(chat_manager, prompt)


__all__ = ['handle_user_queries', 'handle_streaming_query', 'handle_non_streaming_query']

