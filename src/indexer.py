"""
索引构建模块
负责构建和管理向量索引，集成Chroma向量数据库
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict

import chromadb
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Settings,
)
from llama_index.core.schema import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.config import config, get_gpu_device, is_gpu_available, get_device_status
from src.logger import setup_logger

logger = setup_logger('indexer')

# 全局 embedding 模型缓存
_global_embed_model: Optional[HuggingFaceEmbedding] = None


def _setup_huggingface_env():
    """配置 HuggingFace 环境变量（镜像和离线模式）
    
    注意：环境变量已在 src/__init__.py 中预设，这里仅用于日志记录和确认
    """
    # 设置镜像地址
    if config.HF_ENDPOINT:
        os.environ['HF_ENDPOINT'] = config.HF_ENDPOINT
        os.environ['HUGGINGFACE_HUB_ENDPOINT'] = config.HF_ENDPOINT
        os.environ['HF_HUB_ENDPOINT'] = config.HF_ENDPOINT  # 新版本使用这个
        logger.info(f"🌐 使用 HuggingFace 镜像: {config.HF_ENDPOINT}")
    
    # 设置离线模式
    if config.HF_OFFLINE_MODE:
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        logger.info(f"📴 启用离线模式（仅使用本地缓存）")
    else:
        # 确保离线模式关闭
        os.environ.pop('HF_HUB_OFFLINE', None)
        os.environ.pop('TRANSFORMERS_OFFLINE', None)


def load_embedding_model(model_name: Optional[str] = None, force_reload: bool = False) -> HuggingFaceEmbedding:
    """加载 Embedding 模型（支持全局单例模式）
    
    Args:
        model_name: 模型名称，默认使用配置中的模型
        force_reload: 是否强制重新加载（即使已缓存）
        
    Returns:
        HuggingFaceEmbedding 实例
    """
    global _global_embed_model
    
    model_name = model_name or config.EMBEDDING_MODEL
    
    # 如果已经加载过且模型名称相同，直接返回（除非强制重新加载）
    if _global_embed_model is not None and not force_reload:
        # 检查缓存的模型名称是否与新配置一致
        cached_model_name = getattr(_global_embed_model, 'model_name', None)
        if cached_model_name == model_name:
            logger.info(f"✅ 使用缓存的 Embedding 模型（全局变量）: {model_name}")
            logger.info(f"   模型对象ID: {id(_global_embed_model)}")
            return _global_embed_model
        else:
            # 模型名称不一致，清除缓存并重新加载
            logger.info(f"🔄 检测到模型配置变更: {cached_model_name} -> {model_name}")
            logger.info(f"   清除旧模型缓存，重新加载新模型")
            _global_embed_model = None
    
    # 如果需要强制重新加载，清除缓存
    if force_reload:
        logger.info(f"🔄 强制重新加载模型")
        _global_embed_model = None
    
    # 配置 HuggingFace 环境变量
    _setup_huggingface_env()
    
    # 加载模型
    logger.info(f"📦 开始加载 Embedding 模型（全新加载）: {model_name}")
    
    try:
        # 显式指定缓存目录以确保使用本地缓存
        cache_folder = str(Path.home() / ".cache" / "huggingface")
        
        # 获取GPU设备（使用启动时检测的结果）
        device = get_gpu_device()
        import torch
        
        # 输出详细的设备信息
        if device.startswith("cuda") and is_gpu_available():
            device_name = torch.cuda.get_device_name()
            cuda_version = torch.version.cuda
            logger.info(f"✅ Embedding模型使用GPU加速:")
            logger.info(f"   设备: {device}")
            logger.info(f"   GPU名称: {device_name}")
            logger.info(f"   CUDA版本: {cuda_version}")
        else:
            logger.warning("⚠️  Embedding模型使用CPU模式")
            logger.info("💡 性能提示: CPU模式较慢，索引构建可能需要30分钟+（GPU模式下约5分钟）")
            logger.info("💡 建议: 如有GPU，请安装CUDA版本的PyTorch以获得最佳性能")
        
        # 构建模型参数
        model_kwargs = {
            "trust_remote_code": True,
            "cache_folder": cache_folder,
        }
        
        _global_embed_model = HuggingFaceEmbedding(
            model_name=model_name,
            embed_batch_size=config.EMBED_BATCH_SIZE,  # 启用批处理，提升性能
            max_length=config.EMBED_MAX_LENGTH,  # 设置最大长度
            **model_kwargs
        )
        
        # 手动将模型移到 GPU（如果不支持通过参数指定）
        try:
            if device.startswith("cuda") and is_gpu_available():
                # HuggingFaceEmbedding 使用 _model 属性
                if hasattr(_global_embed_model, '_model') and hasattr(_global_embed_model._model, 'to'):
                    _global_embed_model._model = _global_embed_model._model.to(device)
                    logger.info(f"✅ 模型已移动到 GPU: {device}")
                elif hasattr(_global_embed_model, 'model') and hasattr(_global_embed_model.model, 'to'):
                    _global_embed_model.model = _global_embed_model.model.to(device)
                    logger.info(f"✅ 模型已移动到 GPU: {device}")
            else:
                logger.info(f"📌 模型保持在 CPU 上")
        except Exception as e:
            logger.warning(f"⚠️  无法将模型移动到 GPU: {e}")
            logger.info(f"📌 模型将使用 CPU")
        
        logger.info(f"✅ Embedding 模型加载完成: {model_name}")
        logger.info(f"📁 缓存目录: {cache_folder}")
        if device.startswith("cuda"):
            logger.info(f"⚡ GPU加速模式 - 批处理大小: {config.EMBED_BATCH_SIZE} (推荐10-50)")
        else:
            logger.info(f"🐌 CPU模式 - 批处理大小: {config.EMBED_BATCH_SIZE} (建议调整为5-10)")
        logger.info(f"📏 最大长度: {config.EMBED_MAX_LENGTH}")
    except Exception as e:
        # 如果是离线模式且缺少缓存，尝试切换到在线模式
        if config.HF_OFFLINE_MODE and "offline" in str(e).lower():
            logger.warning(f"⚠️  离线模式下本地无缓存，自动切换到在线模式尝试下载")
            os.environ.pop('HF_HUB_OFFLINE', None)
            
            try:
                cache_folder = str(Path.home() / ".cache" / "huggingface")
                
                # 获取GPU设备（使用启动时检测的结果）
                device = get_gpu_device()
                import torch
                
                # 输出详细的设备信息
                if device.startswith("cuda") and is_gpu_available():
                    device_name = torch.cuda.get_device_name()
                    logger.info(f"✅ Embedding模型使用GPU加速: {device_name} ({device})")
                else:
                    logger.warning("⚠️  Embedding模型使用CPU模式")
                    logger.info("💡 性能提示: CPU模式较慢，索引构建可能需要30分钟+（GPU模式下约5分钟）")
                
                # 构建模型参数
                model_kwargs = {
                    "trust_remote_code": True,
                    "cache_folder": cache_folder,
                }
                
                _global_embed_model = HuggingFaceEmbedding(
                    model_name=model_name,
                    embed_batch_size=config.EMBED_BATCH_SIZE,
                    max_length=config.EMBED_MAX_LENGTH,
                    **model_kwargs
                )
                
                # 手动将模型移到 GPU
                try:
                    if device.startswith("cuda") and is_gpu_available():
                        # HuggingFaceEmbedding 使用 _model 属性
                        if hasattr(_global_embed_model, '_model') and hasattr(_global_embed_model._model, 'to'):
                            _global_embed_model._model = _global_embed_model._model.to(device)
                            logger.info(f"✅ 模型已移动到 GPU: {device}")
                        elif hasattr(_global_embed_model, 'model') and hasattr(_global_embed_model.model, 'to'):
                            _global_embed_model.model = _global_embed_model.model.to(device)
                            logger.info(f"✅ 模型已移动到 GPU: {device}")
                    else:
                        logger.info(f"📌 模型保持在 CPU 上")
                except Exception as e:
                    logger.warning(f"⚠️  无法将模型移动到 GPU: {e}")
                    logger.info(f"📌 模型将使用 CPU")
                
                logger.info(f"✅ Embedding 模型下载并加载完成: {model_name}")
                if device.startswith("cuda"):
                    logger.info(f"⚡ GPU加速模式 - 批处理大小: {config.EMBED_BATCH_SIZE} (推荐10-50)")
                else:
                    logger.info(f"🐌 CPU模式 - 批处理大小: {config.EMBED_BATCH_SIZE} (建议调整为5-10)")
                logger.info(f"📏 最大长度: {config.EMBED_MAX_LENGTH}")
            except Exception as retry_error:
                logger.error(f"❌ 模型加载失败: {retry_error}")
                raise
        else:
            logger.error(f"❌ 模型加载失败: {e}")
            raise
    
    return _global_embed_model


def set_global_embed_model(model: HuggingFaceEmbedding):
    """设置全局 Embedding 模型实例
    
    Args:
        model: HuggingFaceEmbedding 实例
    """
    global _global_embed_model
    _global_embed_model = model
    logger.debug("🔧 设置全局 Embedding 模型")


def get_global_embed_model() -> Optional[HuggingFaceEmbedding]:
    """获取全局 Embedding 模型实例
    
    Returns:
        已加载的模型实例，如果未加载则返回 None
    """
    return _global_embed_model


def clear_embedding_model_cache():
    """清除全局 Embedding 模型缓存
    
    用于模型切换或强制重新加载场景
    """
    global _global_embed_model
    if _global_embed_model is not None:
        logger.info(f"🧹 清除 Embedding 模型缓存")
        _global_embed_model = None


def get_embedding_model_status() -> dict:
    """获取 Embedding 模型状态信息
    
    Returns:
        包含模型状态的字典：
        {
            "loaded": bool,              # 是否已加载
            "model_name": str,           # 模型名称
            "cache_dir": str,            # 缓存目录
            "cache_exists": bool,        # 本地缓存是否存在
            "offline_mode": bool,        # 是否离线模式
            "mirror": str,               # 镜像地址
        }
    """
    import os
    from pathlib import Path
    
    model_name = config.EMBEDDING_MODEL
    
    # 检查缓存目录
    cache_root = Path.home() / ".cache" / "huggingface" / "hub"
    # HuggingFace 缓存格式: models--{org}--{model}
    model_cache_name = model_name.replace("/", "--")
    cache_dir = cache_root / f"models--{model_cache_name}"
    cache_exists = cache_dir.exists()
    
    return {
        "loaded": _global_embed_model is not None,
        "model_name": model_name,
        "cache_dir": str(cache_dir),
        "cache_exists": cache_exists,
        "offline_mode": config.HF_OFFLINE_MODE,
        "mirror": config.HF_ENDPOINT if config.HF_ENDPOINT else "huggingface.co (官方)",
    }


class IndexManager:
    """索引管理器"""
    
    def __init__(
        self,
        collection_name: Optional[str] = None,
        persist_dir: Optional[Path] = None,
        embedding_model: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        embed_model_instance: Optional[HuggingFaceEmbedding] = None,
    ):
        """初始化索引管理器
        
        Args:
            collection_name: Chroma集合名称
            persist_dir: 向量存储持久化目录
            embedding_model: Embedding模型名称
            chunk_size: 文本分块大小
            chunk_overlap: 文本分块重叠大小
            embed_model_instance: 预加载的Embedding模型实例（可选）
        """
        # 使用配置或默认值
        self.collection_name = collection_name or config.CHROMA_COLLECTION_NAME
        self.persist_dir = persist_dir or config.VECTOR_STORE_PATH
        self.embedding_model_name = embedding_model or config.EMBEDDING_MODEL
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP
        
        # 确保持久化目录存在
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化embedding模型（优先使用预加载的实例）
        if embed_model_instance is not None:
            print(f"✅ 使用预加载的Embedding模型: {self.embedding_model_name}")
            self.embed_model = embed_model_instance
        else:
            # 检查全局缓存中的模型是否匹配当前配置
            global _global_embed_model
            cached_model_name = None
            if _global_embed_model is not None:
                cached_model_name = getattr(_global_embed_model, 'model_name', None)
            
            # 如果模型名称不匹配，清理缓存
            if cached_model_name and cached_model_name != self.embedding_model_name:
                logger.info(f"🔄 检测到模型配置变更: {cached_model_name} -> {self.embedding_model_name}")
                logger.info(f"   清理旧模型缓存并重新加载")
                clear_embedding_model_cache()
            
            # 尝试使用全局缓存的模型（如果匹配）
            if _global_embed_model is not None:
                try:
                    # 验证缓存的模型是否真的匹配（通过实际计算维度）
                    test_embedding = _global_embed_model.get_query_embedding("test")
                    cached_dim = len(test_embedding)
                    logger.info(f"✅ 使用全局缓存的Embedding模型: {self.embedding_model_name} (维度: {cached_dim})")
                    self.embed_model = _global_embed_model
                except Exception as e:
                    logger.warning(f"⚠️  验证缓存模型失败，重新加载: {e}")
                    clear_embedding_model_cache()
                    # 继续下面的加载流程
                    self.embed_model = None
            else:
                self.embed_model = None
            
            # 如果缓存不可用，加载新模型
            if self.embed_model is None:
                # 配置 HuggingFace 环境变量
                _setup_huggingface_env()
                
                print(f"📦 正在加载Embedding模型: {self.embedding_model_name}")
                
                # 使用load_embedding_model函数以确保缓存管理正确
                try:
                    self.embed_model = load_embedding_model(
                        model_name=self.embedding_model_name,
                        force_reload=False  # 如果缓存匹配，直接使用
                    )
                    logger.info(f"✅ 通过load_embedding_model加载模型: {self.embedding_model_name}")
                    # 如果成功加载，跳过直接加载的代码块
                except Exception as e:
                    logger.warning(f"⚠️  load_embedding_model失败，使用直接加载方式: {e}")
                    # 回退到直接加载方式
                    try:
                        cache_folder = str(Path.home() / ".cache" / "huggingface")
                        
                        # 获取GPU设备（使用启动时检测的结果）
                        device = get_gpu_device()
                        import torch
                        
                        # 输出详细的设备信息
                        if device.startswith("cuda") and is_gpu_available():
                            device_name = torch.cuda.get_device_name()
                            cuda_version = torch.version.cuda
                            print(f"✅ Embedding模型使用GPU加速:")
                            print(f"   设备: {device}")
                            print(f"   GPU名称: {device_name}")
                            print(f"   CUDA版本: {cuda_version}")
                            logger.info(f"✅ Embedding模型使用GPU: {device_name} ({device})")
                        else:
                            print("⚠️  Embedding模型使用CPU模式")
                            print("💡 性能提示: CPU模式较慢，索引构建可能需要30分钟+（GPU模式下约5分钟）")
                            logger.warning("⚠️  Embedding模型使用CPU模式")
                            logger.info("💡 建议: 如有GPU，请安装CUDA版本的PyTorch以获得最佳性能")
                        
                        # 构建模型参数
                        model_kwargs = {
                            "trust_remote_code": True,
                            "cache_folder": cache_folder,
                        }
                        
                        self.embed_model = HuggingFaceEmbedding(
                            model_name=self.embedding_model_name,
                            embed_batch_size=config.EMBED_BATCH_SIZE,  # 启用批处理
                            max_length=config.EMBED_MAX_LENGTH,
                            **model_kwargs
                        )
                        
                        # 手动将模型移到 GPU（如果不支持通过参数指定）
                        try:
                            if device.startswith("cuda") and is_gpu_available():
                                # HuggingFaceEmbedding 使用 _model 属性
                                if hasattr(self.embed_model, '_model') and hasattr(self.embed_model._model, 'to'):
                                    self.embed_model._model = self.embed_model._model.to(device)
                                    logger.info(f"✅ 模型已移动到 GPU: {device}")
                                elif hasattr(self.embed_model, 'model') and hasattr(self.embed_model.model, 'to'):
                                    self.embed_model.model = self.embed_model.model.to(device)
                                    logger.info(f"✅ 模型已移动到 GPU: {device}")
                            else:
                                logger.info(f"📌 模型保持在 CPU 上")
                        except Exception as e:
                            logger.warning(f"⚠️  无法将模型移动到 GPU: {e}")
                            logger.info(f"📌 模型将使用 CPU")
                        
                        if device.startswith("cuda"):
                            print(f"✅ 模型加载完成 (GPU加速, 批处理: {config.EMBED_BATCH_SIZE})")
                        else:
                            print(f"✅ 模型加载完成 (CPU模式, 批处理: {config.EMBED_BATCH_SIZE}, 建议调整为5-10)")
                    except Exception as load_error:
                        # 如果是离线模式且缺少缓存，尝试切换到在线模式
                        if config.HF_OFFLINE_MODE and "offline" in str(load_error).lower():
                            print(f"⚠️  离线模式下本地无缓存，自动切换到在线模式尝试下载...")
                            os.environ.pop('HF_HUB_OFFLINE', None)
                            
                            try:
                                cache_folder = str(Path.home() / ".cache" / "huggingface")
                                
                                # 获取GPU设备（使用启动时检测的结果）
                                device = get_gpu_device()
                                import torch
                                
                                # 输出详细的设备信息
                                if device.startswith("cuda") and is_gpu_available():
                                    device_name = torch.cuda.get_device_name()
                                    print(f"✅ Embedding模型使用GPU加速: {device_name} ({device})")
                                    logger.info(f"✅ Embedding模型使用GPU: {device_name} ({device})")
                                else:
                                    print("⚠️  Embedding模型使用CPU模式")
                                    print("💡 性能提示: CPU模式较慢，索引构建可能需要30分钟+（GPU模式下约5分钟）")
                                    logger.warning("⚠️  Embedding模型使用CPU模式")
                                
                                # 构建模型参数
                                model_kwargs = {
                                    "trust_remote_code": True,
                                    "cache_folder": cache_folder,
                                }
                                
                                self.embed_model = HuggingFaceEmbedding(
                                    model_name=self.embedding_model_name,
                                    embed_batch_size=config.EMBED_BATCH_SIZE,  # 启用批处理
                                    max_length=config.EMBED_MAX_LENGTH,
                                    **model_kwargs
                                )
                                
                                # 手动将模型移到 GPU
                                try:
                                    if device.startswith("cuda") and is_gpu_available():
                                        if hasattr(self.embed_model, '_model') and hasattr(self.embed_model._model, 'to'):
                                            self.embed_model._model = self.embed_model._model.to(device)
                                            logger.info(f"✅ 模型已移动到 GPU: {device}")
                                        elif hasattr(self.embed_model, 'model') and hasattr(self.embed_model.model, 'to'):
                                            self.embed_model.model = self.embed_model.model.to(device)
                                            logger.info(f"✅ 模型已移动到 GPU: {device}")
                                    else:
                                        logger.info(f"📌 模型保持在 CPU 上")
                                except Exception as e:
                                    logger.warning(f"⚠️  无法将模型移动到 GPU: {e}")
                                    logger.info(f"📌 模型将使用 CPU")
                                
                                if device.startswith("cuda"):
                                    print(f"✅ 模型下载并加载完成 (GPU加速, 批处理: {config.EMBED_BATCH_SIZE})")
                                else:
                                    print(f"✅ 模型下载并加载完成 (CPU模式, 批处理: {config.EMBED_BATCH_SIZE}, 建议调整为5-10)")
                            except Exception as retry_error:
                                print(f"❌ 模型加载失败: {retry_error}")
                                raise
                        else:
                            print(f"❌ 模型加载失败: {load_error}")
                            raise
        
        # 配置全局Settings
        Settings.embed_model = self.embed_model
        Settings.chunk_size = self.chunk_size
        Settings.chunk_overlap = self.chunk_overlap
        
        # 初始化Chroma客户端
        print(f"🗄️  初始化Chroma向量数据库: {self.persist_dir}")
        self.chroma_client = chromadb.PersistentClient(path=str(self.persist_dir))
        
        # 检测并修复embedding维度不匹配问题
        self._ensure_collection_dimension_match()
        
        # 创建向量存储
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        
        # 创建存储上下文
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        
        # 索引对象（延迟初始化）
        self._index: Optional[VectorStoreIndex] = None
        
        print("✅ 索引管理器初始化完成")
    
    def build_index(
        self,
        documents: List[LlamaDocument],
        show_progress: bool = True,
        cache_manager=None,
        task_id: Optional[str] = None
    ) -> Tuple[VectorStoreIndex, Dict[str, List[str]]]:
        """构建或更新索引
        
        Args:
            documents: 文档列表
            show_progress: 是否显示进度
            cache_manager: 缓存管理器实例（可选）
            task_id: 任务ID（可选，用于缓存）
            
        Returns:
            (VectorStoreIndex对象, 文件路径到向量ID的映射)
        """
        import time
        import hashlib
        import json
        start_time = time.time()
        
        if not documents:
            print("⚠️  没有文档可索引")
            return self.get_index(), {}
        
        # 文档级断点续传：检查每个文档是否已向量化，只处理未完成的文档
        # 这个功能默认启用，无论是否使用缓存管理器都能提高性能
        documents_to_process, already_vectorized = self._filter_vectorized_documents(documents)
        
        if already_vectorized > 0:
            logger.info(f"✅ 检测到 {already_vectorized} 个文档已向量化，跳过处理")
            print(f"📊 断点续传: {already_vectorized}/{len(documents)} 个文档已向量化，剩余 {len(documents_to_process)} 个待处理")
        
        # 如果没有需要处理的文档，直接返回
        if not documents_to_process:
            logger.info(f"✅ 所有文档已向量化，跳过向量化步骤")
            index = self.get_index()
            vector_ids_map = self._get_vector_ids_batch(
                [doc.metadata.get("file_path", "") for doc in documents 
                 if doc.metadata.get("file_path")]
            )
            
            # 如果提供了缓存管理器，更新缓存状态
            if cache_manager and task_id:
                from src.config import config
                if config.ENABLE_CACHE:
                    docs_hash = self._compute_documents_hash(documents)
                    step_name = cache_manager.STEP_VECTORIZE
                    cache_manager.mark_step_completed(
                        task_id=task_id,
                        step_name=step_name,
                        input_hash=docs_hash,
                        vector_count=self.chroma_collection.count() if hasattr(self, 'chroma_collection') else 0,
                        collection_name=self.collection_name
                    )
            
            return index, vector_ids_map
        
        # 更新待处理的文档列表
        documents = documents_to_process
        
        # 获取当前设备信息
        device = get_gpu_device()
        
        print(f"\n🔨 开始构建索引，共 {len(documents)} 个文档")
        print(f"   分块参数: size={self.chunk_size}, overlap={self.chunk_overlap}")
        
        # 输出设备信息
        if device.startswith("cuda"):
            import torch
            device_name = torch.cuda.get_device_name()
            print(f"📊 索引构建设备: {device} ⚡ GPU加速模式")
            print(f"   GPU: {device_name}")
            print(f"   批处理大小: {config.EMBED_BATCH_SIZE} (GPU推荐10-50)")
            logger.info(f"📊 索引构建使用GPU: {device_name} ({device})")
        else:
            print(f"📊 索引构建设备: {device} 🐌 CPU模式")
            print(f"   批处理大小: {config.EMBED_BATCH_SIZE} (CPU建议5-10)")
            print(f"💡 性能提示: CPU模式较慢，预计耗时30分钟+（GPU模式下约5分钟）")
            logger.warning(f"📊 索引构建使用CPU（性能较慢）")
            logger.info(f"💡 建议调整EMBED_BATCH_SIZE为5-10以获得最佳CPU性能")
        
        try:
            # 如果索引不存在，创建新索引
            if self._index is None:
                index_start_time = time.time()
                self._index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=self.storage_context,
                    show_progress=show_progress,
                )
                index_elapsed = time.time() - index_start_time
                print(f"✅ 索引创建成功 (耗时: {index_elapsed:.2f}s)")
                logger.info(f"索引创建完成: {len(documents)}个文档, 耗时{index_elapsed:.2f}s, 平均{index_elapsed/len(documents):.3f}s/文档")
            else:
                # 如果索引已存在，批量增量添加文档（优化：使用insert_ref_docs批量插入）
                insert_start_time = time.time()
                
                # 使用insert_ref_docs批量插入，性能远优于逐个insert
                # LlamaIndex会自动批处理embedding计算和向量存储写入
                try:
                    self._index.insert_ref_docs(documents, show_progress=show_progress)
                    insert_elapsed = time.time() - insert_start_time
                    print(f"✅ 文档已批量添加到现有索引 (耗时: {insert_elapsed:.2f}s)")
                    logger.info(
                        f"批量增量添加完成: {len(documents)}个文档, "
                        f"耗时{insert_elapsed:.2f}s, "
                        f"平均{insert_elapsed/len(documents):.3f}s/文档"
                    )
                except AttributeError:
                    # 如果insert_ref_docs不存在，回退到批量插入节点的方式
                    logger.warning("insert_ref_docs不可用，使用节点批量插入方式")
                    from llama_index.core.node_parser import SentenceSplitter
                    node_parser = SentenceSplitter(
                        chunk_size=self.chunk_size,
                        chunk_overlap=self.chunk_overlap
                    )
                    # 批量分块并插入节点
                    batch_size = config.EMBED_BATCH_SIZE * 2
                    for i in range(0, len(documents), batch_size):
                        batch_docs = documents[i:i+batch_size]
                        nodes = node_parser.get_nodes_from_documents(batch_docs)
                        # 批量插入节点
                        for node in nodes:
                            self._index.insert(node)
                        if show_progress:
                            progress = min(i + batch_size, len(documents))
                            print(f"   进度: {progress}/{len(documents)} ({progress/len(documents)*100:.1f}%)")
                    insert_elapsed = time.time() - insert_start_time
                    print(f"✅ 文档已批量添加到现有索引 (耗时: {insert_elapsed:.2f}s)")
                    logger.info(
                        f"批量增量添加完成: {len(documents)}个文档, "
                        f"耗时{insert_elapsed:.2f}s, "
                        f"平均{insert_elapsed/len(documents):.3f}s/文档"
                    )
            
            # 获取索引统计信息
            stats = self.get_stats()
            total_elapsed = time.time() - start_time
            
            print(f"📊 索引统计: {stats}")
            device_info = f"{device} ({'GPU加速' if device.startswith('cuda') else 'CPU模式'})"
            logger.info(
                f"索引构建完成 (设备: {device_info}): "
                f"文档数={len(documents)}, "
                f"向量数={stats.get('document_count', 0)}, "
                f"总耗时={total_elapsed:.2f}s, "
                f"平均={total_elapsed/len(documents):.3f}s/文档"
            )
            
            # 构建向量ID映射（优化：批量查询）
            vector_ids_map_start = time.time()
            vector_ids_map = self._get_vector_ids_batch(
                [doc.metadata.get("file_path", "") for doc in documents 
                 if doc.metadata.get("file_path")]
            )
            vector_ids_elapsed = time.time() - vector_ids_map_start
            print(f"📋 已记录 {len(vector_ids_map)} 个文件的向量ID映射 (耗时: {vector_ids_elapsed:.2f}s)")
            logger.debug(f"向量ID映射构建耗时: {vector_ids_elapsed:.2f}s")
            
            # 如果提供了缓存管理器，更新缓存状态
            if cache_manager and task_id:
                from src.config import config
                if config.ENABLE_CACHE:
                    try:
                        docs_hash = self._compute_documents_hash(documents)
                        vector_count = stats.get('document_count', 0)
                        cache_manager.mark_step_completed(
                            task_id=task_id,
                            step_name=cache_manager.STEP_VECTORIZE,
                            input_hash=docs_hash,
                            vector_count=vector_count,
                            collection_name=self.collection_name
                        )
                    except Exception as e:
                        logger.warning(f"更新向量化缓存状态失败: {e}")
            
            return self._index, vector_ids_map
            
        except Exception as e:
            print(f"❌ 索引构建失败: {e}")
            
            # 如果提供了缓存管理器，标记步骤失败
            if cache_manager and task_id:
                try:
                    cache_manager.mark_step_failed(
                        task_id=task_id,
                        step_name=cache_manager.STEP_VECTORIZE,
                        error_message=str(e)
                    )
                except Exception:
                    pass
            
            raise
    
    def get_index(self) -> VectorStoreIndex:
        """获取现有索引
        
        Returns:
            VectorStoreIndex对象
        """
        if self._index is None:
            # 尝试从已有的向量存储加载
            try:
                self._index = VectorStoreIndex.from_vector_store(
                    vector_store=self.vector_store,
                    storage_context=self.storage_context,
                )
                print("✅ 从向量存储加载索引成功")
            except Exception as e:
                print(f"ℹ️  没有找到现有索引，将在添加文档后创建")
                # 创建一个空索引
                self._index = VectorStoreIndex.from_documents(
                    [],
                    storage_context=self.storage_context,
                )
        
        return self._index
    
    def _ensure_collection_dimension_match(self):
        """确保collection的embedding维度与当前模型匹配
        
        如果collection已存在但维度不匹配，会自动删除并重新创建
        """
        try:
            # 首先确保能获取当前embedding模型的维度（必须成功）
            model_dim = None
            dim_detection_methods = []
            
            # 方法1: 尝试从模型属性获取
            if hasattr(self.embed_model, 'embed_dim'):
                model_dim = self.embed_model.embed_dim
                dim_detection_methods.append("embed_dim属性")
            elif hasattr(self.embed_model, '_model') and hasattr(self.embed_model._model, 'config'):
                # 尝试从transformers模型config获取
                try:
                    model_dim = getattr(self.embed_model._model.config, 'hidden_size', None)
                    if model_dim:
                        dim_detection_methods.append("模型config.hidden_size")
                except Exception as e:
                    logger.debug(f"从模型config获取维度失败: {e}")
            
            # 方法2: 通过实际计算一个测试向量获取维度（最可靠的方法）
            if model_dim is None:
                try:
                    test_embedding = self.embed_model.get_query_embedding("test")
                    model_dim = len(test_embedding)
                    dim_detection_methods.append("实际计算测试向量")
                except Exception as e:
                    logger.warning(f"通过测试向量获取维度失败: {e}")
            
            # 如果仍然无法获取模型维度，这是严重错误
            if model_dim is None:
                error_msg = "无法检测embedding模型维度，这可能导致维度不匹配错误"
                logger.error(error_msg)
                print(f"❌ {error_msg}")
                print(f"   尝试的方法: {dim_detection_methods}")
                raise ValueError(error_msg)
            
            logger.info(f"✅ 成功检测到embedding模型维度: {model_dim} (方法: {', '.join(dim_detection_methods)})")
            print(f"📏 当前embedding模型维度: {model_dim}")
            
            # 尝试获取现有collection
            try:
                existing_collection = self.chroma_client.get_collection(name=self.collection_name)
                
                # 获取collection的维度（从metadata或查询实际数据）
                collection_dim = None
                collection_count = existing_collection.count()
                
                try:
                    # 尝试从collection的metadata获取
                    if existing_collection.metadata and 'embedding_dimension' in existing_collection.metadata:
                        collection_dim = existing_collection.metadata['embedding_dimension']
                        logger.info(f"从collection metadata获取维度: {collection_dim}")
                    elif collection_count > 0:
                        # 如果collection有数据，尝试查询一个向量获取维度
                        sample = existing_collection.peek(limit=1)
                        if sample and 'embeddings' in sample and sample['embeddings']:
                            collection_dim = len(sample['embeddings'][0])
                            logger.info(f"从collection实际数据获取维度: {collection_dim}")
                except Exception as e:
                    logger.warning(f"获取collection维度失败: {e}")
                
                # 如果collection为空，直接使用（无需检查维度）
                if collection_count == 0:
                    self.chroma_collection = existing_collection
                    print(f"✅ Collection为空，可以使用: {self.collection_name}")
                    logger.info(f"Collection为空，直接使用: {self.collection_name}")
                # 如果collection有数据但无法获取维度，采用保守策略：删除并重建
                elif collection_dim is None:
                    print(f"⚠️  Collection有数据但无法检测维度，采用保守策略删除并重建")
                    print(f"   当前模型维度: {model_dim}")
                    print(f"🔄 自动删除旧collection并重新创建...")
                    
                    self.chroma_client.delete_collection(name=self.collection_name)
                    logger.warning(f"因无法检测维度，已删除collection: {self.collection_name} (模型维度: {model_dim})")
                    
                    # 重新创建collection
                    self.chroma_collection = self.chroma_client.get_or_create_collection(
                        name=self.collection_name
                    )
                    print(f"✅ 已重新创建collection: {self.collection_name}")
                # 如果维度不匹配，删除并重建
                elif model_dim != collection_dim:
                    print(f"⚠️  检测到embedding维度不匹配:")
                    print(f"   Collection维度: {collection_dim}")
                    print(f"   当前模型维度: {model_dim}")
                    print(f"🔄 自动删除旧collection并重新创建...")
                    
                    self.chroma_client.delete_collection(name=self.collection_name)
                    logger.info(f"已删除维度不匹配的collection: {self.collection_name} (维度: {collection_dim} -> {model_dim})")
                    
                    # 重新创建collection
                    self.chroma_collection = self.chroma_client.get_or_create_collection(
                        name=self.collection_name
                    )
                    print(f"✅ 已重新创建collection: {self.collection_name} (维度: {model_dim})")
                else:
                    # 维度匹配，使用现有collection
                    self.chroma_collection = existing_collection
                    print(f"✅ Collection维度检查通过: {model_dim}维")
                    logger.info(f"Collection维度匹配: {model_dim}维")
                    
            except Exception as e:
                # Collection不存在，创建新的
                if "does not exist" in str(e) or "not found" in str(e).lower():
                    self.chroma_collection = self.chroma_client.get_or_create_collection(
                        name=self.collection_name
                    )
                    print(f"✅ 创建新collection: {self.collection_name} (维度: {model_dim})")
                    logger.info(f"创建新collection: {self.collection_name} (维度: {model_dim})")
                else:
                    # 其他错误，重新抛出
                    logger.error(f"获取collection时出错: {e}")
                    raise
                    
        except Exception as e:
            # 如果检测过程出错，尝试删除旧collection并重建（保守策略）
            logger.error(f"维度检测过程出错: {e}")
            logger.info("采用保守策略：删除旧collection并重建")
            
            try:
                # 尝试删除旧collection（如果存在）
                try:
                    self.chroma_client.delete_collection(name=self.collection_name)
                    logger.info(f"已删除可能不兼容的collection: {self.collection_name}")
                    print(f"🔄 已删除可能不兼容的collection: {self.collection_name}")
                except:
                    # 如果删除失败（collection不存在），继续创建新collection
                    pass
                
                # 创建新collection
                self.chroma_collection = self.chroma_client.get_or_create_collection(
                    name=self.collection_name
                )
                print(f"✅ 已重新创建collection: {self.collection_name}")
                logger.info(f"已重新创建collection: {self.collection_name}")
            except Exception as fallback_error:
                logger.error(f"回退创建collection也失败: {fallback_error}")
                raise
    
    def clear_index(self):
        """清空索引"""
        try:
            # 删除集合
            self.chroma_client.delete_collection(name=self.collection_name)
            print(f"✅ 已删除集合: {self.collection_name}")
            
            # 重新创建集合
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name
            )
            self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
            self.storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )
            
            # 重置索引
            self._index = None
            print("✅ 索引已清空")
            
        except Exception as e:
            print(f"❌ 清空索引失败: {e}")
            raise
    
    def get_stats(self) -> dict:
        """获取索引统计信息
        
        Returns:
            包含统计信息的字典
        """
        try:
            count = self.chroma_collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "embedding_model": self.embedding_model_name,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
            }
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {}
    
    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """搜索相似文档（用于测试）
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        if self._index is None:
            self.get_index()
        
        retriever = self._index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)
        
        results = []
        for node in nodes:
            results.append({
                "text": node.node.text,
                "score": node.score,
                "metadata": node.node.metadata,
            })
        
        return results
    
    def incremental_update(
        self,
        added_docs: List[LlamaDocument],
        modified_docs: List[LlamaDocument],
        deleted_file_paths: List[str],
        metadata_manager=None
    ) -> dict:
        """执行增量更新
        
        Args:
            added_docs: 新增的文档列表
            modified_docs: 修改的文档列表
            deleted_file_paths: 删除的文件路径列表
            metadata_manager: 元数据管理器实例（用于查询向量ID）
            
        Returns:
            更新统计信息
        """
        stats = {
            "added": 0,
            "modified": 0,
            "deleted": 0,
            "errors": []
        }
        
        # 确保索引存在
        if self._index is None:
            self.get_index()
        
        # 1. 处理新增
        if added_docs:
            try:
                added_count, added_vector_ids = self._add_documents(added_docs)
                stats["added"] = added_count
                print(f"✅ 新增 {added_count} 个文档")
                
                # 更新元数据的向量ID
                if metadata_manager and added_docs:
                    for doc in added_docs:
                        file_path = doc.metadata.get("file_path", "")
                        if file_path and file_path in added_vector_ids:
                            owner = doc.metadata.get("repository", "").split("/")[0] if "/" in doc.metadata.get("repository", "") else ""
                            repo = doc.metadata.get("repository", "").split("/")[1] if "/" in doc.metadata.get("repository", "") else ""
                            branch = doc.metadata.get("branch", "main")
                            
                            if owner and repo:
                                metadata_manager.update_file_vector_ids(
                                    owner, repo, branch, file_path,
                                    added_vector_ids[file_path]
                                )
            except Exception as e:
                error_msg = f"新增文档失败: {e}"
                print(f"❌ {error_msg}")
                stats["errors"].append(error_msg)
        
        # 2. 处理修改（先批量删除旧的，再批量添加新的）
        if modified_docs:
            try:
                # 优化：批量收集所有需要删除的向量ID
                all_vector_ids_to_delete = []
                for doc in modified_docs:
                    file_path = doc.metadata.get("file_path", "")
                    if file_path and metadata_manager:
                        # 从元数据中获取旧的向量ID
                        owner = doc.metadata.get("repository", "").split("/")[0] if "/" in doc.metadata.get("repository", "") else ""
                        repo = doc.metadata.get("repository", "").split("/")[1] if "/" in doc.metadata.get("repository", "") else ""
                        branch = doc.metadata.get("branch", "main")
                        
                        vector_ids = metadata_manager.get_file_vector_ids(owner, repo, branch, file_path)
                        if vector_ids:
                            all_vector_ids_to_delete.extend(vector_ids)
                
                # 批量删除所有旧向量（优化：一次性删除）
                deleted_vector_count = 0
                if all_vector_ids_to_delete:
                    # 去重
                    unique_vector_ids = list(set(all_vector_ids_to_delete))
                    # 分批删除以避免单次删除过多数据
                    batch_delete_size = 100
                    for i in range(0, len(unique_vector_ids), batch_delete_size):
                        batch_ids = unique_vector_ids[i:i+batch_delete_size]
                        self._delete_vectors_by_ids(batch_ids)
                        deleted_vector_count += len(batch_ids)
                
                # 批量添加新版本
                modified_count, modified_vector_ids = self._add_documents(modified_docs)
                stats["modified"] = modified_count
                print(f"✅ 更新 {modified_count} 个文档（批量删除 {deleted_vector_count} 个旧向量）")
                
                # 更新元数据的向量ID
                if metadata_manager and modified_docs:
                    for doc in modified_docs:
                        file_path = doc.metadata.get("file_path", "")
                        if file_path and file_path in modified_vector_ids:
                            owner = doc.metadata.get("repository", "").split("/")[0] if "/" in doc.metadata.get("repository", "") else ""
                            repo = doc.metadata.get("repository", "").split("/")[1] if "/" in doc.metadata.get("repository", "") else ""
                            branch = doc.metadata.get("branch", "main")
                            
                            if owner and repo:
                                metadata_manager.update_file_vector_ids(
                                    owner, repo, branch, file_path,
                                    modified_vector_ids[file_path]
                                )
            except Exception as e:
                error_msg = f"更新文档失败: {e}"
                print(f"❌ {error_msg}")
                stats["errors"].append(error_msg)
        
        # 3. 处理删除
        if deleted_file_paths and metadata_manager:
            try:
                deleted_count = self._delete_documents(deleted_file_paths, metadata_manager)
                stats["deleted"] = deleted_count
                print(f"✅ 删除 {deleted_count} 个文档")
            except Exception as e:
                error_msg = f"删除文档失败: {e}"
                print(f"❌ {error_msg}")
                stats["errors"].append(error_msg)
        
        return stats
    
    def _add_documents(self, documents: List[LlamaDocument]) -> Tuple[int, Dict[str, List[str]]]:
        """批量添加文档到索引（优化：使用批量插入）
        
        Args:
            documents: 文档列表
            
        Returns:
            (成功添加的文档数量, 文件路径到向量ID的映射)
        """
        if not documents:
            return 0, {}
        
        try:
            # 优化：使用批量插入替代逐个插入
            # 优先尝试使用insert_ref_docs批量插入
            try:
                self._index.insert_ref_docs(documents, show_progress=False)
                count = len(documents)
            except AttributeError:
                # 如果insert_ref_docs不可用，使用节点批量插入
                from llama_index.core.node_parser import SentenceSplitter
                node_parser = SentenceSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap
                )
                # 批量分块并插入节点
                all_nodes = node_parser.get_nodes_from_documents(documents)
                for node in all_nodes:
                    self._index.insert(node)
                count = len(documents)
            except Exception as e:
                # 如果批量插入失败，回退到逐个插入（保留容错能力）
                logger.warning(f"批量插入失败，回退到逐个插入: {e}")
                count = 0
                for doc in documents:
                    try:
                        self._index.insert(doc)
                        count += 1
                    except Exception as insert_error:
                        print(f"⚠️  添加文档失败 [{doc.metadata.get('file_path', 'unknown')}]: {insert_error}")
                        logger.warning(f"添加文档失败: {insert_error}")
        except Exception as e:
            logger.error(f"批量添加文档失败: {e}")
            print(f"❌ 批量添加文档失败: {e}")
            return 0, {}
        
        # 优化：批量查询向量ID映射
        file_paths = [doc.metadata.get("file_path", "") for doc in documents 
                     if doc.metadata.get("file_path")]
        vector_ids_map = self._get_vector_ids_batch(file_paths)
        
        return count, vector_ids_map
    
    def _delete_documents(self, file_paths: List[str], metadata_manager) -> int:
        """批量删除文档
        
        Args:
            file_paths: 文件路径列表
            metadata_manager: 元数据管理器实例
            
        Returns:
            成功删除的文档数量
        """
        deleted_count = 0
        
        for file_path in file_paths:
            # 需要从文档元数据中提取仓库信息
            # 这里假设文件路径包含仓库信息
            # 实际使用时需要传递完整的仓库信息
            # 暂时跳过，因为我们需要更多上下文信息
            pass
        
        return deleted_count
    
    def _get_vector_ids_by_metadata(self, file_path: str) -> List[str]:
        """通过文件路径查询对应的向量ID列表
        
        Args:
            file_path: 文件路径
            
        Returns:
            向量ID列表
        """
        if not file_path:
            return []
        
        try:
            # 查询 Chroma collection，匹配 file_path
            results = self.chroma_collection.get(
                where={"file_path": file_path}
            )
            return results.get('ids', []) if results else []
        except Exception as e:
            logger.warning(f"查询向量ID失败 [{file_path}]: {e}")
            return []
    
    def _get_vector_ids_batch(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """批量查询向量ID映射（优化：减少查询次数）
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            文件路径到向量ID列表的映射字典
        """
        if not file_paths:
            return {}
        
        # 去重
        unique_paths = list(set(file_paths))
        vector_ids_map = {}
        
        try:
            # Chroma 不支持批量 where 条件查询，但仍可以优化：
            # 1. 减少重复查询（通过去重）
            # 2. 批量获取所有数据然后过滤（适用于数据量不大的情况）
            # 3. 或者继续逐个查询但去掉重复
            
            # 方案：分批查询以避免一次性加载过多数据
            batch_size = 50  # 每批查询50个文件路径
            total_results = 0
            
            for i in range(0, len(unique_paths), batch_size):
                batch_paths = unique_paths[i:i+batch_size]
                for file_path in batch_paths:
                    vector_ids = self._get_vector_ids_by_metadata(file_path)
                    if vector_ids:
                        vector_ids_map[file_path] = vector_ids
                        total_results += len(vector_ids)
            
            logger.debug(
                f"批量查询向量ID: "
                f"输入{len(file_paths)}个路径(去重后{len(unique_paths)}个), "
                f"找到{len(vector_ids_map)}个文件, "
                f"共{total_results}个向量"
            )
        except Exception as e:
            logger.error(f"批量查询向量ID失败: {e}")
            # 回退到逐个查询
            for file_path in unique_paths:
                try:
                    vector_ids = self._get_vector_ids_by_metadata(file_path)
                    if vector_ids:
                        vector_ids_map[file_path] = vector_ids
                except Exception as query_error:
                    logger.warning(f"查询单个向量ID失败 [{file_path}]: {query_error}")
        
        return vector_ids_map
    
    def _delete_vectors_by_ids(self, vector_ids: List[str]):
        """根据向量ID删除向量
        
        Args:
            vector_ids: 向量ID列表
        """
        if not vector_ids:
            return
        
        try:
            self.chroma_collection.delete(ids=vector_ids)
        except Exception as e:
            print(f"⚠️  删除向量失败: {e}")
            raise
    
    def get_node_ids_for_document(self, doc_id: str) -> List[str]:
        """获取文档对应的所有节点ID
        
        Args:
            doc_id: 文档ID
            
        Returns:
            节点ID列表
        """
        # LlamaIndex 使用节点（Node）的概念，每个文档分块后会生成多个节点
        # 需要查询 Chroma collection 来获取与文档相关的所有节点
        try:
            # 查询所有数据，然后过滤出匹配的
            # 注意：这是一个简化实现，大规模数据时需要优化
            result = self.chroma_collection.get()
            
            if not result or 'ids' not in result:
                return []
            
            # 返回所有ID（简化版本，实际应该根据元数据过滤）
            return result['ids']
        except Exception as e:
            print(f"⚠️  查询节点ID失败: {e}")
            return []
    
    @staticmethod
    def _compute_documents_hash(documents: List[LlamaDocument]) -> str:
        """计算文档列表的哈希值
        
        Args:
            documents: 文档列表
            
        Returns:
            MD5哈希值
        """
        import hashlib
        import json
        
        # 基于文档文本内容和元数据计算哈希
        docs_data = []
        for doc in documents:
            docs_data.append({
                "text": doc.text[:1000],  # 只使用前1000字符以提高性能
                "file_path": doc.metadata.get("file_path", ""),
                "file_name": doc.metadata.get("file_name", "")
            })
        
        docs_str = json.dumps(docs_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(docs_str.encode('utf-8')).hexdigest()
    
    def _check_vectors_exist(self, documents: List[LlamaDocument]) -> bool:
        """检查文档对应的向量是否已存在于 Chroma 中
        
        Args:
            documents: 文档列表
            
        Returns:
            如果所有文档的向量都存在返回True，否则返回False
        """
        try:
            # 检查 collection 是否存在且有数据
            if not hasattr(self, 'chroma_collection'):
                return False
            
            collection_count = self.chroma_collection.count()
            if collection_count == 0:
                return False
            
            # 检查每个文档是否都有对应的向量
            # 简化版本：如果 collection 有数据且文档数量合理，认为已存在
            # 更严格的检查可以通过查询每个文件的向量ID实现
            file_paths = [doc.metadata.get("file_path", "") for doc in documents if doc.metadata.get("file_path")]
            if not file_paths:
                return False
            
            # 检查至少一部分文件的向量是否存在
            sample_paths = file_paths[:min(5, len(file_paths))]  # 检查前5个文件
            existing_count = 0
            for file_path in sample_paths:
                vector_ids = self._get_vector_ids_by_metadata(file_path)
                if vector_ids:
                    existing_count += 1
            
            # 如果所有样本文件都有向量，认为缓存有效
            return existing_count == len(sample_paths)
            
        except Exception as e:
            logger.warning(f"检查向量存在性失败: {e}")
            return False
    
    def _filter_vectorized_documents(
        self, 
        documents: List[LlamaDocument]
    ) -> Tuple[List[LlamaDocument], int]:
        """过滤已向量化的文档，实现文档级断点续传
        
        Args:
            documents: 文档列表
            
        Returns:
            (待处理的文档列表, 已向量化的文档数量)
        """
        if not documents:
            return [], 0
        
        # 确保索引已初始化
        if self._index is None:
            self.get_index()
        
        # 检查 collection 是否存在
        if not hasattr(self, 'chroma_collection'):
            return documents, 0
        
        try:
            collection_count = self.chroma_collection.count()
            if collection_count == 0:
                # 如果 collection 为空，所有文档都需要处理
                return documents, 0
            
            # 检查每个文档是否已向量化
            documents_to_process = []
            already_vectorized_count = 0
            
            for doc in documents:
                file_path = doc.metadata.get("file_path", "")
                if not file_path:
                    # 如果没有 file_path，无法检查，需要处理
                    documents_to_process.append(doc)
                    continue
                
                # 查询该文件是否已有向量
                vector_ids = self._get_vector_ids_by_metadata(file_path)
                if vector_ids:
                    # 该文档已向量化，跳过
                    already_vectorized_count += 1
                    logger.debug(f"文档已向量化，跳过: {file_path}")
                else:
                    # 该文档未向量化，需要处理
                    documents_to_process.append(doc)
            
            if already_vectorized_count > 0:
                logger.info(
                    f"文档级断点续传: "
                    f"总文档数={len(documents)}, "
                    f"已向量化={already_vectorized_count}, "
                    f"待处理={len(documents_to_process)}"
                )
            
            return documents_to_process, already_vectorized_count
            
        except Exception as e:
            logger.warning(f"过滤已向量化文档失败: {e}，将处理所有文档")
            return documents, 0
    
    def preload_wikipedia_concepts(
        self,
        concept_keywords: List[str],
        lang: str = "zh",
        show_progress: bool = True
    ) -> int:
        """预加载核心概念的维基百科内容到索引
        
        Args:
            concept_keywords: 概念关键词列表（维基百科页面标题）
            lang: 语言代码（zh=中文, en=英文）
            show_progress: 是否显示进度
            
        Returns:
            成功索引的页面数量
            
        Examples:
            >>> index_manager.preload_wikipedia_concepts(
            ...     ["系统科学", "钱学森", "控制论"],
            ...     lang="zh"
            ... )
        """
        if not concept_keywords:
            print("⚠️  概念关键词列表为空")
            return 0
        
        try:
            from src.data_loader import load_documents_from_wikipedia
            
            if show_progress:
                print(f"📖 预加载 {len(concept_keywords)} 个维基百科概念...")
            
            logger.info(f"开始预加载维基百科概念: {concept_keywords}")
            
            # 加载维基百科页面
            wiki_docs = load_documents_from_wikipedia(
                pages=concept_keywords,
                lang=lang,
                auto_suggest=True,
                clean=True,
                show_progress=show_progress
            )
            
            if not wiki_docs:
                if show_progress:
                    print("⚠️  未找到任何维基百科内容")
                logger.warning("未找到任何维基百科内容")
                return 0
            
            # 构建索引
            self.build_index(wiki_docs, show_progress=show_progress)
            
            if show_progress:
                print(f"✅ 已索引 {len(wiki_docs)} 个维基百科页面")
            
            logger.info(f"成功预加载 {len(wiki_docs)} 个维基百科页面")
            
            return len(wiki_docs)
            
        except Exception as e:
            print(f"❌ 预加载维基百科失败: {e}")
            logger.error(f"预加载维基百科失败: {e}")
            return 0
    
    def close(self):
        """关闭索引管理器，释放资源
        
        显式关闭 Chroma 客户端连接，停止后台线程
        应该在应用关闭时调用此方法
        """
        try:
            logger.info("🔧 开始关闭索引管理器...")
            
            # 1. 清理 Chroma 客户端
            if hasattr(self, 'chroma_client') and self.chroma_client is not None:
                try:
                    # 尝试多种方式关闭客户端
                    client = self.chroma_client
                    
                    # 方法1: 尝试调用 close() 方法
                    if hasattr(client, 'close'):
                        client.close()
                        logger.info("✅ Chroma客户端已通过 close() 方法关闭")
                    # 方法2: 尝试调用 reset() 方法（某些版本支持）
                    elif hasattr(client, 'reset'):
                        client.reset()
                        logger.info("✅ Chroma客户端已通过 reset() 方法重置")
                    # 方法3: 尝试访问内部属性并关闭
                    elif hasattr(client, '_client'):
                        # 某些版本的 Chroma 可能有内部客户端
                        inner_client = getattr(client, '_client', None)
                        if inner_client and hasattr(inner_client, 'close'):
                            inner_client.close()
                            logger.info("✅ Chroma内部客户端已关闭")
                    
                    # 清理引用
                    self.chroma_client = None
                    logger.info("✅ Chroma客户端引用已清理")
                    
                except Exception as e:
                    logger.warning(f"⚠️  关闭 Chroma 客户端时出错: {e}")
                    # 即使出错，也要清理引用
                    self.chroma_client = None
            
            # 2. 清理其他引用
            if hasattr(self, 'chroma_collection'):
                self.chroma_collection = None
            if hasattr(self, 'vector_store'):
                self.vector_store = None
            if hasattr(self, 'storage_context'):
                self.storage_context = None
            if hasattr(self, '_index'):
                self._index = None
            
            # 3. 强制垃圾回收（可选，帮助清理线程）
            try:
                import gc
                gc.collect()
                logger.debug("✅ 已执行垃圾回收")
            except Exception as e:
                logger.debug(f"垃圾回收时出错: {e}")
            
            logger.info("✅ 索引管理器资源已释放")
            
        except Exception as e:
            logger.warning(f"⚠️  关闭索引管理器时出错: {e}")
            # 即使出错，也要尽可能清理引用
            try:
                self.chroma_client = None
                self.chroma_collection = None
                self.vector_store = None
                self.storage_context = None
                self._index = None
            except:
                pass
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        try:
            self.close()
        except Exception:
            # 析构函数中的异常应该被忽略
            pass


def create_index_from_directory(
    directory_path: str | Path,
    collection_name: Optional[str] = None,
    recursive: bool = True
) -> IndexManager:
    """从目录创建索引（便捷函数）
    
    Args:
        directory_path: 文档目录路径
        collection_name: 集合名称
        recursive: 是否递归加载
        
    Returns:
        IndexManager对象
    """
    from src.data_loader import load_documents_from_directory
    
    # 加载文档
    print(f"📂 从目录加载文档: {directory_path}")
    documents = load_documents_from_directory(directory_path, recursive=recursive)
    
    if not documents:
        print("⚠️  未找到任何文档")
        return IndexManager(collection_name=collection_name)
    
    # 创建索引管理器
    index_manager = IndexManager(collection_name=collection_name)
    
    # 构建索引
    index_manager.build_index(documents)
    
    return index_manager


def create_index_from_urls(
    urls: List[str],
    collection_name: Optional[str] = None
) -> IndexManager:
    """从URL列表创建索引（便捷函数）
    
    Args:
        urls: URL列表
        collection_name: 集合名称
        
    Returns:
        IndexManager对象
    """
    from src.data_loader import load_documents_from_urls
    
    # 加载文档
    print(f"🌐 从 {len(urls)} 个URL加载文档")
    documents = load_documents_from_urls(urls)
    
    if not documents:
        print("⚠️  未成功加载任何网页")
        return IndexManager(collection_name=collection_name)
    
    # 创建索引管理器
    index_manager = IndexManager(collection_name=collection_name)
    
    # 构建索引
    index_manager.build_index(documents)
    
    return index_manager


if __name__ == "__main__":
    # 测试代码
    print("=== 测试索引构建 ===\n")
    
    # 创建测试文档
    test_docs = [
        LlamaDocument(
            text="系统科学是研究系统的一般规律和方法的科学。",
            metadata={"title": "系统科学简介", "source": "test"}
        ),
        LlamaDocument(
            text="钱学森是中国系统科学的创建者之一，他提出了系统工程的理论体系。",
            metadata={"title": "钱学森与系统科学", "source": "test"}
        ),
    ]
    
    # 创建索引
    index_manager = IndexManager(collection_name="test_collection")
    index_manager.build_index(test_docs)
    
    # 测试搜索
    print("\n=== 测试搜索 ===")
    results = index_manager.search("钱学森", top_k=2)
    for i, result in enumerate(results, 1):
        print(f"\n结果 {i}:")
        print(f"相似度: {result['score']:.4f}")
        print(f"内容: {result['text']}")
    
    # 清理测试数据
    index_manager.clear_index()
    print("\n✅ 测试完成")

