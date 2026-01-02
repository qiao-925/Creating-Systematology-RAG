"""
索引初始化模块：初始化索引管理器的核心组件
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
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.WARNING)
    logger.propagate = False

# 抑制遥测相关的日志（对用户无用的信息）
_telemetry_loggers = [
    'posthog', 'posthog.client',
    'chromadb.telemetry',
]
for logger_name in _telemetry_loggers:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.WARNING)
    logger.propagate = False

# 注意：chromadb、chromadb.api、chromadb.client 等保留默认日志级别
# 这样可以看到连接成功、集合创建等有用的 INFO 级别日志

import chromadb
from llama_index.core import Settings

from src.infrastructure.config import config
from src.infrastructure.logger import get_logger
from src.infrastructure.embeddings.base import BaseEmbedding
from src.infrastructure.embeddings.factory import create_embedding, get_embedding_instance
from src.infrastructure.indexer.utils.info import print_database_info
from src.infrastructure.indexer.utils.dimension import ensure_collection_dimension_match

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
    
    # 初始化Chroma Cloud客户端
    logger.info(f"🗄️  初始化Chroma向量数据库: collection={collection_name}")
    
    if not config.CHROMA_CLOUD_API_KEY or not config.CHROMA_CLOUD_DATABASE:
        raise ValueError(
            "Chroma Cloud配置不完整，请设置以下环境变量：\n"
            "- CHROMA_CLOUD_API_KEY\n"
            "- CHROMA_CLOUD_DATABASE"
        )
    
    tenant = config.CHROMA_CLOUD_TENANT
    if not tenant or tenant == "your_chroma_cloud_tenant_here":
        logger.warning("⚠️  CHROMA_CLOUD_TENANT 未设置或为模板值，将尝试自动检测...")
        tenant = None
    
    try:
        if tenant:
            chroma_client = chromadb.CloudClient(
                api_key=config.CHROMA_CLOUD_API_KEY,
                tenant=tenant,
                database=config.CHROMA_CLOUD_DATABASE
            )
        else:
            chroma_client = chromadb.CloudClient(
                api_key=config.CHROMA_CLOUD_API_KEY,
                database=config.CHROMA_CLOUD_DATABASE
            )
    except chromadb.errors.ChromaAuthError as e:
        error_msg = str(e)
        if "does not match" in error_msg and "from the server" in error_msg:
            import re
            tenant_match = re.search(r'does not match ([a-f0-9\-]+) from the server', error_msg)
            if tenant_match:
                correct_tenant = tenant_match.group(1)
                logger.error(f"❌ Chroma Cloud Tenant 配置错误")
                logger.error(f"   当前配置: {config.CHROMA_CLOUD_TENANT}")
                logger.error(f"   服务器返回的正确 Tenant: {correct_tenant}")
                raise ValueError(
                    f"Chroma Cloud Tenant 配置不匹配！\n"
                    f"当前配置: {config.CHROMA_CLOUD_TENANT}\n"
                    f"服务器返回的正确 Tenant: {correct_tenant}\n\n"
                    f"请在 .env 文件中更新配置：\n"
                    f"CHROMA_CLOUD_TENANT={correct_tenant}"
                )
        raise
    except Exception as e:
        logger.error(f"❌ Chroma Cloud 初始化失败: {e}")
        raise
    
    # 创建或获取集合
    try:
        chroma_collection = chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    except Exception as e:
        logger.error(f"❌ 创建 Chroma 集合失败: {e}")
        raise
    
    return embed_model, chroma_client, chroma_collection
