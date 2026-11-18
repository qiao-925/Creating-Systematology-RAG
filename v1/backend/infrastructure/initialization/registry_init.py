"""
初始化注册表：初始化函数

主要功能：
- 提供各模块的初始化函数，用于创建和配置模块实例
"""

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

    logger.info(f"Embedding 实例创建成功: {type(embedding_instance).__name__}")
    return embedding_instance


def init_index_manager(manager: InitializationManager) -> Any:
    """初始化索引管理器（延迟加载）"""
    from backend.infrastructure.indexer import IndexManager
    from backend.infrastructure.initialization.registry_init import init_embedding

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

    index_manager = IndexManager(
        collection_name=collection_name,
        embedding_instance=embedding
    )

    return index_manager


def init_llm_factory(manager: InitializationManager) -> Any:
    """初始化LLM工厂（延迟加载：仅验证配置，不创建实例）"""
    if not config.DEEPSEEK_API_KEY:
        logger.warning("未设置 DEEPSEEK_API_KEY，LLM 将在首次调用时校验")
        return {
            'default_model_id': config.get_default_llm_id(),
            'model_config': None,
            'lazy_loaded': True,
            'api_key_present': False,
        }

    default_model_id = config.get_default_llm_id()
    model_config = config.get_llm_model_config(default_model_id)
    if not model_config:
        raise ValueError(f"未找到默认模型配置: {default_model_id}")

    logger.info(f"✅ LLM工厂配置验证成功（默认模型: {default_model_id}）")
    logger.info("LLM实例将在首次使用时创建（延迟加载）")

    return {
        'default_model_id': default_model_id,
        'model_config': model_config,
        'lazy_loaded': True
    }


def init_session_state(manager: InitializationManager) -> None:
    """会话状态初始化（Streamlit 遗留，FastAPI 下为空操作）"""
    return None


def init_rag_service(manager: InitializationManager) -> Any:
    """RAG 服务已移除（Systematology 不依赖），保留空操作供初始化系统兼容"""
    logger.info("RAG 服务已移除，跳过初始化")
    return None


def init_chat_manager(manager: InitializationManager) -> Any:
    """对话管理器已移除（Systematology 不依赖），保留空操作供初始化系统兼容"""
    logger.info("对话管理器已移除，跳过初始化")
    return None
