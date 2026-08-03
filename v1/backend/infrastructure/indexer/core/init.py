"""
索引初始化模块：初始化索引管理器的核心组件

使用 ChromaClientManager 全局单例复用连接，减少握手延迟。
"""

from pathlib import Path
from typing import Optional
import logging

# 在导入 chromadb 之前抑制底层HTTP库的详细日志（避免噪音）
# 注意：chromadb 本身的日志保留，以便显示连接状态等有用信息
_http_loggers = [
    'urllib3', 'urllib3.connectionpool', 'urllib3.util',
    'httpx', 'httpcore', 'httpcore.http11', 'httpcore.connection',
    'httpcore.http2', 'httpcore.sync', 'httpcore.async',
]
for logger_name in _http_loggers:
    _logger = logging.getLogger(logger_name)
    _logger.setLevel(logging.WARNING)
    _logger.propagate = False

# 抑制遥测相关的日志（对用户无用的信息）
_telemetry_loggers = [
    'posthog', 'posthog.client',
    'chromadb.telemetry',
]
for logger_name in _telemetry_loggers:
    _logger = logging.getLogger(logger_name)
    _logger.setLevel(logging.WARNING)
    _logger.propagate = False

# 注意：chromadb、chromadb.api、chromadb.client 等保留默认日志级别
# 这样可以看到连接成功、集合创建等有用的 INFO 级别日志

from llama_index.core import Settings

from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger
from backend.infrastructure.embeddings.base import BaseEmbedding
from backend.infrastructure.embeddings.factory import create_embedding, get_embedding_instance
from backend.infrastructure.indexer.core.chroma_client import (
    ChromaClientManager,
    get_chroma_client,
    get_chroma_collection,
)

logger = get_logger('indexer')


def init_index_manager(
    collection_name: Optional[str],
    persist_dir: Optional[Path],  # 保留参数用于向后兼容，Chroma Cloud模式不再使用
    embedding_model_name: str,
    chunk_size: int,
    chunk_overlap: int,
    embed_model_instance: Optional[BaseEmbedding],
    embedding_instance: Optional[BaseEmbedding]
):
    """初始化索引管理器的核心组件
    
    Returns:
        tuple: (embed_model, chroma_client, chroma_collection)
    """
    # 初始化embedding模型
    if embedding_instance is not None:
        instance_type = type(embedding_instance).__name__
        logger.info(f"✅ 使用提供的Embedding实例: {instance_type}")
        embed_model = embedding_instance
    elif embed_model_instance is not None:
        logger.info(f"✅ 使用预加载的Embedding模型: {embedding_model_name}")
        embed_model = embed_model_instance
    else:
        # 检查全局缓存
        cached_embedding = get_embedding_instance()
        if cached_embedding is not None:
            cached_model_name = cached_embedding.get_model_name()
            if cached_model_name == embedding_model_name:
                logger.info(f"✅ 使用全局缓存的Embedding模型: {embedding_model_name}")
                embed_model = cached_embedding
            else:
                logger.info(f"🔄 模型配置变更: {cached_model_name} -> {embedding_model_name}")
                embed_model = None
        else:
            embed_model = None
        
        if embed_model is None:
            logger.info(f"📦 创建Embedding模型: {embedding_model_name}")
            try:
                embed_model = create_embedding(
                    model_name=embedding_model_name,
                    force_reload=False
                )
            except Exception as e:
                logger.error(f"❌ 创建Embedding模型失败: {e}")
                raise
    
    # 配置全局Settings
    try:
        Settings.embed_model = embed_model
    except (AssertionError, TypeError) as e:
        logger.warning(f"⚠️  直接设置embed_model失败: {e}，尝试绕过类型检查")
        try:
            Settings._embed_model = embed_model
        except Exception:
            logger.error(f"❌ 无法设置embed_model: {e}")
            raise
    
    Settings.chunk_size = chunk_size
    Settings.chunk_overlap = chunk_overlap
    
    # 使用全局单例获取 Chroma 客户端和 Collection
    # ChromaClientManager 会在首次调用时初始化连接，后续复用
    logger.info(f"🗄️  获取 Chroma 向量数据库: collection={collection_name}")
    
    chroma_client = get_chroma_client()
    chroma_collection = get_chroma_collection(collection_name)
    
    return embed_model, chroma_client, chroma_collection
