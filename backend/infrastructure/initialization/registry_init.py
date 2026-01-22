"""
初始化注册表：初始化函数

主要功能：
- 提供各模块的初始化函数，用于创建和配置模块实例
"""

import streamlit as st
from typing import Any

from backend.infrastructure.initialization.manager import InitializationManager, InitStatus
from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger('initialization_registry')


def init_encoding(manager: InitializationManager) -> bool:
    """初始化编码设置"""
    try:
        from backend.infrastructure.encoding import setup_utf8_encoding
        result = setup_utf8_encoding()
        return result
    except ImportError:
        import os
        os.environ["PYTHONIOENCODING"] = "utf-8"
        return True
    except Exception as e:
        logger.error(f"编码设置失败: {e}")
        raise


def init_config(manager: InitializationManager) -> Any:
    """初始化配置系统"""
    from backend.infrastructure.config import config
    return config


def init_logger(manager: InitializationManager) -> Any:
    """初始化日志系统"""
    from backend.infrastructure.logger import get_logger
    test_logger = get_logger('initialization_test')
    return test_logger


def init_embedding(manager: InitializationManager) -> Any:
    """初始化Embedding模型并验证连接"""
    from backend.infrastructure.embeddings.factory import create_embedding, get_embedding_instance
    
    cached_instance = get_embedding_instance()
    if cached_instance is not None:
        logger.info(f"使用工厂函数缓存的 Embedding 实例: {type(cached_instance).__name__}")
        try:
            test_embedding = cached_instance.get_query_embedding("test")
            embed_dim = len(test_embedding)
            logger.info(f"✅ Embedding 连接验证成功（维度: {embed_dim}）")
            cached_instance._cached_embed_dim = embed_dim
        except Exception as e:
            logger.warning(f"⚠️  缓存的 Embedding 实例连接验证失败: {e}，将重新创建")
            cached_instance = None
    
    if cached_instance is None:
        embedding_instance = create_embedding()
        
        try:
            test_embedding = embedding_instance.get_query_embedding("test")
            embed_dim = len(test_embedding)
            logger.info(f"✅ Embedding 连接验证成功（维度: {embed_dim}）")
            embedding_instance._cached_embed_dim = embed_dim
        except Exception as e:
            logger.error(f"❌ Embedding 连接验证失败: {e}")
            raise RuntimeError(f"Embedding 模型连接失败: {e}") from e
    else:
        embedding_instance = cached_instance
    
    if hasattr(st, 'session_state'):
        st.session_state.embed_model = embedding_instance
        st.session_state.embed_model_loaded = True
    
    logger.info(f"Embedding 实例创建成功: {type(embedding_instance).__name__}")
    return embedding_instance


def init_index_manager(manager: InitializationManager) -> Any:
    """初始化索引管理器（延迟加载）"""
    from backend.infrastructure.indexer import IndexManager
    from backend.infrastructure.initialization.registry_init import init_embedding
    
    if hasattr(st, 'session_state'):
        if 'index_manager' in st.session_state and st.session_state.index_manager is not None:
            logger.info("使用 session_state 中已有的 IndexManager")
            return st.session_state.index_manager
    
    embedding = manager.instances.get('embedding')
    if embedding is None:
        logger.info("Embedding 未初始化，自动初始化（延迟加载）")
        try:
            embedding = init_embedding(manager)
            manager.instances['embedding'] = embedding
            if 'embedding' in manager.modules:
                manager.modules['embedding'].status = InitStatus.SUCCESS
        except Exception as e:
            logger.error(f"延迟加载 Embedding 失败: {e}")
            raise ValueError(f"Embedding 实例初始化失败: {e}") from e
    
    collection_name = config.CHROMA_COLLECTION_NAME
    if hasattr(st, 'session_state') and 'collection_name' in st.session_state:
        collection_name = st.session_state.collection_name
    
    index_manager = IndexManager(
        collection_name=collection_name,
        embedding_instance=embedding
    )
    
    if hasattr(st, 'session_state'):
        st.session_state.index_manager = index_manager
        st.session_state.index_manager_validated = True
    
    return index_manager


def init_llm_factory(manager: InitializationManager) -> Any:
    """初始化LLM工厂"""
    from backend.infrastructure.llms.factory import create_deepseek_llm_for_query
    
    if not config.DEEPSEEK_API_KEY:
        raise ValueError("未设置 DEEPSEEK_API_KEY")
    
    llm = create_deepseek_llm_for_query(
        api_key=config.DEEPSEEK_API_KEY,
        model=config.LLM_MODEL,
    )
    
    return llm


def init_session_state(manager: InitializationManager) -> None:
    """初始化会话状态"""
    from frontend.utils.state import init_session_state
    
    init_session_state()
    
    if hasattr(st, 'session_state'):
        if 'github_sync_manager' in st.session_state and st.session_state.github_sync_manager is not None:
            try:
                repos = st.session_state.github_sync_manager.list_repositories()
                logger.info(f"✅ GitHub 同步管理器初始化成功（已管理 {len(repos)} 个仓库）")
            except Exception as e:
                logger.warning(f"⚠️  GitHub 同步管理器验证失败: {e}")
        else:
            logger.warning("⚠️  GitHub 同步管理器未在 session_state 中找到")
    
    return None


def init_rag_service(manager: InitializationManager) -> Any:
    """初始化RAG服务（延迟加载）"""
    from backend.business.rag_api import RAGService
    
    if hasattr(st, 'session_state'):
        if 'rag_service' in st.session_state and st.session_state.rag_service is not None:
            logger.info("使用 session_state 中已有的 RAGService")
            return st.session_state.rag_service
    
    collection_name = config.CHROMA_COLLECTION_NAME
    if hasattr(st, 'session_state') and 'collection_name' in st.session_state:
        collection_name = st.session_state.collection_name
    
    enable_debug = False
    if hasattr(st, 'session_state') and 'debug_mode_enabled' in st.session_state:
        enable_debug = st.session_state.debug_mode_enabled
    
    use_agentic_rag = False
    if hasattr(st, 'session_state') and 'use_agentic_rag' in st.session_state:
        use_agentic_rag = st.session_state.use_agentic_rag
    
    selected_model_id = None
    if hasattr(st, 'session_state') and 'selected_model' in st.session_state:
        selected_model_id = st.session_state.selected_model
    
    rag_service = RAGService(
        collection_name=collection_name,
        enable_debug=enable_debug,
        enable_markdown_formatting=True,
        use_agentic_rag=use_agentic_rag,
        model_id=selected_model_id,
    )
    
    if hasattr(st, 'session_state'):
        st.session_state.rag_service = rag_service
        st.session_state.rag_service_validated = True
    
    logger.info("RAGService 创建完成（延迟加载模式）")
    return rag_service


def init_chat_manager(manager: InitializationManager) -> Any:
    """初始化对话管理器（延迟加载）"""
    from backend.business.chat import ChatManager
    from backend.infrastructure.initialization.registry_init import init_index_manager
    
    index_manager = manager.instances.get('index_manager')
    if index_manager is None:
        logger.info("IndexManager 未初始化，自动初始化（延迟加载）")
        try:
            index_manager = init_index_manager(manager)
            manager.instances['index_manager'] = index_manager
            if 'index_manager' in manager.modules:
                manager.modules['index_manager'].status = InitStatus.SUCCESS
        except Exception as e:
            logger.error(f"延迟加载 IndexManager 失败: {e}")
            raise ValueError(f"IndexManager 实例初始化失败: {e}") from e
    
    if hasattr(st, 'session_state'):
        if 'chat_manager' in st.session_state and st.session_state.chat_manager is not None:
            logger.info("使用 session_state 中已有的 ChatManager")
            return st.session_state.chat_manager
    
    enable_debug = False
    if hasattr(st, 'session_state') and 'debug_mode_enabled' in st.session_state:
        enable_debug = st.session_state.debug_mode_enabled
    
    use_agentic_rag = False
    if hasattr(st, 'session_state') and 'use_agentic_rag' in st.session_state:
        use_agentic_rag = st.session_state.use_agentic_rag
    
    selected_model_id = None
    if hasattr(st, 'session_state') and 'selected_model' in st.session_state:
        selected_model_id = st.session_state.selected_model
    
    chat_manager = ChatManager(
        index_manager=index_manager,
        enable_debug=enable_debug,
        enable_markdown_formatting=True,
        use_agentic_rag=use_agentic_rag,
        model_id=selected_model_id,
    )
    
    if hasattr(st, 'session_state'):
        st.session_state.chat_manager = chat_manager
    
    return chat_manager
