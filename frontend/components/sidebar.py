"""
侧边栏组件
"""

import streamlit as st
from src.infrastructure.config import config
from frontend.components.history import display_session_history
from frontend.components.settings_dialog import show_settings_dialog


def render_sidebar(chat_manager) -> None:
    """渲染侧边栏
    
    Args:
        chat_manager: 对话管理器实例
    """
    with st.sidebar:
        # ========== 应用标题区域 ==========
        st.title("📚 " + config.APP_TITLE)
        st.caption("基于LlamaIndex和DeepSeek的系统科学知识问答系统")
        
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

        # ========== 历史会话（紧随新对话按钮） ==========
        current_session_id = None
        if chat_manager and chat_manager.current_session:
            current_session_id = chat_manager.current_session.session_id
        display_session_history(user_email=None, current_session_id=current_session_id)
        
        # ========== 设置按钮 ==========
        st.divider()
        if st.button("⚙️ 设置", use_container_width=True, key="settings_button"):
            st.session_state.show_settings_dialog = True
        
        # 检查是否需要显示设置弹窗
        if st.session_state.get("show_settings_dialog", False):
            show_settings_dialog()
            # 注意：对话框的关闭由装饰器自动处理，不需要手动关闭

