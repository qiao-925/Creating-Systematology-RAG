"""
参数配置弹窗组件
在输入框下方的 ⚙️ 按钮点击后弹出

主要功能：
- show_params_dialog(): 显示参数配置弹窗（LLM 预设、检索参数、显示设置）
"""

import streamlit as st
from frontend.utils.state import rebuild_services
from frontend.components.config_panel.llm_presets import render_llm_preset_selector
from frontend.components.config_panel.rag_params import (
    render_rag_basic_params,
    render_rag_advanced_params,
)
from frontend.components.config_panel.panel import _render_display_settings


@st.dialog("⚙️ 参数配置", width="large")
def show_params_dialog() -> None:
    """显示参数配置弹窗"""
    # Tab 切换
    tab_basic, tab_advanced = st.tabs(["🎨 基础", "🔧 高级"])
    
    with tab_basic:
        # LLM 预设（回答风格）
        render_llm_preset_selector(on_preset_change=lambda _: rebuild_services())
        
        st.markdown("---")
        
        # 检索策略
        render_rag_basic_params(
            on_strategy_change=lambda _: rebuild_services(),
            on_agentic_toggle=lambda _: rebuild_services(),
        )
    
    with tab_advanced:
        # RAG 高级参数
        render_rag_advanced_params(on_params_change=rebuild_services)
        
        st.markdown("---")
        
        # 显示设置
        _render_display_settings(on_config_change=rebuild_services)
