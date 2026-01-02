"""
会话加载组件
"""

import streamlit as st
from pathlib import Path
from src.business.chat import load_session_from_file
from src.infrastructure.config import config
from frontend.utils.sources import convert_sources_to_dict


def load_history_session(chat_manager) -> bool:
    """加载历史会话
    
    优化：移除rerun，返回加载状态，由调用方统一处理rerun。
    根据session_id动态构建文件路径，不再依赖file_path。
    
    Args:
        chat_manager: 对话管理器实例
        
    Returns:
        bool: 是否成功加载会话，如果不需要加载返回False
    """
    if 'load_session_id' not in st.session_state or not st.session_state.load_session_id:
        return False
    
    # 根据session_id动态构建文件路径（懒加载优化）
    session_id = st.session_state.load_session_id
    sessions_dir = config.SESSIONS_PATH / "default"
    session_path = str(sessions_dir / f"{session_id}.json")
    
    # 加载历史会话
    loaded_session = load_session_from_file(session_path)
    
    if loaded_session:
        # 将历史会话设置为当前会话
        chat_manager.current_session = loaded_session
        
        # 将会话历史转换为messages格式
        st.session_state.messages = []
        # 清空引用来源映射，避免显示上一个对话的引用来源
        st.session_state.current_sources_map = {}
        if 'current_reasoning_map' in st.session_state:
            st.session_state.current_reasoning_map = {}
        
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
                from frontend.utils.helpers import generate_message_id
                message_id = generate_message_id(len(st.session_state.messages) - 1, assistant_msg)
                # 确保sources是字典格式并包含index字段
                converted_sources = convert_sources_to_dict(turn.sources)
                st.session_state.current_sources_map[message_id] = converted_sources
                # 同时更新消息中的sources
                assistant_msg["sources"] = converted_sources
            
            # 处理推理链
            if hasattr(turn, 'reasoning_content') and turn.reasoning_content:
                from frontend.utils.helpers import generate_message_id
                message_id = generate_message_id(len(st.session_state.messages) - 1, assistant_msg)
                if 'current_reasoning_map' not in st.session_state:
                    st.session_state.current_reasoning_map = {}
                st.session_state.current_reasoning_map[message_id] = turn.reasoning_content
        
        # 清除加载标记
        del st.session_state.load_session_id
        if 'load_session_path' in st.session_state:
            del st.session_state.load_session_path
        if 'session_loading_pending' in st.session_state:
            del st.session_state.session_loading_pending
        
        return True
    else:
        # 加载失败，清除标记
        if 'load_session_id' in st.session_state:
            del st.session_state.load_session_id
        if 'load_session_path' in st.session_state:
            del st.session_state.load_session_path
        if 'session_loading_pending' in st.session_state:
            del st.session_state.session_loading_pending
        return False

