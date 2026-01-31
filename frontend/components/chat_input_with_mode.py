"""
聊天输入组件（带模式切换）
参考 DeepSeek 设计：整合输入框和按钮在一个容器中
使用 on_click 回调优化，避免不必要的 st.rerun()

主要功能：
- render_chat_input_with_mode()：渲染整合的输入区域（输入框 + 按钮）
- 处理 Agentic RAG 状态切换逻辑（使用统一的 rebuild_services）

布局设计：
- 输入框
- [🤖 Agentic] [⚙️] ─── [发送]
- 选择 AI 模型（单选，在对话框下）
"""

import streamlit as st
from typing import Optional

from frontend.utils.state import rebuild_services
from backend.infrastructure.config import config
from backend.infrastructure.llms import get_available_models


def _on_send_click(input_key: str) -> None:
    """发送按钮点击回调"""
    st.session_state[f'{input_key}_send_clicked'] = True


def _on_agentic_toggle() -> None:
    """Agentic RAG 切换回调"""
    new_state = not st.session_state.use_agentic_rag
    st.session_state.use_agentic_rag = new_state
    rebuild_services()


def _on_params_click() -> None:
    """参数配置按钮点击回调"""
    st.session_state.show_params_dialog = True


def _on_model_change_below() -> None:
    """对话框下方模型单选变更：同步 selected_model 并重建服务"""
    name = st.session_state.get("model_selector_below", "")
    if not name:
        return
    try:
        models = get_available_models()
        model_options = {m.name: m.id for m in models}
        if name in model_options:
            st.session_state.selected_model = model_options[name]
            rebuild_services()
    except Exception:
        pass


def _render_model_selector_below() -> None:
    """对话框下方模型选择：单选列表"""
    try:
        models = get_available_models()
        if not models:
            return
        model_options = {m.name: m.id for m in models}
        model_names = list(model_options.keys())
        current_model_id = st.session_state.get("selected_model", config.get_default_llm_id())
        current_index = 0
        for i, (name, mid) in enumerate(model_options.items()):
            if mid == current_model_id:
                current_index = i
                break
        st.caption("选择 AI 模型：")
        st.radio(
            "选择 AI 模型",
            options=model_names,
            index=current_index,
            key="model_selector_below",
            label_visibility="collapsed",
            on_change=_on_model_change_below,
        )
    except Exception:
        pass


def render_chat_input_with_mode(
    placeholder: str = "给系统发送消息",
    key: str = "chat_input",
    disabled: bool = False
) -> Optional[str]:
    """渲染整合的聊天输入区域（参考 DeepSeek 设计）
    
    布局：
    - 上方：输入框
    - 下方：[🤖 Agentic] [⚙️] ─── [发送]
    
    Args:
        placeholder: 输入框占位符文本
        key: Streamlit组件key
        disabled: 是否禁用输入框（思考中时隐藏）
        
    Returns:
        用户输入的文本，如果未输入或未点击发送则返回None
    """
    from frontend.components.params_dialog import show_params_dialog
    
    # 初始化状态
    if 'use_agentic_rag' not in st.session_state:
        st.session_state.use_agentic_rag = False
    if f'{key}_input_value' not in st.session_state:
        st.session_state[f'{key}_input_value'] = ''
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = config.get_default_llm_id()
    
    # 检查是否发送（在渲染之前检查）
    user_input = None
    if st.session_state.get(f'{key}_send_clicked', False):
        user_input = st.session_state.get(f'{key}_input_value', '').strip()
        if user_input:
            st.session_state[f'{key}_input_value'] = ''
        st.session_state[f'{key}_send_clicked'] = False
    
    # 渲染输入区域
    with st.container():
        st.markdown("<br>", unsafe_allow_html=True)
        
        if not disabled:
            input_value = st.text_area(
                placeholder,
                value=st.session_state[f'{key}_input_value'],
                key=f'{key}_textarea',
                height=120,
                disabled=disabled,
                label_visibility="collapsed",
                help="输入消息，按 Ctrl+Enter 发送，Shift+Enter 换行"
            )
            st.session_state[f'{key}_input_value'] = input_value
            _render_input_actions(key, input_value.strip())
        else:
            _render_input_actions(key, '')
        # 对话框下方：模型选择
        _render_model_selector_below()
    
    # 检查是否需要显示参数配置弹窗
    if st.session_state.get("show_params_dialog", False):
        show_params_dialog()
        st.session_state.show_params_dialog = False
    
    return user_input


def _render_input_actions(input_key: str, input_value: str) -> None:
    """渲染输入区域下方的操作按钮
    
    布局：[🤖 Agentic] [⚙️] ─── [发送]
    """
    col_agentic, col_params, col_spacer, col_send = st.columns([1.5, 0.5, 2, 1])
    
    with col_agentic:
        _render_agentic_rag_toggle()
    
    with col_params:
        st.button(
            "⚙️",
            key="params_button",
            help="参数配置",
            on_click=_on_params_click,
        )

    with col_send:
        st.button(
            "发送",
            key=f"{input_key}_send_button",
            type="primary",
            use_container_width=True,
            disabled=not input_value,
            on_click=_on_send_click,
            args=(input_key,)
        )


def _render_agentic_rag_toggle() -> None:
    """渲染 Agentic RAG 模式切换按钮"""
    current_state = st.session_state.use_agentic_rag
    
    button_type = "primary" if current_state else "secondary"
    button_help = (
        "点击禁用 Agentic RAG" if current_state 
        else "启用 Agentic RAG：AI 自主选择策略"
    )
    
    st.button(
        "🤖 Agentic",
        key="agentic_rag_toggle",
        type=button_type,
        use_container_width=True,
        help=button_help,
        on_click=_on_agentic_toggle
    )
