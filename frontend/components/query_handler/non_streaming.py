"""
非流式查询处理组件
"""

import streamlit as st
from frontend.utils.sources import convert_sources_to_dict
from frontend.utils.state import save_message_to_history
from frontend.utils.sources import format_answer_with_citation_links
from frontend.components.query_handler.common import display_reasoning, display_sources, save_to_chat_manager
from backend.infrastructure.logger import get_logger

logger = get_logger('app')


def handle_non_streaming_query(rag_service, chat_manager, prompt: str) -> None:
    """处理非流式查询
    
    Args:
        rag_service: RAG服务实例
        chat_manager: 对话管理器实例
        prompt: 用户查询
    """
    # 显示思考中的提示
    with st.chat_message("assistant"):
        with st.spinner("🤔 思考中..."):
            try:
                # 使用RAGService执行查询（新架构）
                response = rag_service.query(
                    question=prompt,
                    user_id=None,
                    session_id=chat_manager.current_session.session_id if chat_manager.current_session else None,
                )
                
                answer = response.answer
                local_sources = convert_sources_to_dict(response.sources)
                reasoning_content = response.metadata.get('reasoning_content')
                
                # 生成消息ID
                from frontend.utils.helpers import generate_message_id
                msg_idx = len(st.session_state.messages)
                message_id = generate_message_id(msg_idx, answer)
                
                # 保存到消息历史
                save_message_to_history(answer, local_sources, reasoning_content)
                
                # 显示观察器信息（在答案前）
                from frontend.components.chat_display import _render_observer_info
                _render_observer_info(msg_idx)
                
                # 立即显示AI回答
                if local_sources:
                    formatted_content = format_answer_with_citation_links(
                        answer,
                        local_sources,
                        message_id=message_id
                    )
                    st.markdown(formatted_content, unsafe_allow_html=True)
                else:
                    st.markdown(answer)
                
                # 显示推理链和引用来源
                display_reasoning(reasoning_content)
                display_sources(local_sources, message_id)
                
                # 保存到ChatManager会话
                save_to_chat_manager(chat_manager, prompt, answer, local_sources, reasoning_content)
                
            except Exception as e:
                import traceback
                st.error(f"❌ 查询失败: {e}")
                st.error(traceback.format_exc())

