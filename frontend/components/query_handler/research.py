"""
研究模式查询处理：调用 rag_service.research() 并渲染结构化结果

核心职责：
- handle_research_query()：调用研究内核，渲染 ResearchOutput 到聊天界面

不负责：研究内核实现、路由分派、普通聊天流
"""

import streamlit as st

from backend.infrastructure.logger import get_logger
from frontend.config import ASSISTANT_AVATAR
from frontend.utils.state import save_message_to_history
from frontend.components.query_handler.common import save_to_chat_manager
from frontend.components.research_display import render_research_output

logger = get_logger("frontend.research")


def handle_research_query(rag_service, prompt: str, chat_manager=None) -> bool:
    """处理研究模式查询

    Args:
        rag_service: RAGService 实例（需有 research() 方法）
        prompt: 用户问题
        chat_manager: 对话管理器实例（可选，用于持久化）

    Returns:
        bool: 是否成功完成
    """
    if not rag_service or not hasattr(rag_service, "research"):
        st.error("当前服务不支持研究模式")
        return False

    try:
        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
            st.markdown(
                "<span class='chat-role-assistant-marker'>System:</span>",
                unsafe_allow_html=True,
            )
            with st.spinner("深度研究中…（取证→综合→判断）"):
                output = rag_service.research(prompt)

            formatted = render_research_output(output)
            st.markdown(formatted, unsafe_allow_html=True)

        save_message_to_history(formatted, sources=[], reasoning_content=None)
        save_to_chat_manager(chat_manager, prompt, formatted, sources=[], reasoning_content=None)

        logger.info(
            "研究查询完成",
            question=prompt[:60],
            confidence=output.confidence.value,
            evidence_count=len(output.evidence),
            turns_used=output.turns_used,
        )
        return True

    except Exception as exc:
        import traceback
        error_msg = f"研究查询失败: {exc}"
        st.error(error_msg)
        st.error(traceback.format_exc())
        st.session_state.messages.append(
            {"role": "assistant", "content": f"❗ {error_msg}"}
        )
        logger.error("研究查询异常", error=str(exc))
        return False
