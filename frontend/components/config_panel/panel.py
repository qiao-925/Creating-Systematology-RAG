"""
主配置面板 - 集成各子组件，提供统一的配置入口

主要功能：
- render_sidebar_config(): 侧边栏常用配置（模型、预设、检索策略）
- render_advanced_config(): 设置弹窗高级配置（RAG 参数、显示设置）
"""

import streamlit as st
from typing import Callable, Optional

from backend.infrastructure.config import config
from frontend.components.config_panel.llm_presets import (
    render_model_selector,
    render_llm_preset_selector,
)
from frontend.components.config_panel.rag_params import (
    render_rag_basic_params,
    render_rag_advanced_params,
)


def render_sidebar_config(
    on_config_change: Optional[Callable[[], None]] = None,
) -> None:
    """渲染侧边栏常用配置
    
    包含：
    - 模型选择
    - LLM 预设（精确/平衡/创意）
    - 检索策略
    - Agentic RAG 开关
    
    Args:
        on_config_change: 配置变更回调（用于触发服务重建）
    """
    # 模型选择
    render_model_selector(on_model_change=lambda _: _trigger_rebuild(on_config_change))
    
    st.divider()
    
    # LLM 预设
    render_llm_preset_selector(on_preset_change=lambda _: _trigger_rebuild(on_config_change))
    
    st.divider()
    
    # RAG 基础参数
    render_rag_basic_params(
        on_strategy_change=lambda _: _trigger_rebuild(on_config_change),
        on_agentic_toggle=lambda _: _trigger_rebuild(on_config_change),
    )


def _trigger_rebuild(callback: Optional[Callable[[], None]]) -> None:
    """触发服务重建"""
    if callback:
        callback()


def render_advanced_config(
    on_config_change: Optional[Callable[[], None]] = None,
) -> None:
    """渲染高级配置面板（用于设置弹窗）
    
    包含：
    - RAG 高级参数（Top-K、阈值、重排序）
    - 显示设置（推理过程、调试模式）
    
    Args:
        on_config_change: 配置变更回调
    """
    # RAG 高级参数
    render_rag_advanced_params(on_params_change=on_config_change)
    
    st.markdown("---")
    
    # 显示设置
    _render_display_settings(on_config_change)


def _render_display_settings(
    on_config_change: Optional[Callable[[], None]] = None,
) -> None:
    """渲染显示设置"""
    st.subheader("显示设置")
    
    # 初始化状态
    if 'show_reasoning' not in st.session_state:
        st.session_state.show_reasoning = config.DEEPSEEK_ENABLE_REASONING_DISPLAY
    if 'debug_mode_enabled' not in st.session_state:
        st.session_state.debug_mode_enabled = False
    
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
    
    # 调试模式
    new_debug_mode = st.toggle(
        "调试模式",
        value=st.session_state.debug_mode_enabled,
        key="debug_mode_toggle",
        help="启用后，会显示详细的检索和处理日志。"
    )
    
    if new_debug_mode != st.session_state.debug_mode_enabled:
        st.session_state.debug_mode_enabled = new_debug_mode
        if on_config_change:
            on_config_change()
