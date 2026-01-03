"""
侧边栏组件
"""

import streamlit as st
from src.infrastructure.config import config
from frontend.components.history import display_session_history
from frontend.components.settings_dialog import show_settings_dialog


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
        if st.button("💬 开启新对话", type="primary", use_container_width=True, key="new_chat_top"):
            if chat_manager:
                # 创建新会话（只重置对话状态，不重新初始化服务）
                chat_manager.start_session()
                st.session_state.messages = []
                # 清空引用来源映射，避免右侧显示上一个对话的引用来源
                if 'current_sources_map' in st.session_state:
                    st.session_state.current_sources_map = {}
                if 'current_reasoning_map' in st.session_state:
                    st.session_state.current_reasoning_map = {}
                # 仅刷新UI，不触发服务重新验证
                st.rerun()

        # ========== 历史会话（可滚动区域） ==========
        # 使用容器包裹，确保历史会话可以滚动
        with st.container():
            current_session_id = None
            if chat_manager and chat_manager.current_session:
                current_session_id = chat_manager.current_session.session_id
            display_session_history(user_email=None, current_session_id=current_session_id)
        
        # ========== 底部固定工具栏 ==========
        _render_sidebar_footer()
        
        # 检查是否需要显示设置弹窗
        if st.session_state.get("show_settings_dialog", False):
            show_settings_dialog()
            # 清除状态标志，避免下次 rerun 时再次显示弹窗
            st.session_state.show_settings_dialog = False
