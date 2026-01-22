"""
聊天输入组件（带模式切换）
参考 DeepSeek 设计：整合输入框和按钮在一个容器中
使用 on_click 回调优化，避免不必要的 st.rerun()

主要功能：
- render_chat_input_with_mode()：渲染整合的输入区域（输入框 + 按钮）
- 处理 Agentic RAG 状态切换逻辑（使用统一的 rebuild_services）
"""

import streamlit as st
from typing import Optional

from frontend.utils.state import rebuild_services


def _on_send_click(input_key: str) -> None:
    """发送按钮点击回调"""
    st.session_state[f'{input_key}_send_clicked'] = True


def _on_agentic_toggle() -> None:
    """Agentic RAG 切换回调
    
    在回调中切换状态并重建服务，使用统一的 rebuild_services()
    """
    # 切换状态
    new_state = not st.session_state.use_agentic_rag
    st.session_state.use_agentic_rag = new_state
    
    # 使用统一的服务重建函数
    rebuild_services()


def render_chat_input_with_mode(
    placeholder: str = "给系统发送消息",
    key: str = "chat_input",
    disabled: bool = False
) -> Optional[str]:
    """渲染整合的聊天输入区域（参考 DeepSeek 设计）
    
    布局：
    - 上方：输入框
    - 下方：选项按钮（Agentic RAG）和发送按钮
    
    Args:
        placeholder: 输入框占位符文本
        key: Streamlit组件key
        disabled: 是否禁用输入框（思考中时隐藏）
        
    Returns:
        用户输入的文本，如果未输入或未点击发送则返回None
    """
    # 初始化状态
    if 'use_agentic_rag' not in st.session_state:
        st.session_state.use_agentic_rag = False
    if f'{key}_input_value' not in st.session_state:
        st.session_state[f'{key}_input_value'] = ''
    
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
                help="输入消息，按 Shift+Enter 换行，点击发送按钮发送"
            )
            st.session_state[f'{key}_input_value'] = input_value
            _render_input_actions(key, input_value.strip())
        else:
            _render_input_actions(key, '')
    
    return user_input


def _render_input_actions(input_key: str, input_value: str) -> None:
    """渲染输入区域下方的操作按钮"""
    col_left, col_right = st.columns([3, 1])
    
    with col_left:
        _render_agentic_rag_toggle()
    
    with col_right:
        # 使用 on_click 回调，避免 rerun
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
        "点击禁用 Agentic RAG 模式" if current_state 
        else "点击启用 Agentic RAG 模式：AI 将自主选择检索策略。适合复杂查询，但响应时间可能稍长。"
    )
    
    # 使用 on_click 回调，避免 rerun
    st.button(
        "🤖 Agentic RAG",
        key="agentic_rag_toggle",
        type=button_type,
        use_container_width=False,
        help=button_help,
        on_click=_on_agentic_toggle
    )
