"""
快速开始组件
"""

import streamlit as st
from frontend.components.chat_input_with_mode import render_chat_input_with_mode
from frontend.config import DEFAULT_QUESTIONS


def render_quick_start() -> None:
    """渲染快速开始界面"""
    st.subheader("💡 快速开始")
    st.caption("点击下方问题快速体验")
    
    # 使用两列布局展示问题按钮
    col1, col2 = st.columns(2)
    for idx, question in enumerate(DEFAULT_QUESTIONS):
        col = col1 if idx % 2 == 0 else col2
        with col:
            if st.button(f"💬 {question}", key=f"default_q_{idx}", use_container_width=True):
                # 立即将用户消息添加到历史，避免rerun后再次显示"快速开始"
                st.session_state.messages.append({"role": "user", "content": question})
                # 将问题设置为用户输入（用于触发查询）
                st.session_state.selected_question = question
                st.rerun()
    
    # 在快速开始下方添加输入框和模式切换按钮
    st.markdown("---")  # 添加分隔线
    # 只显示输入框和模式切换按钮，不在这里处理逻辑（因为一旦有消息，快速开始就会消失）
    prompt = render_chat_input_with_mode("给系统发送消息", key="main_chat_input")
    
    # 处理输入框的发送逻辑（只在没有对话历史时执行）
    # 注意：一旦有消息，下次 rerun 时快速开始就不会显示了
    if prompt:
        # 添加用户消息到历史（这会导致快速开始消失）
        st.session_state.messages.append({"role": "user", "content": prompt})
        # 设置待处理的查询，在 rerun 后处理
        st.session_state.pending_query = prompt
        # 立即 rerun，让快速开始消失
        st.rerun()
