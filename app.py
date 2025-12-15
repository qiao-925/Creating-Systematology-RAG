"""
Streamlit Web应用 - 主页：系统科学知识库RAG应用的Web界面

主要功能：
- cleanup_resources()：清理应用资源，关闭Chroma客户端和后台线程
- display_trace_info()：显示查询追踪信息
- get_chat_title()：从第一个用户消息中提取标题
- sidebar()：侧边栏，包含新对话按钮、历史会话列表和进入设置入口
- main()：主界面，包含用户认证、对话显示、查询处理等

执行流程：
1. 初始化会话状态和资源
2. 用户认证（登录/注册）
3. 初始化RAG服务和对话管理器
4. 显示对话历史和引用来源
5. 处理用户查询并生成回答

特性：
- Claude风格UI设计
- 支持推理链显示和存储
- 支持引用来源展示
- 支持会话历史管理
- 支持Phoenix可观测性集成（在设置页面配置）
"""

import streamlit as st
from pathlib import Path
from typing import Optional
import sys
import time
import atexit
import logging

# 抑制OpenTelemetry导出器的错误日志（避免连接失败时的噪音）
# 这些错误通常是 transient 的，不影响应用功能
logging.getLogger('opentelemetry.sdk.trace.export').setLevel(logging.WARNING)
logging.getLogger('opentelemetry.exporter.otlp').setLevel(logging.WARNING)
logging.getLogger('opentelemetry.exporter.otlp.proto.grpc').setLevel(logging.WARNING)

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

# 优先设置 UTF-8 编码（确保 emoji 正确显示）
try:
    from src.infrastructure.encoding import setup_utf8_encoding
    setup_utf8_encoding()
except ImportError:
    # 如果 encoding 模块尚未加载，手动设置基础编码
    import os
    os.environ["PYTHONIOENCODING"] = "utf-8"

from src.infrastructure.config import config
from src.ui import (
    init_session_state,
    load_rag_service,
    load_index,
    load_chat_manager,
    display_hybrid_sources,
    display_model_status,
    format_answer_with_citation_links,
    display_sources_with_anchors
)
from src.ui.sources_panel import display_sources_below_message
from src.ui.styles import CLAUDE_STYLE_CSS
from llama_index.core import Document as LlamaDocument
from src.infrastructure.logger import get_logger

logger = get_logger('app')


def convert_sources_to_dict(sources) -> list:
    """将SourceModel对象列表转换为字典列表
    
    Args:
        sources: SourceModel对象列表或字典列表
        
    Returns:
        字典列表
    """
    if not sources:
        return []
    
    result = []
    for idx, source in enumerate(sources):
        if isinstance(source, dict):
            # 已经是字典，添加index字段
            source_dict = source.copy()
            source_dict['index'] = idx + 1
            result.append(source_dict)
        else:
            # 是SourceModel对象，转换为字典
            source_dict = source.model_dump() if hasattr(source, 'model_dump') else dict(source)
            source_dict['index'] = idx + 1
            result.append(source_dict)
    
    return result


def cleanup_resources():
    """清理应用资源，关闭 Chroma 客户端和后台线程
    
    这个函数会在应用退出时被调用，确保 Chroma 的后台线程被正确终止
    """
    try:
        import logging
        log = logging.getLogger('app')
        log.info("🔧 开始清理应用资源...")
        
        # 清理 IndexManager（关闭 Chroma 客户端）
        # 注意：在 Streamlit 中，session_state 可能不可用，所以需要 try-except
        try:
            if hasattr(st, 'session_state') and 'index_manager' in st.session_state:
                index_manager = st.session_state.get('index_manager')
                if index_manager:
                    try:
                        index_manager.close()
                        log.info("✅ 索引管理器已清理")
                    except Exception as e:
                        log.warning(f"⚠️  清理索引管理器时出错: {e}")
        except Exception as e:
            # Streamlit session_state 可能在某些情况下不可用
            log.debug(f"无法访问 session_state: {e}")
        
        # 尝试清理全局资源
        try:
            # 清理全局的 Embedding 模型（如果需要）
            from src.infrastructure.indexer import clear_embedding_model_cache
            clear_embedding_model_cache()
            log.debug("✅ 全局模型缓存已清理")
        except Exception as e:
            log.debug(f"清理全局模型缓存时出错: {e}")
        
        # 清理 Hugging Face Embedding 资源（线程池和正在进行的请求）
        try:
            from src.infrastructure.embeddings.hf_inference_embedding import cleanup_hf_embedding_resources
            cleanup_hf_embedding_resources()
            log.debug("✅ Hugging Face Embedding 资源已清理")
        except Exception as e:
            log.debug(f"清理 Hugging Face Embedding 资源时出错: {e}")
        
        log.info("✅ 应用资源清理完成")
    except Exception as e:
        # 使用 print 作为最后的备选方案
        print(f"❌ 清理资源时发生错误: {e}")


# 注册退出钩子（在所有情况下都会执行）
atexit.register(cleanup_resources)


# 页面配置
st.set_page_config(
    page_title="主页",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def display_trace_info(trace_info: dict):
    """显示查询追踪信息
    
    Args:
        trace_info: 追踪信息字典
    """
    if not trace_info:
        return
    
    with st.expander("📊 查询追踪信息", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("总耗时", f"{trace_info.get('total_time', 0)}s")
        
        with col2:
            retrieval_info = trace_info.get('retrieval', {})
            st.metric("检索耗时", f"{retrieval_info.get('time_cost', 0)}s")
        
        with col3:
            st.metric("召回数量", retrieval_info.get('chunks_retrieved', 0))
        
        st.divider()
        
        # 检索详情
        st.markdown("**🔍 检索详情**")
        col1, col2 = st.columns(2)
        with col1:
            st.text(f"Top K: {retrieval_info.get('top_k', 0)}")
            st.text(f"平均相似度: {retrieval_info.get('avg_score', 0)}")
        
        with col2:
            llm_info = trace_info.get('llm_generation', {})
            st.text(f"LLM模型: {llm_info.get('model', 'N/A')}")
            st.text(f"回答长度: {llm_info.get('response_length', 0)} 字符")


def get_chat_title(messages: list) -> Optional[str]:
    """从第一个用户消息中提取标题
    
    Args:
        messages: 消息列表
        
    Returns:
        标题字符串，如果没有用户消息则返回None
    """
    if not messages:
        return None
    
    # 找到第一个用户消息
    for message in messages:
        if message.get("role") == "user":
            content = message.get("content", "")
            if content:
                # 截取前50个字符作为标题
                title = content[:50].strip()
                # 如果超过50个字符，添加省略号
                if len(content) > 50:
                    title += "..."
                return title
    
    return None


def sidebar():
    """侧边栏 - 精简版，只保留核心功能"""
    with st.sidebar:
        # ========== 应用标题区域 ==========
        st.title("📚 " + config.APP_TITLE)
        st.caption("基于LlamaIndex和DeepSeek的系统科学知识问答系统")
        
        # ========== 新对话（顶部） ==========
        if st.button("💬 开启新对话", type="primary", use_container_width=True, key="new_chat_top"):
            if st.session_state.chat_manager:
                # 创建新会话（只重置对话状态，不重新初始化服务）
                st.session_state.chat_manager.start_session()
                st.session_state.messages = []
                # 清空引用来源映射，避免右侧显示上一个对话的引用来源
                if 'current_sources_map' in st.session_state:
                    st.session_state.current_sources_map = {}
                if 'current_reasoning_map' in st.session_state:
                    st.session_state.current_reasoning_map = {}
                # 仅刷新UI，不触发服务重新验证
                st.rerun()

        # ========== 历史会话（紧随新对话按钮） ==========
        current_session_id = None
        if st.session_state.chat_manager and st.session_state.chat_manager.current_session:
            current_session_id = st.session_state.chat_manager.current_session.session_id
        from src.ui.history import display_session_history
        display_session_history(user_email=None, current_session_id=current_session_id)
        
        # ========== 设置按钮 ==========
        st.divider()
        if st.button("⚙️ 设置", use_container_width=True, key="settings_button"):
            st.session_state.show_settings_dialog = True
        
        # 检查是否需要显示设置弹窗
        if st.session_state.get("show_settings_dialog", False):
            from src.ui.settings_dialog import show_settings_dialog
            show_settings_dialog()
            # 注意：对话框的关闭由装饰器自动处理，不需要手动关闭


def main():
    """主界面"""
    # ========== Claude风格CSS样式 ==========
    st.markdown(CLAUDE_STYLE_CSS, unsafe_allow_html=True)
    
    # 初始化会话状态（需早于重型初始化，用于控制遮罩）
    init_session_state()
    
    # ========== 启动初始化 ==========
    if not st.session_state.boot_ready:
        # 启动阶段：简化初始化流程（延迟加载，不预加载模型）
        # 模型和 Phoenix 将在首次使用时按需加载
        st.session_state.boot_ready = True
        st.rerun()
        return
    
    # 显示侧边栏
    sidebar()
    
    # 初始化RAG服务（新架构推荐）
    rag_service = load_rag_service()
    if not rag_service:
        st.error("❌ RAG服务初始化失败")
        return
    
    # 初始化对话管理器（用于会话管理和历史记录）
    chat_manager = load_chat_manager()
    if not chat_manager:
        st.error("❌ 对话管理器初始化失败")
        return
    
    # 辅助函数：使用RAGService执行查询
    def execute_query_with_rag_service(query: str, user_id: str = None, session_id: str = None):
        """使用RAGService执行查询
        
        Returns:
            tuple: (answer, sources)
                - answer: 回答文本
                - sources: 来源列表
        """
        try:
            # 使用RAGService查询
            response = rag_service.query(
                question=query,
                user_id=user_id,  # 单用户模式，user_id可为None
                session_id=session_id or (chat_manager.current_session.session_id if chat_manager.current_session else None),
            )
            
            return response.answer, convert_sources_to_dict(response.sources)
        except Exception as e:
            logger.error(f"RAGService查询失败: {e}", exc_info=True)
            raise
    
    # ========== 处理历史会话加载 ==========
    if 'load_session_id' in st.session_state and st.session_state.load_session_id:
        from src.business.chat import load_session_from_file
        
        # 加载历史会话
        session_path = st.session_state.load_session_path
        loaded_session = load_session_from_file(session_path)
        
        if loaded_session:
            # 将历史会话设置为当前会话
            chat_manager.current_session = loaded_session
            
            # 将会话历史转换为messages格式
            st.session_state.messages = []
            # 清空引用来源映射，避免显示上一个对话的引用来源
            st.session_state.current_sources_map = {}
            
            for idx, turn in enumerate(loaded_session.history):
                # 用户消息
                st.session_state.messages.append({
                    "role": "user",
                    "content": turn.question
                })
                # AI回复（包含推理链，如果存在）
                assistant_msg = {
                    "role": "assistant",
                    "content": turn.answer,
                    "sources": turn.sources
                }
                # 如果会话历史中包含推理链，添加到消息中
                if hasattr(turn, 'reasoning_content') and turn.reasoning_content:
                    assistant_msg["reasoning_content"] = turn.reasoning_content
                st.session_state.messages.append(assistant_msg)
                
                # 如果有引用来源，存储到current_sources_map
                if turn.sources:
                    message_id = f"msg_{len(st.session_state.messages)-1}_{hash(str(assistant_msg))}"
                    # 确保sources是字典格式并包含index字段
                    converted_sources = convert_sources_to_dict(turn.sources)
                    st.session_state.current_sources_map[message_id] = converted_sources
                    # 同时更新消息中的sources
                    assistant_msg["sources"] = converted_sources
            
            st.success(f"✅ 已加载会话: {loaded_session.title}")
        else:
            st.error("❌ 加载会话失败")
        
        # 清除加载标记
        del st.session_state.load_session_id
        del st.session_state.load_session_path
        st.rerun()
    
    # ========== 显示常驻标题（基于第一个用户问题，居中显示） ==========
    chat_title = get_chat_title(st.session_state.messages)
    if chat_title:
        st.markdown(f"<div style='text-align: center;'><h3>{chat_title}</h3></div>", unsafe_allow_html=True)
        st.markdown("---")
    
    # 存储当前消息的引用来源和推理链（用于右侧显示）
    if 'current_sources_map' not in st.session_state:
        st.session_state.current_sources_map = {}
    if 'current_reasoning_map' not in st.session_state:
        st.session_state.current_reasoning_map = {}
    current_sources_map = st.session_state.current_sources_map.copy()  # 使用副本，避免直接修改
    current_reasoning_map = st.session_state.current_reasoning_map.copy()
    
    # 先填充current_sources_map（从历史消息中提取）
    for idx, message in enumerate(st.session_state.messages):
        if message["role"] == "assistant":
            message_id = f"msg_{idx}_{hash(str(message))}"
            if "sources" in message and message["sources"]:
                # 确保sources是字典格式
                sources = message["sources"]
                logger.debug(f"处理消息 {idx} 的sources: type={type(sources)}, len={len(sources) if sources else 0}")
                
                # 统一转换：无论什么格式，都转换为字典列表（确保格式一致）
                if sources:
                    # 检查第一个元素是否是字典
                    if len(sources) > 0:
                        first_item = sources[0]
                        # 如果不是字典，或者有model_dump方法（Pydantic模型），都需要转换
                        if not isinstance(first_item, dict) or hasattr(first_item, 'model_dump'):
                            logger.debug(f"转换sources: 从 {type(first_item)} 转换为字典")
                            sources = convert_sources_to_dict(sources)
                            message["sources"] = sources  # 更新消息中的sources
                    
                    logger.debug(f"最终sources: len={len(sources)}, 第一个元素类型={type(sources[0]) if sources else 'empty'}")
                    current_sources_map[message_id] = sources
                else:
                    current_sources_map[message_id] = []
            else:
                current_sources_map[message_id] = []
                
            # 处理推理链
            if "reasoning_content" in message:
                current_reasoning_map[message_id] = message["reasoning_content"]
    
    # ========== 主内容区域：统一布局，引用来源显示在消息下方 ==========
    
    # 如果无对话历史，将"快速开始"和输入框整块垂直居中
    if not st.session_state.messages:
        # 使用 flexbox 实现垂直居中
        st.markdown("""
        <style>
        .quick-start-container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 85vh;
            padding: 2rem 0;
        }
        </style>
        <div class="quick-start-container">
        """, unsafe_allow_html=True)
        
        # 使用 columns 实现水平居中（缩小宽度）
        left_spacer, center_col, right_spacer = st.columns([2, 6, 2])
        
        with center_col:
            st.markdown("### 💡 快速开始")
            st.caption("点击下方问题快速体验")
            
            default_questions = [
                "什么是系统科学？它的核心思想是什么？",
                "钱学森对系统科学有哪些贡献？",
                "从定性到定量的综合集成法如何与马克思主义哲学结合起来理解？",
                "系统工程在现代科学中的应用有哪些？"
            ]
            
            # 使用两列布局展示问题按钮
            col1, col2 = st.columns(2)
            for idx, question in enumerate(default_questions):
                col = col1 if idx % 2 == 0 else col2
                with col:
                    if st.button(f"💬 {question}", key=f"default_q_{idx}", use_container_width=True):
                        # 立即将用户消息添加到历史，避免rerun后再次显示"快速开始"
                        st.session_state.messages.append({"role": "user", "content": question})
                        # 将问题设置为用户输入（用于触发查询）
                        st.session_state.selected_question = question
                        st.rerun()
            
            # 在快速开始下方添加输入框（也在居中容器内）
            st.markdown("<br>", unsafe_allow_html=True)  # 添加一些间距
            from src.ui.chat_input import deepseek_style_chat_input
            # 只显示输入框，不在这里处理逻辑（因为一旦有消息，快速开始就会消失）
            prompt = deepseek_style_chat_input("给系统发送消息", key="main_chat_input", fixed=False)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 处理输入框的发送逻辑（在容器外，但只在没有对话历史时执行）
        # 注意：一旦有消息，下次 rerun 时快速开始就不会显示了
        if prompt:
            # 添加用户消息到历史（这会导致快速开始消失）
            st.session_state.messages.append({"role": "user", "content": prompt})
            # 设置待处理的查询，在 rerun 后处理
            st.session_state.pending_query = prompt
            # 立即 rerun，让快速开始消失
            st.rerun()
    
    # 处理待处理的查询（在快速开始消失后）
    if 'pending_query' in st.session_state and st.session_state.pending_query:
        prompt = st.session_state.pending_query
        del st.session_state.pending_query  # 清除待处理标记
        
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
                    msg_idx = len(st.session_state.messages)
                    message_id = f"msg_{msg_idx}_{hash(str(answer))}"
                    
                    # 保存到消息历史
                    if answer:
                        assistant_msg = {
                            "role": "assistant",
                            "content": answer,
                            "sources": local_sources
                        }
                        if reasoning_content:
                            assistant_msg["reasoning_content"] = reasoning_content
                        st.session_state.messages.append(assistant_msg)
                    
                    # 存储引用来源
                    current_sources_map[message_id] = local_sources
                    if reasoning_content:
                        current_reasoning_map[message_id] = reasoning_content
                    
                    # 立即显示AI回答
                    if "sources" in assistant_msg and assistant_msg["sources"]:
                        formatted_content = format_answer_with_citation_links(
                            answer,
                            assistant_msg["sources"],
                            message_id=message_id
                        )
                        st.markdown(formatted_content, unsafe_allow_html=True)
                    else:
                        st.markdown(answer)
                    
                    # 显示推理链
                    if reasoning_content:
                        with st.expander("🧠 推理过程", expanded=False):
                            st.markdown(f"```\n{reasoning_content}\n```")
                    
                    # 显示引用来源
                    if local_sources:
                        st.markdown("#### 📚 引用来源")
                        display_sources_below_message(local_sources, message_id=message_id)
                    
                    # 保存到ChatManager会话
                    if chat_manager and answer:
                        if not chat_manager.current_session:
                            chat_manager.start_session()
                        if reasoning_content:
                            chat_manager.current_session.add_turn(prompt, answer, local_sources, reasoning_content)
                        else:
                            chat_manager.current_session.add_turn(prompt, answer, local_sources)
                        if chat_manager.auto_save:
                            chat_manager.save_current_session()
                    
                    # 更新session_state
                    st.session_state.current_sources_map = current_sources_map
                    st.session_state.current_reasoning_map = current_reasoning_map
                    
                except Exception as e:
                    import traceback
                    st.error(f"❌ 查询失败: {e}")
                    st.error(traceback.format_exc())
    
    # 如果有对话历史，使用居中布局
    if st.session_state.messages:
        # 使用 columns 实现水平居中（缩小宽度）
        left_spacer, center_col, right_spacer = st.columns([2, 6, 2])
        
        with center_col:
            # 显示对话历史
            for idx, message in enumerate(st.session_state.messages):
                message_id = f"msg_{idx}_{hash(str(message))}"
                with st.chat_message(message["role"]):
                    # 如果是AI回答且包含引用，使用带链接的格式
                    if message["role"] == "assistant" and "sources" in message and message["sources"]:
                        formatted_content = format_answer_with_citation_links(
                            message["content"],
                            message["sources"],
                            message_id=message_id
                        )
                        st.markdown(formatted_content, unsafe_allow_html=True)
                    else:
                        st.markdown(message["content"])
                    
                    # 显示推理链（始终显示，如果存在）
                    if message["role"] == "assistant":
                        reasoning_content = message.get("reasoning_content")
                        # 调试：检查推理链是否存在
                        if reasoning_content:
                            with st.expander("🧠 推理过程", expanded=False):
                                st.markdown(f"```\n{reasoning_content}\n```")
                        else:
                            # 调试：显示为什么没有推理链
                            if config.DEEPSEEK_ENABLE_REASONING_DISPLAY:
                                # 只在启用显示时才显示调试信息
                                logger.debug(f"消息 {message_id} 没有推理链内容")
                
                # 在消息下方显示引用来源（如果有）
                if message["role"] == "assistant":
                    sources = current_sources_map.get(message_id, [])
                    if sources:
                        # 显示引用来源标题
                        st.markdown("#### 📚 引用来源")
                        # 显示引用来源详情
                        display_sources_below_message(sources, message_id=message_id)
                
                # 更新session_state中的映射（确保同步）
                st.session_state.current_sources_map = current_sources_map
                st.session_state.current_reasoning_map = current_reasoning_map
            
            # 处理默认问题的点击（在显示消息循环之后，避免重复显示）
            if 'selected_question' in st.session_state and st.session_state.selected_question:
                prompt = st.session_state.selected_question
                st.session_state.selected_question = None  # 清除状态
                
                # 注意：用户消息已经在点击按钮时添加到历史了，这里只需要处理查询
                # 显示思考中的提示（使用chat_message样式）
                with st.chat_message("assistant"):
                        with st.spinner("🤔 思考中..."):
                            try:
                                # 使用RAGService执行查询（新架构）
                                response = rag_service.query(
                                    question=prompt,
                                    user_id=None,  # 单用户模式，不需要用户标识
                                    session_id=chat_manager.current_session.session_id if chat_manager.current_session else None,
                                )
                                
                                answer = response.answer
                                local_sources = convert_sources_to_dict(response.sources)
                                reasoning_content = response.metadata.get('reasoning_content')
                                
                                # 生成消息ID
                                msg_idx = len(st.session_state.messages)
                                message_id = f"msg_{msg_idx}_{hash(str(answer))}"
                                
                                # 保存到消息历史（UI显示用，包含推理链）
                                if answer:  # 只在有答案时保存
                                    assistant_msg = {
                                        "role": "assistant",
                                        "content": answer,
                                        "sources": local_sources
                                    }
                                    if reasoning_content:
                                        assistant_msg["reasoning_content"] = reasoning_content
                                    st.session_state.messages.append(assistant_msg)
                                
                                # 存储引用来源
                                current_sources_map[message_id] = local_sources
                                if reasoning_content:
                                    current_reasoning_map[message_id] = reasoning_content
                                
                                # 立即显示AI回答（避免白屏）
                                if "sources" in assistant_msg and assistant_msg["sources"]:
                                    formatted_content = format_answer_with_citation_links(
                                        answer,
                                        assistant_msg["sources"],
                                        message_id=message_id
                                    )
                                    st.markdown(formatted_content, unsafe_allow_html=True)
                                else:
                                    st.markdown(answer)
                                
                                # 显示推理链（如果存在）
                                if reasoning_content:
                                    with st.expander("🧠 推理过程", expanded=False):
                                        st.markdown(f"```\n{reasoning_content}\n```")
                                
                                # 显示引用来源（如果有）
                                if local_sources:
                                    st.markdown("#### 📚 引用来源")
                                    display_sources_below_message(local_sources, message_id=message_id)
                                
                                # 同时保存到ChatManager会话（持久化）
                                if chat_manager and answer:
                                    # 如果没有当前会话，先创建一个
                                    if not chat_manager.current_session:
                                        chat_manager.start_session()
                                    # 保存对话（始终存储推理链，如果存在）
                                    if reasoning_content:
                                        chat_manager.current_session.add_turn(prompt, answer, local_sources, reasoning_content)
                                    else:
                                        chat_manager.current_session.add_turn(prompt, answer, local_sources)
                                    # 自动保存
                                    if chat_manager.auto_save:
                                        chat_manager.save_current_session()
                                
                                # 更新session_state
                                st.session_state.current_sources_map = current_sources_map
                                st.session_state.current_reasoning_map = current_reasoning_map
                                
                                # 清除思考中标志
                                st.session_state.is_thinking = False
                            
                            except Exception as e:
                                import traceback
                                st.error(f"❌ 查询失败: {e}")
                                st.error(traceback.format_exc())
                                # 即使出错也要清除思考中标志
                                st.session_state.is_thinking = False
    
    # 处理用户输入后的查询（在显示消息循环之后）
    if 'user_input_prompt' in st.session_state and st.session_state.user_input_prompt:
        message_id = f"msg_{idx}_{hash(str(message))}"
        with st.chat_message(message["role"]):
            # 如果是AI回答且包含引用，使用带链接的格式
            if message["role"] == "assistant" and "sources" in message and message["sources"]:
                formatted_content = format_answer_with_citation_links(
                    message["content"],
                    message["sources"],
                    message_id=message_id
                )
                st.markdown(formatted_content, unsafe_allow_html=True)
            else:
                st.markdown(message["content"])
            
            # 显示推理链（始终显示，如果存在）
            if message["role"] == "assistant":
                reasoning_content = message.get("reasoning_content")
                # 调试：检查推理链是否存在
                if reasoning_content:
                    with st.expander("🧠 推理过程", expanded=False):
                        st.markdown(f"```\n{reasoning_content}\n```")
                else:
                    # 调试：显示为什么没有推理链
                    if config.DEEPSEEK_ENABLE_REASONING_DISPLAY:
                        # 只在启用显示时才显示调试信息
                        logger.debug(f"消息 {message_id} 没有推理链内容")
        
        # 在消息下方显示引用来源（如果有）
        if message["role"] == "assistant":
            sources = current_sources_map.get(message_id, [])
            if sources:
                # 显示引用来源标题
                st.markdown("#### 📚 引用来源")
                # 显示引用来源详情
                display_sources_below_message(sources, message_id=message_id)
        
        # 更新session_state中的映射（确保同步）
        st.session_state.current_sources_map = current_sources_map
        st.session_state.current_reasoning_map = current_reasoning_map
    
    # 用户输入（Material Design风格，多行输入 + 自动高度调整 + 键盘快捷键 + 字符计数）
    # 注意：如果没有对话历史，输入框已经在快速开始容器内了，这里只处理有对话历史的情况
    if st.session_state.messages:
        from src.ui.chat_input import deepseek_style_chat_input
        # 检查是否正在思考中
        is_thinking = st.session_state.get('is_thinking', False)
        # 有对话历史时，输入框固定在底部
        prompt = deepseek_style_chat_input("给系统发送消息", key="main_chat_input", fixed=True)
    else:
        # 如果没有对话历史，输入框已经在快速开始容器内处理了
        prompt = None
    
    # 处理有对话历史时的用户输入
    if prompt and st.session_state.messages:
        # 设置思考中标志
        st.session_state.is_thinking = True
        # 立即显示用户消息（避免白屏）- 在居中布局内
        if st.session_state.messages:
            # 如果有对话历史，在居中布局内显示
            left_spacer, center_col, right_spacer = st.columns([2, 6, 2])
            with center_col:
                with st.chat_message("user"):
                    st.markdown(prompt)
        else:
            # 如果没有对话历史，直接显示
            with st.chat_message("user"):
                st.markdown(prompt)
        
        # 添加用户消息到历史
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # 显示思考中的提示（使用chat_message样式，与默认问题一致）- 在居中布局内
        if st.session_state.messages:
            left_spacer, center_col, right_spacer = st.columns([2, 6, 2])
            with center_col:
                with st.chat_message("assistant"):
                    # 创建消息占位符用于流式更新
                    message_placeholder = st.empty()
                    
                    try:
                        # 使用流式对话API
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
                                    message_placeholder.markdown(full_answer)
                                elif chunk['type'] == 'error':
                                    st.error(f"❌ 流式对话失败: {chunk['data'].get('message', 'Unknown error')}")
                                    return
                        
                        # 运行异步流式处理
                        import asyncio
                        asyncio.run(process_stream())
                        
                        # 生成消息ID
                        msg_idx = len(st.session_state.messages)
                        message_id = f"msg_{msg_idx}_{hash(str(full_answer))}"
                        
                        # 转换引用来源格式
                        local_sources = convert_sources_to_dict(local_sources)
                        
                        # 调试：检查推理链提取情况
                        logger.info(f"🔍 推理链提取检查: reasoning_content={reasoning_content is not None}, 长度={len(reasoning_content) if reasoning_content else 0}")
                        if reasoning_content:
                            logger.info(f"✅ 推理链内容预览（前100字符）: {reasoning_content[:100]}...")
                        else:
                            logger.warning("⚠️ 响应中没有推理链内容，检查：1) 是否使用 deepseek-reasoner 模型 2) API 是否返回了推理链")
                        
                        # 保存到消息历史（UI显示用，包含推理链）
                        if full_answer:  # 只在有答案时保存
                            assistant_msg = {
                                "role": "assistant",
                                "content": full_answer,
                                "sources": local_sources
                            }
                            if reasoning_content:
                                assistant_msg["reasoning_content"] = reasoning_content
                            st.session_state.messages.append(assistant_msg)
                        
                        # 存储引用来源
                        current_sources_map[message_id] = local_sources
                        if reasoning_content:
                            current_reasoning_map[message_id] = reasoning_content
                        
                        # 显示带引用的格式化内容（如果有来源）
                        if local_sources:
                            formatted_content = format_answer_with_citation_links(
                                full_answer,
                                local_sources,
                                message_id=message_id
                            )
                            message_placeholder.markdown(formatted_content, unsafe_allow_html=True)
                        
                        # 显示推理链（如果存在）
                        if reasoning_content:
                            with st.expander("🧠 推理过程", expanded=False):
                                st.markdown(f"```\n{reasoning_content}\n```")
                        
                        # 显示引用来源（如果有）
                        if local_sources:
                            st.markdown("#### 📚 引用来源")
                            display_sources_below_message(local_sources, message_id=message_id)
                        
                        # 同时保存到ChatManager会话（持久化）
                        if chat_manager and full_answer:
                            if not chat_manager.current_session:
                                chat_manager.start_session()
                            # 保存对话（始终存储推理链，如果存在）
                            if reasoning_content:
                                chat_manager.current_session.add_turn(prompt, full_answer, local_sources, reasoning_content)
                            else:
                                chat_manager.current_session.add_turn(prompt, full_answer, local_sources)
                            if chat_manager.auto_save:
                                chat_manager.save_current_session()
                        
                        # 更新session_state
                        st.session_state.current_sources_map = current_sources_map
                        st.session_state.current_reasoning_map = current_reasoning_map
                        
                        # 清除思考中标志
                        st.session_state.is_thinking = False
                        
                    except Exception as e:
                        import traceback
                        st.error(f"❌ 查询失败: {e}")
                        st.error(traceback.format_exc())
                        # 即使出错也要清除思考中标志
                        st.session_state.is_thinking = False
        else:
            # 如果没有对话历史，直接显示
            # 设置思考中标志
            st.session_state.is_thinking = True
            with st.chat_message("assistant"):
                # 创建消息占位符用于流式更新
                message_placeholder = st.empty()
                
                try:
                    # 使用流式对话API
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
                                message_placeholder.markdown(full_answer)
                            elif chunk['type'] == 'error':
                                st.error(f"❌ 流式对话失败: {chunk['data'].get('message', 'Unknown error')}")
                                return
                    
                    # 运行异步流式处理
                    import asyncio
                    asyncio.run(process_stream())
                    
                    # 生成消息ID
                    msg_idx = len(st.session_state.messages)
                    message_id = f"msg_{msg_idx}_{hash(str(full_answer))}"
                    
                    # 转换引用来源格式
                    local_sources = convert_sources_to_dict(local_sources)
                    
                    # 调试：检查推理链提取情况
                    logger.info(f"🔍 推理链提取检查: reasoning_content={reasoning_content is not None}, 长度={len(reasoning_content) if reasoning_content else 0}")
                    if reasoning_content:
                        logger.info(f"✅ 推理链内容预览（前100字符）: {reasoning_content[:100]}...")
                    else:
                        logger.warning("⚠️ 响应中没有推理链内容，检查：1) 是否使用 deepseek-reasoner 模型 2) API 是否返回了推理链")
                    
                    # 保存到消息历史（UI显示用，包含推理链）
                    if full_answer:  # 只在有答案时保存
                        assistant_msg = {
                            "role": "assistant",
                            "content": full_answer,
                            "sources": local_sources
                        }
                        if reasoning_content:
                            assistant_msg["reasoning_content"] = reasoning_content
                        st.session_state.messages.append(assistant_msg)
                    
                    # 存储引用来源
                    current_sources_map[message_id] = local_sources
                    if reasoning_content:
                        current_reasoning_map[message_id] = reasoning_content
                    
                    # 显示带引用的格式化内容（如果有来源）
                    if local_sources:
                        formatted_content = format_answer_with_citation_links(
                            full_answer,
                            local_sources,
                            message_id=message_id
                        )
                        message_placeholder.markdown(formatted_content, unsafe_allow_html=True)
                    
                    # 显示推理链（如果存在）
                    if reasoning_content:
                        with st.expander("🧠 推理过程", expanded=False):
                            st.markdown(f"```\n{reasoning_content}\n```")
                    
                    # 显示引用来源（如果有）
                    if local_sources:
                        st.markdown("#### 📚 引用来源")
                        display_sources_below_message(local_sources, message_id=message_id)
                    
                    # 同时保存到ChatManager会话（持久化）
                    if chat_manager and full_answer:
                        if not chat_manager.current_session:
                            chat_manager.start_session()
                        # 保存对话（始终存储推理链，如果存在）
                        if reasoning_content:
                            chat_manager.current_session.add_turn(prompt, full_answer, local_sources, reasoning_content)
                        else:
                            chat_manager.current_session.add_turn(prompt, full_answer, local_sources)
                        if chat_manager.auto_save:
                            chat_manager.save_current_session()
                    
                    # 更新session_state
                    st.session_state.current_sources_map = current_sources_map
                    st.session_state.current_reasoning_map = current_reasoning_map
                    
                    # 清除思考中标志
                    st.session_state.is_thinking = False
                    
                except Exception as e:
                    import traceback
                    st.error(f"❌ 查询失败: {e}")
                    st.error(traceback.format_exc())
                    # 即使出错也要清除思考中标志
                    st.session_state.is_thinking = False


if __name__ == "__main__":
    main()

