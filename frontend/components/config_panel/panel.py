"""
主配置面板 - 集成各子组件，提供统一的配置入口

主要功能：
- render_advanced_config(): 设置弹窗高级配置（RAG 参数、显示设置）
"""

import streamlit as st
from typing import Callable, Optional

from backend.infrastructure.config import config
from frontend.components.config_panel.rag_params import (
    render_rag_advanced_params,
)


def render_advanced_config(
    on_config_change: Optional[Callable[[], None]] = None,
) -> None:
    """渲染高级配置面板（用于设置弹窗）
    
    包含：
    - RAG 高级参数（Top-K、阈值、重排序）
    - 显示设置（推理过程）
    
    Args:
        on_config_change: 配置变更回调
    """
    # RAG 高级参数
    render_rag_advanced_params(on_params_change=on_config_change)
    
    st.markdown("---")
    
    # 研究模式
    _render_research_mode(on_config_change)
    
    st.markdown("---")
    
    # 显示设置
    _render_display_settings(on_config_change)


def _render_research_mode(
    on_config_change: Optional[Callable[[], None]] = None,
) -> None:
    """渲染研究模式开关"""
    st.subheader("研究模式")
    
    if 'research_mode' not in st.session_state:
        st.session_state.research_mode = False
    
    new_research_mode = st.toggle(
        "启用深度研究",
        value=st.session_state.research_mode,
        key="research_mode_toggle",
        help="启用后，系统将以研究型 Agent 模式运行：自主取证、形成判断、揭示张力。适合需要深度分析的研究问题。"
    )
    
    if new_research_mode != st.session_state.research_mode:
        st.session_state.research_mode = new_research_mode
        if on_config_change:
            on_config_change()


def _render_display_settings(
    on_config_change: Optional[Callable[[], None]] = None,
) -> None:
    """渲染显示设置"""
    st.subheader("显示设置")
    
    # 初始化状态
    if 'show_reasoning' not in st.session_state:
        st.session_state.show_reasoning = config.DEEPSEEK_ENABLE_REASONING_DISPLAY
    
    # 推理过程显示
    new_show_reasoning = st.toggle(
        "显示推理过程",
        value=st.session_state.show_reasoning,
        key="show_reasoning_toggle",
        help="启用后，使用推理模型时会显示详细的思考过程。"
    )
    
    if new_show_reasoning != st.session_state.show_reasoning:
        st.session_state.show_reasoning = new_show_reasoning
        if on_config_change:
            on_config_change()
