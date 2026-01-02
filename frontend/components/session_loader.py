"""
会话加载组件
"""

import streamlit as st
from src.business.chat import load_session_from_file
from frontend.utils.sources import convert_sources_to_dict


def load_history_session(chat_manager) -> None:
    """加载历史会话
    
    Args:
        chat_manager: 对话管理器实例
    """
    if 'load_session_id' not in st.session_state or not st.session_state.load_session_id:
        return
    
    # 加载历史会话
    session_path = st.session_state.load_session_path
    loaded_session = load_session_from_file(session_path)
    
    if loaded_session:
        # 将历史会话设置为当前会话
        chat_manager.current_session = loaded_session
        
        # 将会话历史转换为messages格式
        st.session_state.messages = []
        # 清空引用来源映射，避免显示上一个对话的引用来源
        st.session_state.current_sources_map = {}
        
        for idx, turn in enumerate(loaded_session.history):
            # 用户消息
            st.session_state.messages.append({
                "role": "user",
                "content": turn.question
            })
            # AI回复（包含推理链，如果存在）
            assistant_msg = {
                "role": "assistant",
                "content": turn.answer,
                "sources": turn.sources
            }
            # 如果会话历史中包含推理链，添加到消息中
            if hasattr(turn, 'reasoning_content') and turn.reasoning_content:
                assistant_msg["reasoning_content"] = turn.reasoning_content
            st.session_state.messages.append(assistant_msg)
            
            # 如果有引用来源，存储到current_sources_map
            if turn.sources:
                message_id = f"msg_{len(st.session_state.messages)-1}_{hash(str(assistant_msg))}"
                # 确保sources是字典格式并包含index字段
                converted_sources = convert_sources_to_dict(turn.sources)
                st.session_state.current_sources_map[message_id] = converted_sources
                # 同时更新消息中的sources
                assistant_msg["sources"] = converted_sources
        
        st.success(f"✅ 已加载会话: {loaded_session.title}")
    else:
        st.error("❌ 加载会话失败")
    
    # 清除加载标记
    del st.session_state.load_session_id
    del st.session_state.load_session_path
    st.rerun()

