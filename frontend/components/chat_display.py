"""
对话显示组件
参考 Streamlit AI Assistant 设计：单列居中布局
"""

import streamlit as st
from frontend.utils.state import initialize_sources_map
from frontend.utils.sources import format_answer_with_citation_links
from frontend.components.sources_panel import display_sources_below_message
from frontend.components.observability_summary import render_observability_summary
from frontend.components.observer_renderers import render_llamadebug_full_info, render_ragas_full_info
from frontend.config import SUGGESTION_QUESTIONS
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
    # 清空观察器日志
    if 'llama_debug_logs' in st.session_state:
        st.session_state.llama_debug_logs = []
    if 'ragas_logs' in st.session_state:
        st.session_state.ragas_logs = []


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
    
    title_row = st.container()
    with title_row:
        col_title, col_restart, col_settings = st.columns([8, 1, 1])
        
        with col_title:
            st.title("✨ ")
            st.title(config.APP_TITLE, anchor=False)
        
        with col_restart:
            if has_messages:
                st.button(
                    "",
                    icon=":material/refresh:",
                    on_click=_clear_conversation,
                    args=(chat_manager,),
                    key="restart_button",
                    help="Restart"
                )

        with col_settings:
            st.button(
                "",
                icon=":material/settings:",
                on_click=_on_settings_click,
                key="settings_button_top",
                help="设置"
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
    # 统一处理会话加载（优化：减少 rerun 次数）
    if st.session_state.get('session_loading_pending') or st.session_state.get('load_session_id'):
        from frontend.components.session_loader import load_history_session
        if load_history_session(chat_manager):
            st.rerun()
    
    # 注入全局JavaScript脚本（仅一次，必须在渲染任何消息前）
    if not st.session_state.get('citation_script_injected', False):
        from frontend.utils.sources import inject_citation_script
        st.markdown(inject_citation_script(), unsafe_allow_html=True)
        st.session_state.citation_script_injected = True
    
    # 渲染标题行（标题 + Restart + 设置按钮）
    _render_title_row(chat_manager)
    
    # 检查是否需要显示设置弹窗
    if st.session_state.get("show_settings_dialog", False):
        from frontend.components.settings_dialog import show_settings_dialog
        show_settings_dialog()
        st.session_state.show_settings_dialog = False
    
    # 初始化来源映射
    initialize_sources_map()

    # Quick start placeholder: clear stale first-screen content on reruns
    quick_start_ph = st.empty()

    # ??????????????? + ?????
    if not st.session_state.messages:
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

        if not user_first_interaction:
            from frontend.components.quick_start import render_quick_start
            with quick_start_ph.container():
                render_quick_start()
            # ???? demo??????????????????????????/??
            st.stop()
        else:
            # ???? messages ??????????
            quick_start_ph.empty()
            if user_just_asked_initial:
                prompt = st.session_state.initial_question
            elif user_just_clicked_suggestion:
                selected_label = st.session_state.selected_suggestion
                prompt = SUGGESTION_QUESTIONS.get(selected_label, selected_label)
            else:
                prompt = None

            if prompt:
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.pending_query = prompt
                st.session_state.initial_question = None
                st.session_state.selected_suggestion = None
                if 'initial_question_input' in st.session_state:
                    st.session_state.initial_question_input = ""
    else:
        # ??????????????
        quick_start_ph.empty()

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
            with st.chat_message("user"):
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
            with st.chat_message("assistant"):
                st.container()  # Fix ghost message bug.
                st.markdown(formatted_content, unsafe_allow_html=True)
            render_assistant_continuation(idx, message_id, msg)
        st.session_state.current_sources_map = st.session_state.current_sources_map
        st.session_state.current_reasoning_map = st.session_state.current_reasoning_map


def render_assistant_continuation(message_index: int, message_id: str, msg: dict) -> None:
    """渲染助手消息延续块（观察器、推理、引用来源），样式与气泡统一由 CP4 CSS 处理。"""
    st.markdown(
        f"<div class='message-continuation-anchor' data-message-id='{message_id}'></div>",
        unsafe_allow_html=True,
    )
    with st.chat_message("assistant"):
        _render_observer_info(message_index)
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


def _render_observer_info(message_index: int) -> None:
    """渲染观察器信息（在答案前显示）
    
    Args:
        message_index: 消息索引（assistant消息的索引）
    """
    # 初始化日志存储
    if 'llama_debug_logs' not in st.session_state:
        st.session_state.llama_debug_logs = []
    if 'ragas_logs' not in st.session_state:
        st.session_state.ragas_logs = []
    
    # 获取观察器日志
    debug_logs = st.session_state.llama_debug_logs
    ragas_logs = st.session_state.ragas_logs
    
    # 计算assistant消息的数量（用于匹配日志）
    assistant_count = sum(1 for msg in st.session_state.messages[:message_index+1] if msg.get("role") == "assistant")
    
    # 找到对应的日志（通过assistant消息数量匹配）
    debug_log = None
    ragas_log = None
    
    # 如果日志数量足够，使用对应的日志
    if len(debug_logs) >= assistant_count:
        debug_log = debug_logs[assistant_count - 1]
    elif len(debug_logs) > 0:
        # 否则使用最新的日志
        debug_log = debug_logs[-1]
    
    if len(ragas_logs) >= assistant_count:
        ragas_log = ragas_logs[assistant_count - 1]
    elif len(ragas_logs) > 0:
        ragas_log = ragas_logs[-1]
    
    # 显示观察器信息（如果有）- 分层展示
    if debug_log or ragas_log:
        # L0 + L1: 智能摘要（始终显示，集成 RAGAS）
        if debug_log:
            render_observability_summary(debug_log, ragas_log=ragas_log, show_l2=False)
        
        # L2: 完整链路（折叠，供开发者调试）
        with st.expander("🔬 完整链路详情（开发者）", expanded=False):
            if debug_log:
                render_llamadebug_full_info(debug_log)
            
            if ragas_log:
                st.divider()
                render_ragas_full_info(ragas_log)

