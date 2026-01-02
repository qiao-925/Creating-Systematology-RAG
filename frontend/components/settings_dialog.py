"""
设置弹窗组件
在弹窗中显示所有设置选项

主要功能：
- show_settings_dialog()：显示设置弹窗
"""

import streamlit as st
from src.infrastructure.config import config
from frontend.utils.state import init_session_state
from frontend.utils.styles import CLAUDE_STYLE_CSS
from frontend.settings.data_source import render_data_source_tab
from frontend.settings.dev_tools import render_dev_tools_tab
from frontend.settings.system_status import render_system_status_tab


@st.dialog("⚙️ 设置", width="large")
def show_settings_dialog() -> None:
    """显示设置弹窗"""
    # 应用CSS样式
    st.markdown(CLAUDE_STYLE_CSS, unsafe_allow_html=True)
    
    # 初始化状态（模型延迟加载，首次使用时自动加载）
    init_session_state()
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs([
        "📦 数据源管理",
        "💬 对话设置",
        "🐛 开发者工具",
        "⚙️ 系统状态"
    ])
    
    # 渲染各个标签页
    with tab1:
        render_data_source_tab()
    
    with tab2:
        # 对话设置标签页
        st.header("💬 对话设置")
        st.caption("配置对话相关的行为和显示选项")
        
        # 推理链设置
        st.subheader("🧠 推理链")
        enable_reasoning_display = st.checkbox(
            "显示推理链",
            value=config.DEEPSEEK_ENABLE_REASONING_DISPLAY,
            help="在对话界面中显示 AI 的推理过程（reasoning_content）"
        )
        st.session_state.show_reasoning = enable_reasoning_display
        
        enable_reasoning_store = st.checkbox(
            "存储推理链到会话历史",
            value=config.DEEPSEEK_STORE_REASONING,
            help="将推理链保存到会话历史记录中（会增加文件大小）"
        )
        if enable_reasoning_store != config.DEEPSEEK_STORE_REASONING:
            st.session_state.store_reasoning = enable_reasoning_store
        
        st.divider()
        
        # 会话管理（预留）
        st.subheader("💾 会话管理")
        st.info("ℹ️ 会话管理功能将在未来版本中提供更多选项")
    
    with tab3:
        render_dev_tools_tab()
    
    with tab4:
        render_system_status_tab()


