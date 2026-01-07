"""
流式查询处理组件
"""

import streamlit as st
import asyncio
from typing import Optional
from frontend.utils.sources import convert_sources_to_dict
from frontend.utils.state import save_message_to_history
from frontend.utils.sources import format_answer_with_citation_links
from frontend.components.query_handler.common import display_reasoning, display_sources, save_to_chat_manager
from backend.infrastructure.logger import get_logger

logger = get_logger('app')


def handle_streaming_query(chat_manager, prompt: str) -> None:
    """处理流式查询
    
    Args:
        chat_manager: 对话管理器实例
        prompt: 用户查询
    """
    with st.chat_message("assistant"):
            # 创建消息占位符用于流式更新
            message_placeholder = st.empty()
            
            try:
                full_answer = ""
                local_sources = []
                reasoning_content = None
                
                # 异步流式处理
                async def process_stream():
                    nonlocal full_answer, local_sources, reasoning_content
                    async for chunk in chat_manager.stream_chat(prompt):
                        if chunk['type'] == 'token':
                            full_answer += chunk['data']
                            # 实时更新显示（带光标效果）
                            message_placeholder.markdown(full_answer + "▌")
                        elif chunk['type'] == 'sources':
                            local_sources = chunk['data']
                        elif chunk['type'] == 'reasoning':
                            reasoning_content = chunk['data']
                        elif chunk['type'] == 'done':
                            # 流式完成，移除光标
                            if 'answer' in chunk['data']:
                                full_answer = chunk['data']['answer']
                            if 'sources' in chunk['data']:
                                local_sources = chunk['data']['sources']
                            if 'reasoning_content' in chunk['data']:
                                reasoning_content = chunk['data']['reasoning_content']
                            message_placeholder.markdown(full_answer)
                        elif chunk['type'] == 'error':
                            st.error(f"❌ 流式对话失败: {chunk['data'].get('message', 'Unknown error')}")
                            return
                
                # 运行异步流式处理
                _run_async_stream(process_stream)
                
                # 转换引用来源格式
                local_sources = convert_sources_to_dict(local_sources)
                
                # 调试：检查推理链提取情况
                logger.info(f"🔍 推理链提取检查: reasoning_content={reasoning_content is not None}, 长度={len(reasoning_content) if reasoning_content else 0}")
                if reasoning_content:
                    logger.info(f"✅ 推理链内容预览（前100字符）: {reasoning_content[:100]}...")
                else:
                    logger.warning("⚠️ 响应中没有推理链内容，检查：1) 是否使用 deepseek-reasoner 模型 2) API 是否返回了推理链")
                
                # 保存到消息历史
                if full_answer:
                    save_message_to_history(full_answer, local_sources, reasoning_content)
                
                # 显示带引用的格式化内容（如果有来源）
                from frontend.utils.helpers import generate_message_id
                msg_idx = len(st.session_state.messages)
                message_id = generate_message_id(msg_idx, full_answer)
                
                if local_sources:
                    formatted_content = format_answer_with_citation_links(
                        full_answer,
                        local_sources,
                        message_id=message_id
                    )
                    message_placeholder.markdown(formatted_content, unsafe_allow_html=True)
                
                # 显示推理链和引用来源
                display_reasoning(reasoning_content)
                display_sources(local_sources, message_id)
                
                # 保存到ChatManager会话
                save_to_chat_manager(chat_manager, prompt, full_answer, local_sources, reasoning_content)
                
            except Exception as e:
                import traceback
                st.error(f"❌ 查询失败: {e}")
                st.error(traceback.format_exc())
            finally:
                st.session_state.is_thinking = False


def _run_async_stream(coro) -> None:
    """运行异步流式处理（处理事件循环冲突）
    
    Args:
        coro: 协程函数
    """
    try:
        # 尝试使用 nest_asyncio（如果已安装）
        import nest_asyncio
        nest_asyncio.apply()
        # 使用当前事件循环
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环正在运行，创建任务
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro())
                future.result()
        else:
            asyncio.run(coro())
    except ImportError:
        # 如果没有 nest_asyncio，直接运行
        asyncio.run(coro())
    except RuntimeError:
        # 如果事件循环已存在，创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro())
        finally:
            loop.close()

