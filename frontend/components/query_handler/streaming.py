"""
娴佸紡鏌ヨ澶勭悊缁勪欢
鍩轰簬 rag_service.stream_chat 瀹炵幇 st.write_stream 娴佸紡杈撳嚭
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import streamlit as st

from backend.infrastructure.logger import get_logger
from frontend.utils.sources import convert_sources_to_dict
from frontend.utils.state import save_message_to_history
from frontend.components.query_handler.common import save_to_chat_manager
from frontend.components.chat_display import render_assistant_continuation

logger = get_logger('app')


def _debug_log(location: str, message: str, data: dict | None = None, hypothesis_id: str = "S") -> None:
    # #region agent log
    try:
        log_path = Path(__file__).resolve().parent.parent.parent.parent / ".cursor" / "debug.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": hypothesis_id, "location": location, "message": message, "data": data or {}, "timestamp": __import__("time").time() * 1000}, ensure_ascii=False) + "\n")
    except Exception:  # noqa: S110
        pass
    # #endregion


def _iter_async_stream(async_iter: Any) -> Iterable[Dict[str, Any]]:
    """同步迭代 async generator，避免在 Streamlit 中直接 await。"""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        while True:
            try:
                chunk = loop.run_until_complete(async_iter.__anext__())
            except StopAsyncIteration:
                break
            yield chunk
    finally:
        try:
            loop.run_until_complete(async_iter.aclose())
        except Exception:
            pass
        loop.close()
        asyncio.set_event_loop(None)


def _stream_answer_tokens(rag_service, prompt: str, session_id: Optional[str], stream_state: dict) -> Iterable[str]:
    """把 stream_chat 事件流转换为文本 token 迭代器，供 st.write_stream 使用。"""
    async_iter = rag_service.stream_chat(prompt, session_id=session_id)
    token_count = 0

    for chunk in _iter_async_stream(async_iter):
        if not isinstance(chunk, dict):
            continue
        chunk_type = chunk.get("type")
        if chunk_type == "token":
            text = chunk.get("data") or ""
            if text:
                stream_state["parts"].append(text)
                token_count += 1
                yield text
        elif chunk_type == "sources":
            stream_state["sources"] = chunk.get("data") or []
        elif chunk_type == "reasoning":
            stream_state["reasoning"] = chunk.get("data")
        elif chunk_type == "done":
            data = chunk.get("data") or {}
            if "answer" in data:
                stream_state["final_answer"] = data.get("answer")
            if "sources" in data:
                stream_state["sources"] = data.get("sources")
            if "reasoning_content" in data:
                stream_state["reasoning"] = data.get("reasoning_content")
            if token_count == 0 and stream_state.get("final_answer"):
                # 若无 token 但 done 中有答案，至少输出一次
                yield stream_state["final_answer"]
        elif chunk_type == "error":
            message = (chunk.get("data") or {}).get("message", "Unknown error")
            stream_state["error"] = message
            raise RuntimeError(message)


def handle_streaming_query(rag_service, chat_manager, prompt: str) -> bool:
    """处理流式查询（st.write_stream 实时输出）。
    Returns:
        bool: 是否成功完成流式输出
    """
    _debug_log("streaming.py:entry", "handle_streaming_query entry", {"prompt_len": len(prompt)})
    if not rag_service or not hasattr(rag_service, "stream_chat"):
        st.error("当前服务不支持流式输出")
        _debug_log("streaming.py:unsupported", "rag_service has no stream_chat", hypothesis_id="S")
        return False

    session_id = None
    if chat_manager and chat_manager.current_session:
        session_id = chat_manager.current_session.session_id

    stream_state = {
        "parts": [],
        "sources": [],
        "reasoning": None,
        "final_answer": None,
        "error": None,
    }

    try:
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                if hasattr(st, "write_stream"):
                    st.write_stream(_stream_answer_tokens(rag_service, prompt, session_id, stream_state))
                else:
                    # 兼容旧版本：手动累加 token 输出
                    placeholder = st.empty()
                    buffer = ""
                    for token in _stream_answer_tokens(rag_service, prompt, session_id, stream_state):
                        buffer += token
                        placeholder.markdown(buffer)

        answer = stream_state.get("final_answer") or "".join(stream_state["parts"]).strip()
        sources = convert_sources_to_dict(stream_state.get("sources") or [])
        reasoning_content = stream_state.get("reasoning")

        # 兜底：后端无输出时给出提示，避免界面空白
        if not answer and not stream_state.get("error"):
            answer = "❗ 未收到模型输出，请稍后重试或检查后端日志。"
            sources = []

        if answer:
            from frontend.utils.helpers import generate_message_id
            msg_idx = len(st.session_state.messages)
            message_id = generate_message_id(msg_idx, answer)
            save_message_to_history(answer, sources, reasoning_content)
            save_to_chat_manager(chat_manager, prompt, answer, sources, reasoning_content)
            msg = {
                "role": "assistant",
                "content": answer,
                "sources": sources or [],
                "reasoning_content": reasoning_content,
            }
            render_assistant_continuation(msg_idx, message_id, msg)
        _debug_log("streaming.py:exit_success", "handle_streaming_query exit success", hypothesis_id="S")
        return True
    except Exception as e:
        import traceback
        _debug_log("streaming.py:exit_exception", "handle_streaming_query exception", {"exc_type": type(e).__name__}, hypothesis_id="S")
        # 显式回显错误，避免下一轮 rerun 后上下文空白
        error_msg = f"查询失败: {e}"
        st.error(error_msg)
        st.error(traceback.format_exc())
        st.session_state.messages.append({"role": "assistant", "content": f"❗ {error_msg}"})
        return False
