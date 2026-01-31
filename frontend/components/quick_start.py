"""
快速开始组件：建议问题 pills + 输入框
参考 Streamlit AI Assistant 设计
"""

import streamlit as st

from frontend.components.keyword_cloud import render_keyword_cloud
from frontend.config import SUGGESTION_QUESTIONS


def render_quick_start() -> None:
    """渲染快速开始界面：输入框 + 建议问题 pills
    
    参考 Streamlit AI Assistant 设计：
    - chat_input 在上
    - pills 建议问题在下
    """
    st.markdown(
        """
        <style>
        .quickstart-row {
            position: relative;
        }
        .quickstart-row [data-testid="stHorizontalBlock"] {
            gap: 0;
        }
        .quickstart-row .stTextInput > div > div {
            border-radius: var(--chat-input-radius);
        }
        .quickstart-row .stTextInput input {
            border-radius: var(--chat-input-radius);
            height: var(--chat-input-height);
            padding: var(--chat-input-pad-y) var(--chat-input-pad-right) var(--chat-input-pad-y) var(--chat-input-pad-x);
            background: var(--chat-input-bg);
            border: 1px solid var(--chat-input-border);
            color: var(--chat-input-text);
        }
        .quickstart-row .stTextInput input::placeholder {
            color: var(--chat-input-placeholder);
        }
        .quickstart-row .quickstart-send-btn {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            z-index: 3;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .quickstart-row .quickstart-send-btn .stButton {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .quickstart-row .quickstart-send-btn button {
            width: 40px;
            min-width: 40px;
            height: 40px;
            padding: 0;
            border-radius: 999px;
            background: var(--chat-input-bg);
            color: var(--chat-input-text);
            border: 1px solid var(--chat-input-border);
            transition: all 0.16s ease;
        }
        .quickstart-row .quickstart-send-btn button:hover:not(:disabled) {
            background: var(--primary-color);
            border-color: var(--primary-color);
            color: #ffffff;
        }
        .quickstart-row .quickstart-send-btn button:disabled {
            opacity: 0.45;
            cursor: not-allowed;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="quickstart-row">', unsafe_allow_html=True)
    col_input, col_send = st.columns([1, 0.01])
    with col_input:
        prompt = st.text_input("输入追问...", key="initial_question_input", label_visibility="collapsed")
    with col_send:
        st.markdown('<div class="quickstart-send-btn">', unsafe_allow_html=True)
        submitted = st.button(
            "",
            icon=":material/arrow_upward:",
            type="secondary",
            use_container_width=False,
            disabled=not prompt.strip(),
            help="quick-start-send"
        )
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if submitted and prompt:
        st.session_state.initial_question = prompt
        st.session_state.initial_question_input = ""
        return
    
    # 建议问题 pills
    st.pills(
        label="试试这些问题",
        options=list(SUGGESTION_QUESTIONS.keys()),
        key="selected_suggestion",
        label_visibility="collapsed",
    )

    # 气泡选择器（词云）放在输入框下方
    render_keyword_cloud()
