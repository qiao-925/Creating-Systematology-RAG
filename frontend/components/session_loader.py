"""
会话加载组件 - 从文件加载历史会话

主要功能：
- load_history_session(): 加载历史会话到当前上下文

特性：
- 懒加载优化（根据 session_id 动态构建路径）
- 统一的 rerun 处理
"""

import streamlit as st
from pathlib import Path

from backend.business.chat import load_session_from_file
from backend.infrastructure.config import config
from frontend.utils.sources import convert_sources_to_dict


def load_history_session(chat_manager) -> bool:
    """加载历史会话
    
    优化：移除 rerun，返回加载状态，由调用方统一处理 rerun。
    根据 session_id 动态构建文件路径，不再依赖 file_path。
    
    Args:
        chat_manager: 对话管理器实例
        
    Returns:
        bool: 是否成功加载会话，如果不需要加载返回 False
    """
    if 'load_session_id' not in st.session_state or not st.session_state.load_session_id:
        return False
    
    # 根据 session_id 动态构建文件路径
    session_id = st.session_state.load_session_id
    sessions_dir = config.SESSIONS_PATH / "default"
    session_path = str(sessions_dir / f"{session_id}.json")
    
    # 加载历史会话
    loaded_session = load_session_from_file(session_path)
    
    if loaded_session:
        # 将历史会话设置为当前会话
        chat_manager.current_session = loaded_session
        
        # 将会话历史转换为 messages 格式
        st.session_state.messages = []
        st.session_state.current_sources_map = {}
        if 'current_reasoning_map' in st.session_state:
            st.session_state.current_reasoning_map = {}
        
        for turn in loaded_session.history:
            # 用户消息
            st.session_state.messages.append({
                "role": "user",
                "content": turn.question
            })
            
            # AI 回复（包含推理链，如果存在）
            assistant_msg = {
                "role": "assistant",
                "content": turn.answer,
                "sources": turn.sources
            }
            
            # 如果会话历史中包含推理链，添加到消息中
            if hasattr(turn, 'reasoning_content') and turn.reasoning_content:
                assistant_msg["reasoning_content"] = turn.reasoning_content
            
            st.session_state.messages.append(assistant_msg)
            
            # 如果有引用来源，存储到 current_sources_map
            if turn.sources:
                from frontend.utils.helpers import generate_message_id
                message_id = generate_message_id(
                    len(st.session_state.messages) - 1, 
                    assistant_msg
                )
                # 确保 sources 是字典格式并包含 index 字段
                converted_sources = convert_sources_to_dict(turn.sources)
                st.session_state.current_sources_map[message_id] = converted_sources
                assistant_msg["sources"] = converted_sources
            
            # 处理推理链
            if hasattr(turn, 'reasoning_content') and turn.reasoning_content:
                from frontend.utils.helpers import generate_message_id
                message_id = generate_message_id(
                    len(st.session_state.messages) - 1, 
                    assistant_msg
                )
                if 'current_reasoning_map' not in st.session_state:
                    st.session_state.current_reasoning_map = {}
                st.session_state.current_reasoning_map[message_id] = turn.reasoning_content
        
        # 清除加载标记
        _clear_loading_flags()
        return True
    else:
        # 加载失败，清除标记
        _clear_loading_flags()
        return False


def _clear_loading_flags() -> None:
    """清除所有加载相关的标记"""
    for key in ['load_session_id', 'load_session_path', 'session_loading_pending']:
        if key in st.session_state:
            del st.session_state[key]
