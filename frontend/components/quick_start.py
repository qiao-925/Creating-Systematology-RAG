"""
快速开始组件：建议问题 pills + 输入框

按 Streamlit Assistant 的方式实现：
- 使用原生 st.chat_input
- 发送按钮由 Streamlit 内置，显示在输入框内右侧
"""

import streamlit as st

from frontend.components.keyword_cloud import render_keyword_cloud
from frontend.config import SUGGESTION_QUESTIONS


def render_quick_start() -> None:
    """渲染快速开始界面。"""
    # Put chat_input inside a non-root layout block to force inline rendering.
    # Streamlit 1.53 renders root-level chat_input at page bottom by design.
    col, = st.columns([1])
    with col:
        prompt = st.chat_input("输入问题...", key="initial_question")

    if prompt:
        return

    st.pills(
        label="试试这些问题",
        options=list(SUGGESTION_QUESTIONS.keys()),
        key="selected_suggestion",
        label_visibility="collapsed",
    )

    render_keyword_cloud()
