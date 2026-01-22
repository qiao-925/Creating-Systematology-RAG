"""
侧边栏组件 - 显示应用标题、配置面板、历史会话列表

主要功能：
- render_sidebar(): 渲染完整侧边栏
- _render_sidebar_footer(): 渲染底部工具栏
"""

import streamlit as st
from backend.infrastructure.config import config
from frontend.components.settings_dialog import show_settings_dialog
from frontend.components.history import display_session_history
from frontend.components.config_panel import render_sidebar_config
from frontend.utils.state import rebuild_services


def _render_sidebar_footer() -> None:
    """渲染侧边栏底部固定工具栏
    
    在侧边栏底部固定显示设置等工具按钮
    """
    # 使用 columns 创建按钮布局
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # 设置按钮（最左侧）
        if st.button("⚙️", key="settings_button", help="设置", use_container_width=True):
            st.session_state.show_settings_dialog = True
    
    with col2:
        # 预留位置（帮助按钮，暂时禁用）
        st.button("💡", key="help_button", help="帮助", use_container_width=True, disabled=True)
    
    with col3:
        # 预留位置（反馈按钮，暂时禁用）
        st.button("📱", key="feedback_button", help="反馈", use_container_width=True, disabled=True)


def render_sidebar(chat_manager) -> None:
    """渲染侧边栏
    
    Args:
        chat_manager: 对话管理器实例
    """
    with st.sidebar:
        # ========== 应用标题区域 ==========
        st.title("📚 " + config.APP_TITLE)
        
        # ========== 新对话（顶部） ==========
        def _start_new_chat():
            """开启新对话的回调函数"""
            if chat_manager:
                chat_manager.start_session()
            st.session_state.messages = []
            # 清空引用来源映射
            if 'current_sources_map' in st.session_state:
                st.session_state.current_sources_map = {}
            if 'current_reasoning_map' in st.session_state:
                st.session_state.current_reasoning_map = {}
            # 清空观察器日志
            if 'llama_debug_logs' in st.session_state:
                st.session_state.llama_debug_logs = []
            if 'ragas_logs' in st.session_state:
                st.session_state.ragas_logs = []
        
        st.button(
            "💬 开启新对话", 
            type="primary", 
            use_container_width=True, 
            key="new_chat_top",
            on_click=_start_new_chat
        )
        
        st.divider()
        
        # ========== 配置面板（模型、预设、检索策略） ==========
        render_sidebar_config(on_config_change=rebuild_services)
        
        st.divider()
        
        # ========== 历史会话列表 ==========
        current_session_id = None
        if chat_manager and chat_manager.current_session:
            current_session_id = chat_manager.current_session.session_id
        
            display_session_history(current_session_id=current_session_id)
        
        st.divider()
        
        # ========== 底部固定工具栏 ==========
        _render_sidebar_footer()
        
        # 检查是否需要显示设置弹窗
        if st.session_state.get("show_settings_dialog", False):
            show_settings_dialog()
            # 清除状态标志，避免下次 rerun 时再次显示弹窗
            st.session_state.show_settings_dialog = False
