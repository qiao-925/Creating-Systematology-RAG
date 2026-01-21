"""
快速开始组件
使用 on_click 回调优化，避免不必要的 st.rerun()
"""

import streamlit as st
from frontend.components.chat_input_with_mode import render_chat_input_with_mode
from frontend.config import DEFAULT_QUESTIONS


def _create_question_callback(question: str):
    """创建问题按钮的回调函数（闭包捕获 question）"""
    def callback():
        st.session_state.messages.append({"role": "user", "content": question})
        st.session_state.selected_question = question
    return callback


def render_quick_start() -> None:
    """渲染快速开始界面"""
    st.subheader("💡 快速开始")
    st.caption("点击下方问题快速体验")
    
    # 使用两列布局展示问题按钮
    col1, col2 = st.columns(2)
    for idx, question in enumerate(DEFAULT_QUESTIONS):
        col = col1 if idx % 2 == 0 else col2
        with col:
            # 使用 on_click 回调，按钮点击本身会触发重执行
            st.button(
                f"💬 {question}", 
                key=f"default_q_{idx}", 
                use_container_width=True,
                on_click=_create_question_callback(question)
            )
    
    # 在快速开始下方添加输入框和模式切换按钮
    st.markdown("---")
    prompt = render_chat_input_with_mode("给系统发送消息", key="main_chat_input")
    
    # 处理输入框的发送逻辑
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.pending_query = prompt
        # 不需要 st.rerun()，状态已更新，脚本会自然重执行
