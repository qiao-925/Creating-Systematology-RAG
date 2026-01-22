"""
状态管理工具模块
初始化和管理Streamlit会话状态

主要功能：
- init_session_state()：初始化Streamlit会话状态，包括索引管理、对话管理等
- initialize_sources_map()：初始化来源映射
- save_message_to_history()：保存消息到历史
- invalidate_service_cache()：使服务缓存失效
- rebuild_services()：重建 RAGService 和 ChatManager（配置变更时调用）

特性：
- 完整的会话状态初始化
- 单例模式管理服务
- 配置变更时的服务重建
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from frontend.utils.sources import convert_sources_to_dict
from backend.infrastructure.config import config


def init_session_state() -> None:
    """初始化会话状态"""
    # 设置默认collection_name（使用配置中的默认值）
    if 'collection_name' not in st.session_state:
        st.session_state.collection_name = config.CHROMA_COLLECTION_NAME
    
    # 索引和对话管理
    if 'index_manager' not in st.session_state:
        st.session_state.index_manager = None
    
    if 'chat_manager' not in st.session_state:
        st.session_state.chat_manager = None
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'index_built' not in st.session_state:
        st.session_state.index_built = False
    
    if 'hybrid_query_engine' not in st.session_state:
        st.session_state.hybrid_query_engine = None
    
    # GitHub 增量更新相关
    if 'github_sync_manager' not in st.session_state:
        from backend.infrastructure.data_loader.github_sync import GitHubSyncManager
        st.session_state.github_sync_manager = GitHubSyncManager(config.GITHUB_SYNC_STATE_PATH)
    
    if 'github_repos' not in st.session_state:
        # 从同步状态中加载已存在的仓库列表
        st.session_state.github_repos = st.session_state.github_sync_manager.list_repositories()
    
    # 调试模式与可观测性（默认开启）
    if 'debug_mode_enabled' not in st.session_state:
        st.session_state.debug_mode_enabled = True
    
    # 追踪信息默认启用，无需配置
    if 'collect_trace' not in st.session_state:
        st.session_state.collect_trace = True
    
    # RAG服务（新架构）
    if 'rag_service' not in st.session_state:
        st.session_state.rag_service = None
    
    # 启动遮罩：首屏加载完成前为 False，完成后置 True
    if 'boot_ready' not in st.session_state:
        st.session_state.boot_ready = False
    
    # 对话设置（推理链）
    if 'show_reasoning' not in st.session_state:
        st.session_state.show_reasoning = config.DEEPSEEK_ENABLE_REASONING_DISPLAY
    
    if 'store_reasoning' not in st.session_state:
        st.session_state.store_reasoning = config.DEEPSEEK_STORE_REASONING
    
    # Agentic RAG 设置（默认禁用）
    if 'use_agentic_rag' not in st.session_state:
        st.session_state.use_agentic_rag = False
    
    # 服务验证状态缓存（避免每次rerun都验证）
    if 'rag_service_validated' not in st.session_state:
        st.session_state.rag_service_validated = False
    
    if 'index_manager_validated' not in st.session_state:
        st.session_state.index_manager_validated = False
    
    # 强制验证标志（当配置变更时需要重新验证）
    if 'force_validate_services' not in st.session_state:
        st.session_state.force_validate_services = False
    
    # 模型选择状态
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = config.get_default_llm_id()
    
    # LLM 预设（精确/平衡/创意）
    if 'llm_preset' not in st.session_state:
        st.session_state.llm_preset = 'balanced'
    
    # RAG 检索策略
    if 'retrieval_strategy' not in st.session_state:
        st.session_state.retrieval_strategy = config.RETRIEVAL_STRATEGY
    
    # RAG 高级参数
    if 'similarity_top_k' not in st.session_state:
        st.session_state.similarity_top_k = config.SIMILARITY_TOP_K
    
    if 'similarity_threshold' not in st.session_state:
        st.session_state.similarity_threshold = config.SIMILARITY_THRESHOLD
    
    if 'enable_rerank' not in st.session_state:
        st.session_state.enable_rerank = config.ENABLE_RERANK


def initialize_sources_map() -> None:
    """初始化来源映射（从历史消息中提取）"""
    if 'current_sources_map' not in st.session_state:
        st.session_state.current_sources_map = {}
    if 'current_reasoning_map' not in st.session_state:
        st.session_state.current_reasoning_map = {}
    
    current_sources_map = st.session_state.current_sources_map.copy()
    current_reasoning_map = st.session_state.current_reasoning_map.copy()
    
    # 先填充current_sources_map（从历史消息中提取）
    from frontend.utils.helpers import generate_message_id
    for idx, message in enumerate(st.session_state.messages):
        if message["role"] == "assistant":
            message_id = generate_message_id(idx, message)
            if "sources" in message and message["sources"]:
                # 确保sources是字典格式
                sources = message["sources"]
                
                # 统一转换：无论什么格式，都转换为字典列表（确保格式一致）
                if sources:
                    # 检查第一个元素是否是字典
                    if len(sources) > 0:
                        first_item = sources[0]
                        # 如果不是字典，或者有model_dump方法（Pydantic模型），都需要转换
                        if not isinstance(first_item, dict) or hasattr(first_item, 'model_dump'):
                            sources = convert_sources_to_dict(sources)
                            message["sources"] = sources  # 更新消息中的sources
                    
                    current_sources_map[message_id] = sources
                else:
                    current_sources_map[message_id] = []
            else:
                current_sources_map[message_id] = []
                
            # 处理推理链
            if "reasoning_content" in message:
                current_reasoning_map[message_id] = message["reasoning_content"]
    
    # 更新session_state
    st.session_state.current_sources_map = current_sources_map
    st.session_state.current_reasoning_map = current_reasoning_map


def save_message_to_history(answer: str, sources: List[Dict[str, Any]], reasoning_content: Optional[str] = None) -> None:
    """保存消息到历史
    
    Args:
        answer: 回答文本
        sources: 来源列表
        reasoning_content: 推理链内容（可选）
    """
    from frontend.utils.helpers import generate_message_id
    msg_idx = len(st.session_state.messages)
    message_id = generate_message_id(msg_idx, answer)
    
    assistant_msg = {
        "role": "assistant",
        "content": answer,
        "sources": sources
    }
    if reasoning_content:
        assistant_msg["reasoning_content"] = reasoning_content
    
    st.session_state.messages.append(assistant_msg)
    st.session_state.current_sources_map[message_id] = sources
    if reasoning_content:
        st.session_state.current_reasoning_map[message_id] = reasoning_content


def invalidate_service_cache() -> None:
    """使服务缓存失效，下次加载时会重新验证
    
    在以下场景调用：
    - 集合名称变更
    - 配置变更
    - 手动触发验证
    
    注意：此函数主要用于配置变更场景，统一初始化系统的实例
    存储在 init_result.instances 中，不会自动失效。
    如需重新初始化，应重新调用 initialize_app()。
    """
    from backend.infrastructure.logger import get_logger
    logger = get_logger('frontend.services')
    
    st.session_state.rag_service_validated = False
    st.session_state.index_manager_validated = False
    st.session_state.force_validate_services = True
    logger.info("🔄 服务缓存已失效，下次加载时将重新验证")


def rebuild_services() -> bool:
    """重建 RAGService 和 ChatManager
    
    当配置变更时调用，根据当前 session_state 中的配置重建服务实例。
    
    Returns:
        bool: 重建是否成功
    """
    from backend.infrastructure.logger import get_logger
    logger = get_logger('frontend.services')
    
    if 'init_result' not in st.session_state:
        logger.warning("init_result 不存在，无法重建服务")
        return False
    
    init_result = st.session_state.init_result
    index_manager = init_result.instances.get('index_manager')
    
    if index_manager is None:
        # 标记需要重新初始化
        logger.warning("index_manager 不存在，标记需要重新初始化")
        st.session_state.boot_ready = False
        if 'init_result' in st.session_state:
            del st.session_state.init_result
        return False
    
    # 获取当前配置
    from frontend.components.config_panel.models import AppConfig
    app_config = AppConfig.from_session_state()
    
    # 获取 LLM 参数
    temperature = app_config.get_llm_temperature()
    max_tokens = app_config.get_llm_max_tokens()
    
    logger.info(
        f"重建服务: model={app_config.selected_model}, "
        f"preset={app_config.llm_preset}, "
        f"agentic={app_config.use_agentic_rag}, "
        f"temperature={temperature}"
    )
    
    try:
        # 延迟导入避免循环依赖
        from backend.business.rag_api import RAGService
        from backend.business.chat import ChatManager
        
        collection_name = st.session_state.get(
            'collection_name', config.CHROMA_COLLECTION_NAME
        )
        enable_debug = app_config.debug_mode
        
        # 重建 RAGService
        init_result.instances['rag_service'] = RAGService(
            collection_name=collection_name,
            enable_debug=enable_debug,
            enable_markdown_formatting=True,
            use_agentic_rag=app_config.use_agentic_rag,
            model_id=app_config.selected_model,
            retrieval_strategy=app_config.retrieval_strategy,
            similarity_top_k=app_config.similarity_top_k,
            similarity_threshold=app_config.similarity_threshold,
            enable_rerank=app_config.enable_rerank,
        )
        
        # 重建 ChatManager
        init_result.instances['chat_manager'] = ChatManager(
            index_manager=index_manager,
            user_email=None,
            enable_debug=enable_debug,
            enable_markdown_formatting=True,
            use_agentic_rag=app_config.use_agentic_rag,
            model_id=app_config.selected_model,
            retrieval_strategy=app_config.retrieval_strategy,
            similarity_top_k=app_config.similarity_top_k,
            similarity_threshold=app_config.similarity_threshold,
            enable_rerank=app_config.enable_rerank,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        logger.info("✅ 服务重建完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 服务重建失败: {e}", exc_info=True)
        return False

