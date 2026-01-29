"""
快速开始组件：词云选词 + 生成问题 + 输入框。
使用 on_click 回调优化，避免不必要的 st.rerun()。
"""

import streamlit as st

from frontend.components.chat_input_with_mode import render_chat_input_with_mode
from frontend.components.keyword_cloud import render_keyword_cloud


def render_quick_start() -> None:
    """渲染快速开始界面：探索知识库词云 + 输入框。"""
    render_keyword_cloud()
    st.markdown("---")
    prompt = render_chat_input_with_mode("给系统发送消息", key="main_chat_input")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.pending_query = prompt
