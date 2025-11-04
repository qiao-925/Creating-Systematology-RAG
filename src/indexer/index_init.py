"""
索引管理器主类 - 初始化模块
IndexManager初始化相关方法
"""

import os
from pathlib import Path
from typing import Optional

import chromadb
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from src.config import config, get_gpu_device, is_gpu_available
from src.logger import setup_logger
from src.embeddings.base import BaseEmbedding
from src.indexer.embedding_utils import (
    load_embedding_model,
    clear_embedding_model_cache,
    _setup_huggingface_env,
    get_global_embed_model
)
from src.indexer.index_core import print_database_info
from src.indexer.index_dimension import ensure_collection_dimension_match

logger = setup_logger('indexer')


def init_index_manager(
    collection_name: Optional[str],
    persist_dir: Optional[Path],  # 保留参数用于向后兼容，Chroma Cloud模式不再使用
    embedding_model_name: str,
    chunk_size: int,
    chunk_overlap: int,
    embed_model_instance: Optional[HuggingFaceEmbedding],
    embedding_instance: Optional[BaseEmbedding]
):
    """初始化索引管理器的核心组件
    
    Returns:
        tuple: (embed_model, chroma_client, chroma_collection)
    """
    # 初始化embedding模型
    # 优先使用新架构的BaseEmbedding实例，支持可插拔设计
    # 新架构提供了统一的接口和更好的扩展性，同时兼容旧接口
    if embedding_instance is not None:
        logger.info(f"✅ 使用提供的Embedding实例: {embedding_instance}")
        # 适配器模式：如果实例有适配方法，转换为llama_index兼容格式
        # 否则直接使用（可能是已兼容的实例）
        if hasattr(embedding_instance, 'get_llama_index_embedding'):
            embed_model = embedding_instance.get_llama_index_embedding()
        else:
            embed_model = embedding_instance
    elif embed_model_instance is not None:
        logger.info(f"✅ 使用预加载的Embedding模型（旧接口）: {embedding_model_name}")
        embed_model = embed_model_instance
    else:
        # 检查全局缓存
        # Embedding模型加载成本高（数GB大小、GPU内存占用），全局缓存避免重复加载
        # 多个IndexManager实例共享同一个模型实例，节省内存和加载时间
        global_embed_model = get_global_embed_model()
        cached_model_name = None
        if global_embed_model is not None:
            cached_model_name = getattr(global_embed_model, 'model_name', None)
        
        # 如果配置的模型名称与缓存不一致，必须清空缓存
        # 不同模型的向量维度不同，混用会导致索引维度不匹配错误
        if cached_model_name and cached_model_name != embedding_model_name:
            logger.info(f"🔄 检测到模型配置变更: {cached_model_name} -> {embedding_model_name}")
            clear_embedding_model_cache()
        
        # 验证缓存模型是否可用
        # 模型可能已被释放或损坏，需要实际调用一次确认可用性
        if global_embed_model is not None:
            try:
                test_embedding = global_embed_model.get_query_embedding("test")
                cached_dim = len(test_embedding)
                logger.info(f"✅ 使用全局缓存的Embedding模型: {embedding_model_name} (维度: {cached_dim})")
                embed_model = global_embed_model
            except Exception as e:
                # 缓存模型不可用时清空，避免后续继续使用损坏的模型
                logger.warning(f"⚠️  验证缓存模型失败，重新加载: {e}")
                clear_embedding_model_cache()
                embed_model = None
        else:
            embed_model = None
        
        # 如果缓存不可用，加载新模型
        if embed_model is None:
            _setup_huggingface_env()
            logger.info(f"📦 正在加载Embedding模型: {embedding_model_name}")
            try:
                embed_model = load_embedding_model(
                    model_name=embedding_model_name,
                    force_reload=False
                )
            except Exception as e:
                logger.warning(f"⚠️  load_embedding_model失败: {e}")
                embed_model = _load_embedding_model_fallback(embedding_model_name)
    
    # 配置全局Settings
    # llama_index使用全局Settings存储默认配置，所有组件都会从中读取
    # 必须设置这些值，否则文档分块和向量化会使用默认值（可能不符合预期）
    Settings.embed_model = embed_model
    Settings.chunk_size = chunk_size
    Settings.chunk_overlap = chunk_overlap
    
    # 初始化Chroma Cloud客户端
    logger.info("🗄️  初始化Chroma Cloud向量数据库")
    from src.config import config
    
    if not config.CHROMA_CLOUD_API_KEY or not config.CHROMA_CLOUD_TENANT or not config.CHROMA_CLOUD_DATABASE:
        raise ValueError(
            "Chroma Cloud配置不完整，请设置以下环境变量：\n"
            "- CHROMA_CLOUD_API_KEY\n"
            "- CHROMA_CLOUD_TENANT\n"
            "- CHROMA_CLOUD_DATABASE"
        )
    
    chroma_client = chromadb.CloudClient(
        api_key=config.CHROMA_CLOUD_API_KEY,
        tenant=config.CHROMA_CLOUD_TENANT,
        database=config.CHROMA_CLOUD_DATABASE
    )
    
    # 创建或获取集合
    chroma_collection = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    
    return embed_model, chroma_client, chroma_collection


def _load_embedding_model_fallback(embedding_model_name: str):
    """回退的embedding模型加载方法"""
    cache_folder = str(Path.home() / ".cache" / "huggingface")
    device = get_gpu_device()
    import torch
    
    if device.startswith("cuda") and is_gpu_available():
        device_name = torch.cuda.get_device_name()
        logger.info(f"✅ Embedding模型使用GPU加速:")
        logger.info(f"   设备: {device}")
        logger.info(f"   GPU名称: {device_name}")
    else:
        logger.warning("⚠️  Embedding模型使用CPU模式")
    
    model_kwargs = {
        "trust_remote_code": True,
        "cache_folder": cache_folder,
    }
    
    embed_model = HuggingFaceEmbedding(
        model_name=embedding_model_name,
        embed_batch_size=config.EMBED_BATCH_SIZE,
        max_length=config.EMBED_MAX_LENGTH,
        **model_kwargs
    )
    
    # 手动将模型移到 GPU
    try:
        if device.startswith("cuda") and is_gpu_available():
            if hasattr(embed_model, '_model') and hasattr(embed_model._model, 'to'):
                embed_model._model = embed_model._model.to(device)
            elif hasattr(embed_model, 'model') and hasattr(embed_model.model, 'to'):
                embed_model.model = embed_model.model.to(device)
    except Exception as e:
        logger.warning(f"⚠️  无法将模型移动到 GPU: {e}")
    
    if device.startswith("cuda"):
        logger.info(f"✅ 模型加载完成 (GPU加速, 批处理: {config.EMBED_BATCH_SIZE})")
    else:
        logger.info(f"✅ 模型加载完成 (CPU模式, 批处理: {config.EMBED_BATCH_SIZE}, 建议调整为5-10)")
    
    return embed_model

