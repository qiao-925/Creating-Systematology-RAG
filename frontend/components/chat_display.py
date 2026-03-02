"""
对话显示组件
参考 Streamlit AI Assistant 设计：单列居中布局
"""

import streamlit as st
from frontend.utils.state import initialize_sources_map
from frontend.utils.sources import format_answer_with_citation_links
from frontend.components.sources_panel import display_sources_below_message
from frontend.components.chat_layout_helpers import (
    render_title_text,
    render_settings_icon,
    render_restart_icon,
    inject_settings_button_icon_css,
    inject_restart_button_icon_css,
    inject_landing_center_css,
    inject_landing_hide_script,
)
from frontend.config import (
    USER_AVATAR,
    ASSISTANT_AVATAR,
)
from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger('app')


def _clear_conversation(chat_manager) -> None:
    """清空对话的回调函数"""
    if chat_manager:
        chat_manager.start_session()
    st.session_state.messages = []
    if 'initial_question' in st.session_state:
        st.session_state.initial_question = None
    if 'initial_question_input' in st.session_state:
        st.session_state.initial_question_input = ""
    if 'selected_suggestion' in st.session_state:
        st.session_state.selected_suggestion = None
    if 'selected_question' in st.session_state:
        st.session_state.selected_question = None
    if 'pending_query' in st.session_state:
        st.session_state.pending_query = None
    if 'keyword_cloud_selected' in st.session_state:
        st.session_state.keyword_cloud_selected = []
    if 'keyword_cloud_generated' in st.session_state:
        st.session_state.keyword_cloud_generated = []
    if 'keyword_cloud_loading' in st.session_state:
        st.session_state.keyword_cloud_loading = False
    # 清空引用来源映射
    if 'current_sources_map' in st.session_state:
        st.session_state.current_sources_map = {}
    if 'current_reasoning_map' in st.session_state:
        st.session_state.current_reasoning_map = {}


def _on_settings_click() -> None:
    """设置按钮点击回调"""
    st.session_state.show_settings_dialog = True


def _render_title_row(chat_manager) -> None:
    """渲染标题行（标题 + Restart + 设置按钮）
    
    参考 Streamlit AI Assistant 布局：
    - 标题居左（宽度自适应）
    - Restart 按钮和设置按钮在右侧
    """
    # 如果用户刚触发提问（但消息尚未写入 messages），也要立即显示 Restart
    has_messages = bool(st.session_state.get('messages'))
    if not has_messages:
        has_messages = any(
            st.session_state.get(key)
            for key in (
                "initial_question",
                "selected_suggestion",
                "selected_question",
                "pending_query",
            )
        )

    inject_settings_button_icon_css()
    inject_restart_button_icon_css()
    
    title_row = st.container(horizontal=True, vertical_alignment="center")
    with title_row:
        title_block = st.container(width="stretch")
        with title_block:
            render_title_text()

        if has_messages:
            st.button(
                render_restart_icon(),
                on_click=_clear_conversation,
                args=(chat_manager,),
                key="restart_button",
                help="Restart",
            )

        settings_action = st.container(width="content", key="top_settings_action")
        with settings_action:
            st.button(
                render_settings_icon(),
                on_click=_on_settings_click,
                key="settings_button_top",
                help="设置",
                type="tertiary",
            )


def render_chat_interface(rag_service, chat_manager) -> None:
    """渲染对话界面
    
    参考 Streamlit AI Assistant 设计：
    - 标题行（标题 + Restart + 设置）
    - 无对话：建议问题 + 输入框
    - 有对话：对话气泡 + 输入框
    
    Args:
        rag_service: RAG服务实例
        chat_manager: 对话管理器实例
    """
    # 注入全局JavaScript脚本（仅一次，必须在渲染任何消息前）
    if not st.session_state.get('citation_script_injected', False):
        from frontend.utils.sources import inject_citation_script
        st.markdown(inject_citation_script(), unsafe_allow_html=True)
        st.session_state.citation_script_injected = True

    # 确保 messages 已初始化
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    has_messages = bool(st.session_state.messages)
    user_just_asked_initial = bool(st.session_state.get("initial_question"))
    user_just_clicked_suggestion = bool(st.session_state.get("selected_suggestion"))
    user_just_selected_question = bool(st.session_state.get("selected_question"))
    user_has_pending_query = bool(st.session_state.get("pending_query"))
    user_first_interaction = (
        user_just_asked_initial
        or user_just_clicked_suggestion
        or user_just_selected_question
        or user_has_pending_query
    )

    logger.debug(
        "render_chat_interface 状态检查",
        has_messages=has_messages,
        messages_count=len(st.session_state.get("messages", [])),
        user_just_asked_initial=user_just_asked_initial,
        user_just_clicked_suggestion=user_just_clicked_suggestion,
        user_just_selected_question=user_just_selected_question,
        user_has_pending_query=user_has_pending_query,
        user_first_interaction=user_first_interaction,
        will_show_landing=(not has_messages) and (not user_first_interaction)
    )

    # 仅首屏（无对话、无待处理输入）上下居中，进入对话后恢复顶部布局
    if (not has_messages) and (not user_first_interaction):
        inject_landing_center_css()
        with st.container(key="landing_center_shell"):
            _render_title_row(chat_manager)

            if st.session_state.get("show_settings_dialog", False):
                from frontend.components.settings_dialog import show_settings_dialog

                show_settings_dialog()
                st.session_state.show_settings_dialog = False

            initialize_sources_map()
            from frontend.components.quick_start import render_quick_start

            render_quick_start()
        inject_landing_hide_script()
        st.stop()

    # 渲染标题行（标题 + Restart + 设置按钮）
    _render_title_row(chat_manager)

    # 检查是否需要显示设置弹窗
    if st.session_state.get("show_settings_dialog", False):
        from frontend.components.settings_dialog import show_settings_dialog

        show_settings_dialog()
        st.session_state.show_settings_dialog = False

    # 初始化来源映射
    initialize_sources_map()

    render_chat_history()

    
    # 底部输入框（有对话历史时显示）
    user_message = st.chat_input("输入追问...")
    if user_message:
        st.session_state.pending_query = user_message


def render_chat_history() -> None:
    """渲染对话历史（st.chat_message 气泡 + 延续块）"""
    from frontend.utils.helpers import generate_message_id
    for idx, msg in enumerate(st.session_state.messages):
        message_id = generate_message_id(idx, msg)
        role = msg["role"]
        if role == "user":
            with st.chat_message("user", avatar=USER_AVATAR):
                st.markdown("<span class='chat-role-user-marker'>User:</span>", unsafe_allow_html=True)
                st.markdown(msg["content"])
        else:
            if "sources" in msg and msg["sources"]:
                formatted_content = format_answer_with_citation_links(
                    msg["content"],
                    msg["sources"],
                    message_id=message_id
                )
            else:
                formatted_content = msg["content"]
            with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
                st.markdown("<span class='chat-role-assistant-marker'>System:</span>", unsafe_allow_html=True)
                st.container()  # Fix ghost message bug.
                st.markdown(formatted_content, unsafe_allow_html=True)
            render_assistant_continuation(message_id, msg)
        st.session_state.current_sources_map = st.session_state.current_sources_map
        st.session_state.current_reasoning_map = st.session_state.current_reasoning_map


def render_assistant_continuation(message_id: str, msg: dict) -> None:
    """渲染助手消息延续块（推理、引用来源）。"""
    st.markdown(
        f"<div class='message-continuation-anchor' data-message-id='{message_id}'></div>",
        unsafe_allow_html=True,
    )
    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        st.markdown("<span class='chat-role-assistant-marker'>System:</span>", unsafe_allow_html=True)
        reasoning_content = msg.get("reasoning_content")
        if reasoning_content:
            with st.expander("🧠 推理过程", expanded=False):
                st.markdown(f"```\n{reasoning_content}\n```")
        elif config.DEEPSEEK_ENABLE_REASONING_DISPLAY:
            logger.debug(f"消息 {message_id} 没有推理链内容")
        sources = st.session_state.current_sources_map.get(message_id, [])
        if sources:
            st.markdown("#### 📚 引用来源")
            display_sources_below_message(sources, message_id=message_id)
