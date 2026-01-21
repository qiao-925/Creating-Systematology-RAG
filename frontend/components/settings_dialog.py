"""
设置弹窗组件
在弹窗中显示数据源管理

主要功能：
- show_settings_dialog()：显示设置弹窗（仅数据源管理）
"""

import streamlit as st
from frontend.utils.state import init_session_state
from frontend.settings import render_data_source_tab


@st.dialog("⚙️ 设置", width="large")
def show_settings_dialog() -> None:
    """显示设置弹窗（仅数据源管理）"""
    # 初始化状态（模型延迟加载，首次使用时自动加载）
    init_session_state()
    
    # 只显示数据源管理
    render_data_source_tab()


