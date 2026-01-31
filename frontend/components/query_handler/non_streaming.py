"""
非流式查询处理组件
使用 st.status 组件显示查询进度
"""

import json
from pathlib import Path

import streamlit as st
from frontend.utils.sources import convert_sources_to_dict
from frontend.utils.state import save_message_to_history
from frontend.utils.sources import format_answer_with_citation_links
from frontend.components.query_handler.common import save_to_chat_manager
from frontend.components.chat_display import render_assistant_continuation
from backend.infrastructure.logger import get_logger

logger = get_logger('app')


def _debug_log(location: str, message: str, data: dict | None = None, hypothesis_id: str = "A") -> None:
    # #region agent log
    try:
        log_path = Path(__file__).resolve().parent.parent.parent.parent / ".cursor" / "debug.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": hypothesis_id, "location": location, "message": message, "data": data or {}, "timestamp": __import__("time").time() * 1000}, ensure_ascii=False) + "\n")
    except Exception:  # noqa: S110
        pass
    # #endregion

def handle_non_streaming_query(rag_service, chat_manager, prompt: str) -> None:
    """处理非流式查询（带进度展示）
    
    Args:
        rag_service: RAG服务实例
        chat_manager: 对话管理器实例
        prompt: 用户查询
    """
    # #region agent log
    _debug_log("non_streaming.py:entry", "handle_non_streaming_query entry", {"prompt_len": len(prompt)})
    # #endregion
    with st.status("🤔 思考中...", expanded=False) as status:
        try:
            # #region agent log
            _debug_log("non_streaming.py:before_first_status_update", "before first status.update", hypothesis_id="A")
            # #endregion
            status.update(label="📝 理解问题...")
            status.update(label="🔍 检索相关文档...")
            # #region agent log
            _debug_log("non_streaming.py:before_query", "before rag_service.query", hypothesis_id="A")
            # #endregion
            response = rag_service.query(
                question=prompt,
                user_id=None,
                session_id=chat_manager.current_session.session_id if chat_manager.current_session else None,
            )
            # #region agent log
            _debug_log("non_streaming.py:after_query", "after rag_service.query", hypothesis_id="A")
            # #endregion
            answer = response.answer
            local_sources = convert_sources_to_dict(response.sources)
            reasoning_content = response.metadata.get('reasoning_content')
            sources_count = len(local_sources) if local_sources else 0
            # #region agent log
            _debug_log("non_streaming.py:before_status_complete", "before status.update(complete)", hypothesis_id="A")
            # #endregion
            status.update(label=f"✅ 完成 · 检索到 {sources_count} 篇文档", state="complete")
            from frontend.utils.helpers import generate_message_id
            msg_idx = len(st.session_state.messages)
            message_id = generate_message_id(msg_idx, answer)
            save_message_to_history(answer, local_sources, reasoning_content)
            save_to_chat_manager(chat_manager, prompt, answer, local_sources, reasoning_content)
            if local_sources:
                formatted_content = format_answer_with_citation_links(
                    answer, local_sources, message_id=message_id
                )
            else:
                formatted_content = answer
            with st.chat_message("assistant"):
                st.container()  # Fix ghost message bug.
                st.markdown(formatted_content, unsafe_allow_html=True)
            msg = {
                "role": "assistant",
                "content": answer,
                "sources": local_sources or [],
                "reasoning_content": reasoning_content,
            }
            render_assistant_continuation(msg_idx, message_id, msg)
            # #region agent log
            _debug_log("non_streaming.py:exit_success", "handle_non_streaming_query exit success", hypothesis_id="A")
            # #endregion
        except Exception as e:
            import traceback
            # #region agent log
            _debug_log("non_streaming.py:exit_exception", "handle_non_streaming_query exception", {"exc_type": type(e).__name__}, hypothesis_id="A")
            # #endregion
            status.update(label="❌ 查询失败", state="error")
            st.error(f"❌ 查询失败: {e}")
            st.error(traceback.format_exc())

