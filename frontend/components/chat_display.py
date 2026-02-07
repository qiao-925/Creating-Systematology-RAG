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
from frontend.config import (
    SUGGESTION_QUESTIONS,
    USER_AVATAR,
    ASSISTANT_AVATAR,
    APP_TITLE_TEXT_SVG_HEIGHT_PX,
    SETTINGS_ICON_SIZE_PX,
    RESTART_ICON_SIZE_PX,
    get_restart_icon_svg_data_uri,
    get_settings_icon_svg_data_uri,
    get_title_text_svg_data_uri,
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
    # 清空观察器日志
    if 'llama_debug_logs' in st.session_state:
        st.session_state.llama_debug_logs = []
    if 'ragas_logs' in st.session_state:
        st.session_state.ragas_logs = []


def _on_settings_click() -> None:
    """设置按钮点击回调"""
    st.session_state.show_settings_dialog = True


def _render_title_text() -> None:
    """渲染标题文字：优先 SVG，缺失时回退普通标题文本。"""
    title_text_svg_data_uri = get_title_text_svg_data_uri()
    if title_text_svg_data_uri:
        st.markdown(
            (
                f"<img src='{title_text_svg_data_uri}' "
                f"height='{APP_TITLE_TEXT_SVG_HEIGHT_PX}' "
                "style='display:block;width:auto;max-width:100%;margin:.3rem 0 .25rem 0;' "
                "alt='title-text'/>"
            ),
            unsafe_allow_html=True,
        )
        return

    st.title(config.APP_TITLE, anchor=False, width="stretch")


def _render_settings_icon() -> str:
    """返回设置按钮文本：SVG 可用时返回占位文本，否则回退符号。"""
    svg_data_uri = get_settings_icon_svg_data_uri()
    if svg_data_uri:
        return " "
    return "⚙︎"


def _render_restart_icon() -> str:
    """返回重置按钮文本：SVG 可用时返回占位文本，否则回退符号。"""
    svg_data_uri = get_restart_icon_svg_data_uri()
    if svg_data_uri:
        return " "
    return "↻"


def _inject_settings_button_icon_css() -> None:
    """为设置按钮注入 SVG 图标样式（仅视觉，不影响按钮行为）。"""
    svg_data_uri = get_settings_icon_svg_data_uri()
    if not svg_data_uri:
        return

    st.markdown(
        f"""
<style>
.st-key-settings_button_top button,
.st-key-settings_button_top [data-testid="stBaseButton-tertiary"] {{
    width: {SETTINGS_ICON_SIZE_PX + 10}px !important;
    min-width: {SETTINGS_ICON_SIZE_PX + 10}px !important;
    height: {SETTINGS_ICON_SIZE_PX + 10}px !important;
    padding: 0 !important;
    border: none !important;
    border-radius: 0 !important;
    background-color: transparent !important;
    color: #87E7A9 !important;
    font-size: 0 !important;
    line-height: 0 !important;
    box-shadow: none !important;
}}

.st-key-settings_button_top button::before,
.st-key-settings_button_top [data-testid="stBaseButton-tertiary"]::before {{
    content: "";
    display: block;
    width: {SETTINGS_ICON_SIZE_PX}px;
    height: {SETTINGS_ICON_SIZE_PX}px;
    margin: 0 auto;
    background-color: currentColor;
    -webkit-mask: url('{svg_data_uri}') center / contain no-repeat;
    mask: url('{svg_data_uri}') center / contain no-repeat;
}}

.st-key-settings_button_top button:hover,
.st-key-settings_button_top [data-testid="stBaseButton-tertiary"]:hover,
.st-key-settings_button_top button:focus-visible,
.st-key-settings_button_top [data-testid="stBaseButton-tertiary"]:focus-visible {{
    border: none !important;
    background-color: transparent !important;
    color: #B6F2C8 !important;
    box-shadow: none !important;
    outline: none !important;
    transform: none !important;
}}
</style>
        """,
        unsafe_allow_html=True,
    )


def _inject_restart_button_icon_css() -> None:
    """为重置按钮注入 SVG 图标样式（仅视觉，不影响按钮行为）。"""
    svg_data_uri = get_restart_icon_svg_data_uri()
    if not svg_data_uri:
        return

    st.markdown(
        f"""
<style>
.st-key-restart_button button,
.st-key-restart_button [data-testid="stBaseButton-secondary"] {{
    width: {RESTART_ICON_SIZE_PX + 10}px !important;
    min-width: {RESTART_ICON_SIZE_PX + 10}px !important;
    height: {RESTART_ICON_SIZE_PX + 10}px !important;
    padding: 0 !important;
    border: none !important;
    border-radius: 0 !important;
    background-color: transparent !important;
    color: #87E7A9 !important;
    font-size: 0 !important;
    line-height: 0 !important;
    box-shadow: none !important;
}}

.st-key-restart_button button::before,
.st-key-restart_button [data-testid="stBaseButton-secondary"]::before {{
    content: "";
    display: block;
    width: {RESTART_ICON_SIZE_PX}px;
    height: {RESTART_ICON_SIZE_PX}px;
    margin: 0 auto;
    background-color: currentColor;
    -webkit-mask: url('{svg_data_uri}') center / contain no-repeat;
    mask: url('{svg_data_uri}') center / contain no-repeat;
}}

.st-key-restart_button button:hover,
.st-key-restart_button [data-testid="stBaseButton-secondary"]:hover,
.st-key-restart_button button:focus-visible,
.st-key-restart_button [data-testid="stBaseButton-secondary"]:focus-visible {{
    border: none !important;
    background-color: transparent !important;
    color: #B6F2C8 !important;
    box-shadow: none !important;
    outline: none !important;
    transform: none !important;
}}
</style>
        """,
        unsafe_allow_html=True,
    )


def _inject_landing_center_css() -> None:
    """首屏状态下让标题+输入区块上下居中。"""
    st.markdown(
        """
<style>
.st-key-landing_center_shell {
    min-height: calc(100vh - 8.8rem) !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    width: 100% !important;
    padding-bottom: 6vh !important;
}

@media (max-width: 768px) {
    .st-key-landing_center_shell {
        min-height: calc(100vh - 7rem) !important;
        padding-bottom: 3.5vh !important;
    }
}
</style>
        """,
        unsafe_allow_html=True,
    )


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

    _inject_settings_button_icon_css()
    _inject_restart_button_icon_css()
    
    title_row = st.container(horizontal=True, vertical_alignment="center")
    with title_row:
        title_block = st.container(width="stretch")
        with title_block:
            _render_title_text()

        if has_messages:
            st.button(
                _render_restart_icon(),
                on_click=_clear_conversation,
                args=(chat_manager,),
                key="restart_button",
                help="Restart",
            )

        settings_action = st.container(width="content", key="top_settings_action")
        with settings_action:
            st.button(
                _render_settings_icon(),
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

    has_messages = bool(st.session_state.get("messages"))
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

    # 仅首屏（无对话、无待处理输入）上下居中，进入对话后恢复顶部布局
    if (not has_messages) and (not user_first_interaction):
        _inject_landing_center_css()
        with st.container(key="landing_center_shell"):
            _render_title_row(chat_manager)

            if st.session_state.get("show_settings_dialog", False):
                from frontend.components.settings_dialog import show_settings_dialog

                show_settings_dialog()
                st.session_state.show_settings_dialog = False

            initialize_sources_map()
            from frontend.components.quick_start import render_quick_start

            render_quick_start()
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

    if not has_messages:
        if not user_first_interaction:
            from frontend.components.quick_start import render_quick_start
            render_quick_start()
            st.stop()
        else:
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
                st.markdown("<span class='chat-role-user-marker'></span>", unsafe_allow_html=True)
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
                st.markdown("<span class='chat-role-assistant-marker'></span>", unsafe_allow_html=True)
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
    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        st.markdown("<span class='chat-role-assistant-marker'></span>", unsafe_allow_html=True)
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
