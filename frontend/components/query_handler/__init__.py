"""
查询处理组件模块
"""

import json
from pathlib import Path

import streamlit as st
from frontend.components.query_handler.streaming import handle_streaming_query
from frontend.config import USER_AVATAR
from frontend.utils.throttle import throttle_requests


def _debug_log(location: str, message: str, data: dict | None = None, hypothesis_id: str = "B") -> None:
    # #region agent log
    try:
        log_path = Path(__file__).resolve().parent.parent.parent.parent / ".cursor" / "debug.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": hypothesis_id, "location": location, "message": message, "data": data or {}, "timestamp": __import__("time").time() * 1000}, ensure_ascii=False) + "\n")
    except Exception:  # noqa: S110
        pass
    # #endregion


def handle_user_queries(rag_service, chat_manager) -> None:
    """处理用户查询（路由分发器）
    
    Args:
        rag_service: RAG服务实例
        chat_manager: 会话管理器实例
    """
    # 处理待处理的查询（快速启动）
    if 'pending_query' in st.session_state and st.session_state.pending_query:
        prompt = st.session_state.pending_query
        del st.session_state.pending_query  # 清除待处理标记

        should_render_inline = False
        if not st.session_state.messages or st.session_state.messages[-1].get("content") != prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            should_render_inline = True
        if should_render_inline:
            with st.chat_message("user", avatar=USER_AVATAR):
                st.markdown("<span class='chat-role-user-marker'></span>", unsafe_allow_html=True)
                st.markdown(prompt)

        # 仅在真正发起请求时节流，且在 UI 已渲染后执行
        throttle_requests()
        # #region agent log
        _debug_log("query_handler/__init__.py:branch", "branch pending_query", {"will_rerun": True}, "B")
        # #endregion
        handle_streaming_query(rag_service, chat_manager, prompt)
        # 成功时不再强制 rerun，避免页面出现“白蒙蒙”遮罩
        return

    # 处理示例/默认问题点击（填充并发送）
    if 'selected_question' in st.session_state and st.session_state.selected_question:
        prompt = st.session_state.selected_question
        st.session_state.selected_question = None  # 清除状态
        # #region agent log
        _debug_log("query_handler/__init__.py:branch", "branch selected_question", {"will_rerun": True}, "B")
        # #endregion
        if not st.session_state.messages or st.session_state.messages[-1].get("content") != prompt:
            user_msg = {"role": "user", "content": prompt}
            with st.chat_message("user", avatar=USER_AVATAR):
                st.markdown("<span class='chat-role-user-marker'></span>", unsafe_allow_html=True)
                st.markdown(prompt)
            st.session_state.messages.append(user_msg)
        # 仅在真正发起请求时节流，且在 UI 已渲染后执行
        throttle_requests()
        handle_streaming_query(rag_service, chat_manager, prompt)
        # 成功时不再强制 rerun，避免页面出现“白蒙蒙”遮罩
        return
    
    # 处理用户输入
    # 用户输入由 chat_display.py 中的 st.chat_input 写入 messages + pending_query。
    # 这里不再渲染第二套输入组件，避免布局错乱和重复提交。


__all__ = ['handle_user_queries', 'handle_streaming_query']
