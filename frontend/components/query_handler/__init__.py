"""
查询处理组件模块
"""

import json
from pathlib import Path

import streamlit as st
from streamlit_chat import message
from frontend.components.query_handler.non_streaming import handle_non_streaming_query
from frontend.utils.helpers import generate_message_id


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
        chat_manager: 对话管理器实例
    """
    # 处理待处理的查询（快速开始）
    if 'pending_query' in st.session_state and st.session_state.pending_query:
        # #region agent log
        _debug_log("query_handler/__init__.py:branch", "branch pending_query", {"will_rerun": True}, "B")
        # #endregion
        prompt = st.session_state.pending_query
        del st.session_state.pending_query  # 清除待处理标记
        handle_non_streaming_query(rag_service, chat_manager, prompt)
        # #region agent log
        _debug_log("query_handler/__init__.py:before_rerun", "before st.rerun (pending_query)", hypothesis_id="B")
        # #endregion
        st.rerun()
        return

    # 处理词云/默认问题点击（填入并发送）
    if 'selected_question' in st.session_state and st.session_state.selected_question:
        prompt = st.session_state.selected_question
        st.session_state.selected_question = None  # 清除状态
        # 确保用户消息已添加到 messages（_on_use_question 已添加，但为了保险再检查一次）
        # #region agent log
        _debug_log("query_handler/__init__.py:branch", "branch selected_question", {"will_rerun": True}, "B")
        # #endregion
        if not st.session_state.messages or st.session_state.messages[-1].get("content") != prompt:
            user_msg = {"role": "user", "content": prompt}
            msg_id = generate_message_id(len(st.session_state.messages), user_msg)
            message(prompt, is_user=True, key=f"msg_user_{msg_id}")
            st.session_state.messages.append(user_msg)
        handle_non_streaming_query(rag_service, chat_manager, prompt)
        # #region agent log
        _debug_log("query_handler/__init__.py:before_rerun", "before st.rerun (selected_question)", hypothesis_id="B")
        # #endregion
        st.rerun()
        return
    
    # 处理用户输入
    if st.session_state.messages:
        from frontend.components.chat_input_with_mode import render_chat_input_with_mode
        prompt = render_chat_input_with_mode("给系统发送消息", key="main_chat_input")
        
        if prompt:
            # #region agent log
            _debug_log("query_handler/__init__.py:branch", "branch main_chat_input", {"will_rerun": False}, "B")
            # #endregion
            st.session_state.is_thinking = True
            user_msg = {"role": "user", "content": prompt}
            msg_id = generate_message_id(len(st.session_state.messages), user_msg)
            message(prompt, is_user=True, key=f"msg_user_{msg_id}")
            st.session_state.messages.append(user_msg)
            handle_non_streaming_query(rag_service, chat_manager, prompt)
            # #region agent log
            _debug_log("query_handler/__init__.py:after_query_no_rerun", "after handle_non_streaming_query (no rerun)", hypothesis_id="B")
            # #endregion


__all__ = ['handle_user_queries', 'handle_non_streaming_query']

