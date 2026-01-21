"""
初始化注册表：注册所有需要初始化的模块

主要功能：
- register_all_modules()：注册所有模块到初始化管理器
- 定义各模块的检查函数和依赖关系
"""

import streamlit as st
from typing import Optional, Any

from backend.infrastructure.initialization.manager import InitializationManager, InitStatus
from backend.infrastructure.initialization.categories import InitCategory
from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger('initialization_registry')


def register_all_modules(manager: InitializationManager) -> None:
    """注册所有需要初始化的模块到初始化管理器
    
    Args:
        manager: 初始化管理器实例
    """
    logger.info("开始注册所有模块...")
    
    # ========== 基础层 ==========
    
    # 1. 编码设置
    manager.register_module(
        name="encoding",
        category=InitCategory.FOUNDATION.value,
        check_func=lambda: _check_encoding(),
        init_func=lambda: _init_encoding(manager),
        is_required=True,
        description="UTF-8编码设置"
    )
    
    # 2. 配置系统
    manager.register_module(
        name="config",
        category=InitCategory.FOUNDATION.value,
        check_func=lambda: _check_config(),
        init_func=lambda: _init_config(manager),
        dependencies=["encoding"],
        is_required=True,
        description="配置系统加载"
    )
    
    # 3. 日志系统
    manager.register_module(
        name="logger",
        category=InitCategory.FOUNDATION.value,
        check_func=lambda: _check_logger(),
        init_func=lambda: _init_logger(manager),
        dependencies=["config"],
        is_required=True,
        description="日志系统初始化"
    )
    
    # ========== 核心层 ==========
    
    # 4. Embedding 模型（延迟加载：启动时不初始化，首次使用时再初始化）
    manager.register_module(
        name="embedding",
        category=InitCategory.CORE.value,
        check_func=lambda: _check_embedding(),
        init_func=lambda: _init_embedding(manager),
        dependencies=["config", "logger"],
        is_required=False,  # 改为可选，延迟加载
        description=f"Embedding模型 ({config.EMBEDDING_TYPE}) - 延迟加载"
    )
    
    # 5. Chroma 向量数据库（延迟加载：启动时不连接，首次使用时再连接）
    manager.register_module(
        name="chroma",
        category=InitCategory.CORE.value,
        check_func=lambda: _check_chroma(),
        dependencies=["config", "logger"],
        is_required=False,  # 改为可选，延迟加载
        description="Chroma向量数据库连接 - 延迟加载"
    )
    
    # 6. 索引管理器（延迟加载：启动时不初始化，首次使用时再初始化）
    manager.register_module(
        name="index_manager",
        category=InitCategory.CORE.value,
        check_func=lambda: _check_index_manager(),
        init_func=lambda: _init_index_manager(manager),
        dependencies=[],  # 移除强制依赖，改为延迟初始化
        is_required=False,  # 改为可选，延迟加载
        description="索引管理器 - 延迟加载"
    )
    
    # 7. LLM 工厂
    manager.register_module(
        name="llm_factory",
        category=InitCategory.CORE.value,
        check_func=lambda: _check_llm_factory(),
        init_func=lambda: _init_llm_factory(manager),
        dependencies=["config", "logger"],
        is_required=True,
        description="LLM工厂（DeepSeek）"
    )
    
    # 8. 会话状态
    manager.register_module(
        name="session_state",
        category=InitCategory.CORE.value,
        check_func=lambda: _check_session_state(),
        init_func=lambda: _init_session_state(manager),
        dependencies=["config"],
        is_required=True,
        description="Streamlit会话状态初始化"
    )
    
    # 9. RAG 服务（延迟加载：启动时不初始化，首次使用时再初始化）
    manager.register_module(
        name="rag_service",
        category=InitCategory.CORE.value,
        check_func=lambda: _check_rag_service(),
        init_func=lambda: _init_rag_service(manager),
        dependencies=["llm_factory"],  # 移除对 index_manager 的强制依赖
        is_required=False,  # 改为可选，延迟加载
        description="RAG服务 - 延迟加载"
    )
    
    # 10. 对话管理器（延迟加载：启动时不初始化，首次使用时再初始化）
    manager.register_module(
        name="chat_manager",
        category=InitCategory.CORE.value,
        check_func=lambda: _check_chat_manager(),
        init_func=lambda: _init_chat_manager(manager),
        dependencies=["llm_factory"],  # 移除对 index_manager 的强制依赖
        is_required=False,  # 改为可选，延迟加载
        description="对话管理器 - 延迟加载"
    )
    
    # ========== 可选层 ==========
    
    # 11. 查询引擎（可选）
    manager.register_module(
        name="query_engine",
        category=InitCategory.OPTIONAL.value,
        check_func=lambda: _check_query_engine(),
        dependencies=["index_manager", "llm_factory"],
        is_required=False,
        description="模块化查询引擎"
    )
    
    # 12. LlamaDebug 观察器
    manager.register_module(
        name="llama_debug",
        category=InitCategory.OPTIONAL.value,
        check_func=lambda: _check_llama_debug(),
        dependencies=["config", "logger"],
        is_required=False,
        description="LlamaDebug调试工具"
    )
    
    # 13. RAGAS 评估器
    manager.register_module(
        name="ragas",
        category=InitCategory.OPTIONAL.value,
        check_func=lambda: _check_ragas(),
        dependencies=["config", "logger"],
        is_required=False,
        description="RAGAS评估工具"
    )
    
    logger.info(f"✅ 已注册 {len(manager.modules)} 个模块")


# ========== 初始化函数实现 ==========

def _init_encoding(manager: InitializationManager) -> bool:
    """初始化编码设置"""
    try:
        from backend.infrastructure.encoding import setup_utf8_encoding
        result = setup_utf8_encoding()
        return result
    except ImportError:
        # 如果 encoding 模块尚未加载，手动设置基础编码
        import os
        os.environ["PYTHONIOENCODING"] = "utf-8"
        return True
    except Exception as e:
        logger.error(f"编码设置失败: {e}")
        raise


def _init_config(manager: InitializationManager) -> Any:
    """初始化配置系统"""
    # 配置系统在导入时已经初始化，这里只是确保已加载
    from backend.infrastructure.config import config
    return config


def _init_logger(manager: InitializationManager) -> Any:
    """初始化日志系统"""
    # 日志系统在导入时已经初始化
    from backend.infrastructure.logger import get_logger
    test_logger = get_logger('initialization_test')
    return test_logger


def _init_embedding(manager: InitializationManager) -> Any:
    """初始化Embedding模型并验证连接
    
    优化：缓存首次验证的维度信息，避免后续重复 API 调用
    """
    from backend.infrastructure.embeddings.factory import create_embedding, get_embedding_instance
    
    # 先尝试从工厂函数获取缓存的实例
    cached_instance = get_embedding_instance()
    if cached_instance is not None:
        logger.info(f"使用工厂函数缓存的 Embedding 实例: {type(cached_instance).__name__}")
        # 验证连接（生成测试向量）
        try:
            test_embedding = cached_instance.get_query_embedding("test")
            embed_dim = len(test_embedding)
            logger.info(f"✅ Embedding 连接验证成功（维度: {embed_dim}）")
            # 缓存维度信息，避免后续重复 API 调用
            cached_instance._cached_embed_dim = embed_dim
        except Exception as e:
            logger.warning(f"⚠️  缓存的 Embedding 实例连接验证失败: {e}，将重新创建")
            cached_instance = None
    
    # 创建新的 Embedding 实例
    if cached_instance is None:
        embedding_instance = create_embedding()
        
        # 验证连接（生成测试向量）
        try:
            test_embedding = embedding_instance.get_query_embedding("test")
            embed_dim = len(test_embedding)
            logger.info(f"✅ Embedding 连接验证成功（维度: {embed_dim}）")
            # 缓存维度信息，避免后续重复 API 调用
            embedding_instance._cached_embed_dim = embed_dim
        except Exception as e:
            logger.error(f"❌ Embedding 连接验证失败: {e}")
            raise RuntimeError(f"Embedding 模型连接失败: {e}") from e
    else:
        embedding_instance = cached_instance
    
    # 存储到 session_state（如果可用）
    if hasattr(st, 'session_state'):
        st.session_state.embed_model = embedding_instance
        st.session_state.embed_model_loaded = True
    
    logger.info(f"Embedding 实例创建成功: {type(embedding_instance).__name__}")
    return embedding_instance


def _init_index_manager(manager: InitializationManager) -> Any:
    """初始化索引管理器（延迟加载：如果依赖未初始化，则自动初始化）"""
    from backend.infrastructure.indexer import IndexManager
    
    # 检查 session_state 中是否已有
    if hasattr(st, 'session_state'):
        if 'index_manager' in st.session_state and st.session_state.index_manager is not None:
            logger.info("使用 session_state 中已有的 IndexManager")
            return st.session_state.index_manager
    
    # 延迟加载：如果 embedding 未初始化，则自动初始化
    embedding = manager.instances.get('embedding')
    if embedding is None:
        logger.info("Embedding 未初始化，自动初始化（延迟加载）")
        try:
            embedding = _init_embedding(manager)
            # 保存到管理器实例中
            manager.instances['embedding'] = embedding
            # 更新模块状态
            if 'embedding' in manager.modules:
                manager.modules['embedding'].status = InitStatus.SUCCESS
        except Exception as e:
            logger.error(f"延迟加载 Embedding 失败: {e}")
            raise ValueError(f"Embedding 实例初始化失败: {e}") from e
    
    # 创建新的 IndexManager
    collection_name = config.CHROMA_COLLECTION_NAME
    if hasattr(st, 'session_state') and 'collection_name' in st.session_state:
        collection_name = st.session_state.collection_name
    
    index_manager = IndexManager(
        collection_name=collection_name,
        embedding_instance=embedding
    )
    
    # 存储到 session_state（如果可用）
    if hasattr(st, 'session_state'):
        st.session_state.index_manager = index_manager
        st.session_state.index_manager_validated = True
    
    return index_manager


def _init_llm_factory(manager: InitializationManager) -> Any:
    """初始化LLM工厂（创建LLM实例，不调用API）"""
    from backend.infrastructure.llms.factory import create_deepseek_llm_for_query
    
    if not config.DEEPSEEK_API_KEY:
        raise ValueError("未设置 DEEPSEEK_API_KEY")
    
    # 创建LLM实例（不实际调用API）
    llm = create_deepseek_llm_for_query(
        api_key=config.DEEPSEEK_API_KEY,
        model=config.LLM_MODEL,
    )
    
    return llm


def _init_session_state(manager: InitializationManager) -> None:
    """初始化会话状态（包括GitHub同步管理器）"""
    from frontend.utils.state import init_session_state
    
    init_session_state()
    
    # 验证 GitHub 同步管理器是否已初始化
    if hasattr(st, 'session_state'):
        if 'github_sync_manager' in st.session_state and st.session_state.github_sync_manager is not None:
            try:
                # 测试 GitHub 同步管理器是否正常工作（列出仓库）
                repos = st.session_state.github_sync_manager.list_repositories()
                logger.info(f"✅ GitHub 同步管理器初始化成功（已管理 {len(repos)} 个仓库）")
            except Exception as e:
                logger.warning(f"⚠️  GitHub 同步管理器验证失败: {e}")
        else:
            logger.warning("⚠️  GitHub 同步管理器未在 session_state 中找到")
    
    return None


def _init_rag_service(manager: InitializationManager) -> Any:
    """初始化RAG服务（延迟加载：不依赖 index_manager，通过 @property 延迟加载）"""
    from backend.business.rag_api import RAGService
    
    # 检查 session_state 中是否已有
    if hasattr(st, 'session_state'):
        if 'rag_service' in st.session_state and st.session_state.rag_service is not None:
            logger.info("使用 session_state 中已有的 RAGService")
            return st.session_state.rag_service
    
    # 创建新的 RAGService（不立即初始化 index_manager，通过 @property 延迟加载）
    collection_name = config.CHROMA_COLLECTION_NAME
    if hasattr(st, 'session_state') and 'collection_name' in st.session_state:
        collection_name = st.session_state.collection_name
    
    enable_debug = False
    if hasattr(st, 'session_state') and 'debug_mode_enabled' in st.session_state:
        enable_debug = st.session_state.debug_mode_enabled
    
    # 读取 use_agentic_rag 配置
    use_agentic_rag = False
    if hasattr(st, 'session_state') and 'use_agentic_rag' in st.session_state:
        use_agentic_rag = st.session_state.use_agentic_rag
    
    # RAGService 创建时不初始化 index_manager，通过 @property 延迟加载
    rag_service = RAGService(
        collection_name=collection_name,
        enable_debug=enable_debug,
        enable_markdown_formatting=True,
        use_agentic_rag=use_agentic_rag,
    )
    
    # 存储到 session_state（如果可用）
    if hasattr(st, 'session_state'):
        st.session_state.rag_service = rag_service
        st.session_state.rag_service_validated = True
    
    logger.info("RAGService 创建完成（延迟加载模式）")
    return rag_service


def _init_chat_manager(manager: InitializationManager) -> Any:
    """初始化对话管理器（延迟加载：不依赖 index_manager，通过 RAGService 延迟加载）"""
    from backend.business.chat import ChatManager
    
    # 延迟加载：如果 index_manager 未初始化，则自动初始化
    index_manager = manager.instances.get('index_manager')
    if index_manager is None:
        logger.info("IndexManager 未初始化，自动初始化（延迟加载）")
        try:
            index_manager = _init_index_manager(manager)
            # 保存到管理器实例中
            manager.instances['index_manager'] = index_manager
            # 更新模块状态
            if 'index_manager' in manager.modules:
                manager.modules['index_manager'].status = InitStatus.SUCCESS
        except Exception as e:
            logger.error(f"延迟加载 IndexManager 失败: {e}")
            raise ValueError(f"IndexManager 实例初始化失败: {e}") from e
    
    # 检查 session_state 中是否已有
    if hasattr(st, 'session_state'):
        if 'chat_manager' in st.session_state and st.session_state.chat_manager is not None:
            logger.info("使用 session_state 中已有的 ChatManager")
            return st.session_state.chat_manager
    
    # 创建新的 ChatManager
    enable_debug = False
    if hasattr(st, 'session_state') and 'debug_mode_enabled' in st.session_state:
        enable_debug = st.session_state.debug_mode_enabled
    
    # 读取 use_agentic_rag 配置
    use_agentic_rag = False
    if hasattr(st, 'session_state') and 'use_agentic_rag' in st.session_state:
        use_agentic_rag = st.session_state.use_agentic_rag
    
    chat_manager = ChatManager(
        index_manager=index_manager,
        enable_debug=enable_debug,
        enable_markdown_formatting=True,
        use_agentic_rag=use_agentic_rag,
    )
    
    # 存储到 session_state（如果可用）
    if hasattr(st, 'session_state'):
        st.session_state.chat_manager = chat_manager
    
    return chat_manager


# ========== 检查函数实现 ==========

def _check_encoding() -> bool:
    """检查编码设置"""
    try:
        import os
        return os.environ.get("PYTHONIOENCODING", "").lower() == "utf-8"
    except Exception:
        return False


def _check_config() -> bool:
    """检查配置系统"""
    try:
        # 检查关键配置是否存在
        return (
            hasattr(config, 'DEEPSEEK_API_KEY') and
            hasattr(config, 'EMBEDDING_TYPE') and
            hasattr(config, 'CHROMA_COLLECTION_NAME')
        )
    except Exception:
        return False


def _check_logger() -> bool:
    """检查日志系统"""
    try:
        from backend.infrastructure.logger import get_logger
        test_logger = get_logger('test')
        test_logger.info("测试日志")
        return True
    except Exception:
        return False


def _check_embedding() -> bool:
    """检查Embedding模型"""
    try:
        # 检查session_state中是否有embedding实例
        if hasattr(st, 'session_state'):
            if 'embed_model' in st.session_state and st.session_state.embed_model is not None:
                return True
        
        # 尝试从工厂函数获取
        from backend.infrastructure.embeddings.factory import get_embedding_instance
        instance = get_embedding_instance()
        return instance is not None
    except Exception:
        return False


def _check_chroma() -> bool:
    """检查Chroma向量数据库"""
    try:
        # 检查配置
        if not config.CHROMA_COLLECTION_NAME:
            return False
        
        # 尝试创建IndexManager来测试Chroma连接
        from backend.infrastructure.indexer import IndexManager
        # 不实际创建，只检查配置
        return True
    except Exception:
        return False


def _check_index_manager() -> bool:
    """检查索引管理器"""
    try:
        # 优先从统一初始化系统获取
        init_result = st.session_state.get('init_result')
        if init_result and 'index_manager' in init_result.instances:
            return init_result.instances['index_manager'] is not None
        
        # 回退到 session_state 检查
        if hasattr(st, 'session_state'):
            if 'index_manager' in st.session_state and st.session_state.index_manager is not None:
                return True
        
        return False
    except Exception as e:
        logger.debug(f"索引管理器检查失败: {e}")
        return False


def _check_llm_factory() -> bool:
    """检查LLM工厂"""
    try:
        # 检查API Key是否配置
        if not config.DEEPSEEK_API_KEY:
            return False
        
        # 尝试创建LLM实例（不实际调用API）
        from backend.infrastructure.llms.factory import create_deepseek_llm_for_query
        # 只检查函数是否存在，不实际创建
        return callable(create_deepseek_llm_for_query)
    except Exception:
        return False


def _check_query_engine() -> bool:
    """检查查询引擎"""
    try:
        # 查询引擎是可选的，需要索引管理器
        if not _check_index_manager():
            return False
        
        # 检查模块是否存在
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        return True
    except Exception:
        return False


def _check_rag_service() -> bool:
    """检查RAG服务"""
    try:
        # 优先从统一初始化系统获取
        init_result = st.session_state.get('init_result')
        if init_result and 'rag_service' in init_result.instances:
            return init_result.instances['rag_service'] is not None
        
        # 回退到 session_state 检查
        if hasattr(st, 'session_state'):
            if 'rag_service' in st.session_state and st.session_state.rag_service is not None:
                return True
        
        return False
    except Exception as e:
        logger.debug(f"RAG服务检查失败: {e}")
        return False


def _check_chat_manager() -> bool:
    """检查对话管理器"""
    try:
        # 优先从统一初始化系统获取
        init_result = st.session_state.get('init_result')
        if init_result and 'chat_manager' in init_result.instances:
            return init_result.instances['chat_manager'] is not None
        
        # 回退到 session_state 检查
        if hasattr(st, 'session_state'):
            if 'chat_manager' in st.session_state and st.session_state.chat_manager is not None:
                return True
        
        return False
    except Exception as e:
        logger.debug(f"对话管理器检查失败: {e}")
        return False


def _check_session_state() -> bool:
    """检查会话状态"""
    try:
        if not hasattr(st, 'session_state'):
            return False
        
        # 检查关键状态是否存在
        required_keys = ['collection_name', 'messages']
        return all(key in st.session_state for key in required_keys)
    except Exception:
        return False


def _check_llama_debug() -> bool:
    """检查LlamaDebug观察器
    
    Returns:
        bool: True表示检查通过，False表示检查失败
        
    Raises:
        Exception: 检查过程中出现异常时抛出，包含详细错误信息
    """
    from backend.infrastructure.logger import get_logger
    check_logger = get_logger('initialization.check')
    
    # 检查配置项是否存在
    if not hasattr(config, 'ENABLE_DEBUG_HANDLER'):
        error_msg = "配置项 ENABLE_DEBUG_HANDLER 不存在，请检查配置文件"
        check_logger.error(error_msg)
        raise AttributeError(error_msg)
    
    # 检查是否启用
    if not config.ENABLE_DEBUG_HANDLER:
        error_msg = "LlamaDebug 未启用（ENABLE_DEBUG_HANDLER=False），请在 application.yml 中设置 observability.llama_debug.enable=true"
        check_logger.warning(error_msg)
        # 对于可选模块，未启用时返回 False 而不是抛出异常
        return False
    
    # 检查模块是否存在
    try:
        from backend.infrastructure.observers.llama_debug_observer import LlamaDebugObserver
        check_logger.debug("LlamaDebugObserver 模块导入成功")
    except ImportError as e:
        error_msg = f"无法导入 LlamaDebugObserver 模块: {e}。请检查模块文件是否存在"
        check_logger.error(error_msg)
        raise ImportError(error_msg) from e
    
    # 尝试创建实例以验证可用性
    try:
        observer = LlamaDebugObserver(enabled=False)  # 禁用以避免副作用
        check_logger.debug("LlamaDebugObserver 实例创建成功")
    except Exception as e:
        error_msg = f"LlamaDebugObserver 实例创建失败: {e}。请检查依赖项是否正确安装"
        check_logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e
    
    check_logger.info("LlamaDebug 检查通过")
    return True


def _check_ragas() -> bool:
    """检查RAGAS评估器"""
    try:
        if not config.RAGAS_ENABLE:
            return False
        
        # 检查模块是否存在
        from backend.infrastructure.observers.ragas_evaluator import RAGASEvaluator
        return True
    except Exception:
        return False
