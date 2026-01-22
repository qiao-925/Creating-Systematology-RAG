"""
LLM 预设面板组件 - LLM 预设选择的 UI 控制

主要功能：
- render_llm_preset_selector(): 预设选择器（精确/平衡/创意）
- render_model_selector(): 模型选择器
"""

import streamlit as st
from typing import Callable, Optional

from backend.infrastructure.config import config
from backend.infrastructure.llms import get_available_models
from frontend.components.config_panel.models import LLM_PRESETS


def render_model_selector(
    on_model_change: Optional[Callable[[str], None]] = None,
) -> None:
    """渲染模型选择器
    
    Args:
        on_model_change: 模型变更回调
    """
    try:
        models = get_available_models()
        if not models:
            st.info("⚠️ 未配置可用模型")
            return
        
        # 构建选项字典：{显示名称: 模型ID}
        model_options = {model.name: model.id for model in models}
        model_names = list(model_options.keys())
        
        # 获取当前选择的模型
        current_model_id = st.session_state.get(
            'selected_model', config.get_default_llm_id()
        )
        
        # 找到当前模型在列表中的索引
        current_index = 0
        for i, (name, model_id) in enumerate(model_options.items()):
            if model_id == current_model_id:
                current_index = i
                break
        
        # 显示模型选择器
        selected_name = st.selectbox(
            "🤖 选择模型",
            options=model_names,
            index=current_index,
            key="model_selector_config",
            help="切换不同的 LLM 模型。切换后，当前会话的后续消息将使用新模型。"
        )
        
        # 更新 session_state
        selected_model_id = model_options[selected_name]
        if st.session_state.get('selected_model') != selected_model_id:
            st.session_state.selected_model = selected_model_id
            
            # 检查是否为推理模型
            model_config = config.get_llm_model_config(selected_model_id)
            if model_config and model_config.supports_reasoning:
                st.info(f"✅ 已切换到 {selected_name}（支持推理链）")
            else:
                st.info(f"✅ 已切换到 {selected_name}")
            
            if on_model_change:
                on_model_change(selected_model_id)
    
    except Exception as e:
        st.error(f"加载模型列表失败: {e}")
        st.session_state.selected_model = config.get_default_llm_id()


def render_llm_preset_selector(
    on_preset_change: Optional[Callable[[str], None]] = None,
) -> None:
    """渲染 LLM 预设选择器
    
    Args:
        on_preset_change: 预设变更回调
    """
    # 初始化状态
    if 'llm_preset' not in st.session_state:
        st.session_state.llm_preset = 'balanced'
    
    current_preset = st.session_state.llm_preset
    
    # 检查当前模型是否为推理模型（不支持 temperature）
    current_model_id = st.session_state.get(
        'selected_model', config.get_default_llm_id()
    )
    model_config = config.get_llm_model_config(current_model_id)
    is_reasoning_model = model_config and model_config.supports_reasoning
    
    # 构建选项
    preset_keys = list(LLM_PRESETS.keys())
    preset_names = [LLM_PRESETS[k]["name"] for k in preset_keys]
    
    current_index = preset_keys.index(current_preset) if current_preset in preset_keys else 1
    
    # 预设选择
    st.markdown("**🎨 回答风格**")
    
    if is_reasoning_model:
        st.caption("⚠️ 推理模型不支持调整风格")
        # 显示但禁用
        st.radio(
            "选择风格",
            options=preset_names,
            index=current_index,
            key="llm_preset_radio_disabled",
            disabled=True,
            label_visibility="collapsed",
        )
    else:
        selected_name = st.radio(
            "选择风格",
            options=preset_names,
            index=current_index,
            key="llm_preset_radio",
            label_visibility="collapsed",
        )
        
        # 更新预设
        selected_key = preset_keys[preset_names.index(selected_name)]
        if selected_key != current_preset:
            st.session_state.llm_preset = selected_key
            if on_preset_change:
                on_preset_change(selected_key)
    
    # 显示当前预设说明
    preset_info = LLM_PRESETS.get(current_preset, LLM_PRESETS["balanced"])
    st.caption(f"💡 {preset_info['description']}")
    
    if not is_reasoning_model:
        st.caption(f"Temperature: {preset_info['temperature']}")
