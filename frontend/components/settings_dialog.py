"""
设置弹窗组件
在弹窗中显示数据源管理和高级配置

主要功能：
- show_settings_dialog()：显示设置弹窗（数据源 + 高级配置）
"""

import streamlit as st
from frontend.utils.state import init_session_state, rebuild_services
from frontend.settings import render_data_source_tab
from frontend.components.config_panel import render_advanced_config


@st.dialog("设置", width="large", icon="⚙️")
def show_settings_dialog() -> None:
    """显示设置弹窗（数据源管理 + 高级配置）"""
    # 初始化状态
    init_session_state()
    
    # Tab 切换
    tab_data_source, tab_advanced = st.tabs(["📂 数据源", "🔧 高级配置"])
    
    with tab_data_source:
        render_data_source_tab()
    
    with tab_advanced:
        render_advanced_config(on_config_change=rebuild_services)
