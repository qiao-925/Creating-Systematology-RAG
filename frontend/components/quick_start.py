"""
快速开始组件：建议问题 pills + 输入框
参考 Streamlit AI Assistant 设计
"""

import streamlit as st

from frontend.config import SUGGESTION_QUESTIONS


def render_quick_start() -> None:
    """渲染快速开始界面：输入框 + 建议问题 pills
    
    参考 Streamlit AI Assistant 设计：
    - chat_input 在上
    - pills 建议问题在下
    """
    # 检查是否点击了建议问题
    if st.session_state.get('selected_suggestion'):
        selected_label = st.session_state.selected_suggestion
        if selected_label in SUGGESTION_QUESTIONS:
            question = SUGGESTION_QUESTIONS[selected_label]
            st.session_state.messages.append({"role": "user", "content": question})
            st.session_state.pending_query = question
            st.session_state.selected_suggestion = None
            return
    
    # 输入框
    prompt = st.chat_input("输入问题...", key="initial_question")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.pending_query = prompt
        return
    
    # 建议问题 pills
    st.pills(
        label="试试这些问题",
        options=list(SUGGESTION_QUESTIONS.keys()),
        key="selected_suggestion",
        label_visibility="collapsed",
    )
