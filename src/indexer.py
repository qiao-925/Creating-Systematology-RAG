"""
索引构建模块
负责构建和管理向量索引，集成Chroma向量数据库
"""

import os
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict

import chromadb
from tqdm import tqdm
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
        
        # 打印数据库信息
        self._print_database_info()
        
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
        show_progress: bool = True
    ) -> VectorStoreIndex:
        """构建或更新索引（简化版）
        
        Args:
            documents: 文档列表
            show_progress: 是否显示进度
            
        Returns:
            VectorStoreIndex对象
        """
        start_time = time.time()
        
        if not documents:
            print("⚠️  没有文档可索引")
            return self.get_index()
        
        # 获取当前设备信息
        device = get_gpu_device()
        
        print(f"\n🔨 开始构建索引，共 {len(documents)} 个文档")
        print(f"   设备: {device}")
        logger.info(f"开始索引构建: {len(documents)}个文档, 设备: {device}")
        
        try:
            # 创建新索引
            if self._index is None:
                self._index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=self.storage_context,
                    show_progress=show_progress,
                )
            else:
                # 增量添加到现有索引
                self._index.insert_ref_docs(documents, show_progress=show_progress)
            
            # 统计信息
            elapsed = time.time() - start_time
            stats = self.get_stats()
            
            print(f"✅ 索引构建完成 (耗时: {elapsed:.2f}s, 文档数: {stats['document_count']})")
            logger.info(f"索引构建完成: {len(documents)}个文档, 耗时{elapsed:.2f}s")
            
            return self._index
            
        except Exception as e:
            print(f"❌ 索引构建失败: {e}")
            logger.error(f"索引构建失败: {e}")
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
    
    def _print_database_info(self):
        """打印数据库和collection的详细信息"""
        try:
            # 1. 列出所有collections
            try:
                all_collections = self.chroma_client.list_collections()
                print(f"\n📋 数据库中的Collections列表:")
                if all_collections:
                    for idx, coll in enumerate(all_collections, 1):
                        try:
                            coll_count = coll.count() if hasattr(coll, 'count') else 0
                            coll_name = coll.name if hasattr(coll, 'name') else str(coll)
                            print(f"   {idx}. {coll_name} - {coll_count} 个向量")
                            logger.info(f"Collection: {coll_name}, 向量数: {coll_count}")
                        except Exception as e:
                            coll_name = coll.name if hasattr(coll, 'name') else str(coll)
                            print(f"   {idx}. {coll_name} - 无法获取统计信息: {e}")
                else:
                    print("   (无collections)")
                    logger.info("数据库中暂无collections")
            except Exception as e:
                logger.warning(f"获取collections列表失败: {e}")
                print(f"   ⚠️  无法列出collections: {e}")
            
            # 2. 检查当前collection是否存在
            print(f"\n🔍 检查目标Collection: {self.collection_name}")
            try:
                existing_collection = self.chroma_client.get_collection(name=self.collection_name)
                collection_count = existing_collection.count()
                
                print(f"   ✅ Collection存在")
                print(f"   📊 向量总数: {collection_count}")
                logger.info(f"Collection '{self.collection_name}' 存在，向量数: {collection_count}")
                
                # 3. 获取collection的详细信息
                sample_data = None  # 初始化变量
                if collection_count > 0:
                    # 获取样本数据（最多10条）
                    sample_limit = min(10, collection_count)
                    try:
                        sample_data = existing_collection.peek(limit=sample_limit)
                        
                        # 统计metadata中的信息
                        file_paths = set()
                        repositories = set()
                        file_types = {}
                        
                        if sample_data and 'metadatas' in sample_data:
                            for metadata in sample_data['metadatas']:
                                if metadata:
                                    # 收集文件路径
                                    if 'file_path' in metadata:
                                        file_paths.add(metadata['file_path'])
                                    
                                    # 收集仓库信息
                                    if 'repository' in metadata:
                                        repositories.add(metadata['repository'])
                                    
                                    # 统计文件类型
                                    if 'file_name' in metadata:
                                        file_name = metadata['file_name']
                                        file_ext = Path(file_name).suffix.lower() if file_name else ''
                                        file_types[file_ext] = file_types.get(file_ext, 0) + 1
                        
                        # 打印统计信息
                        print(f"\n   📈 Collection统计信息:")
                        print(f"      • 向量数量: {collection_count}")
                        
                        if file_paths:
                            print(f"      • 唯一文件路径数: {len(file_paths)}")
                            if len(file_paths) <= 20:
                                print(f"      • 文件路径列表:")
                                for fp in sorted(list(file_paths))[:20]:
                                    print(f"        - {fp}")
                            else:
                                print(f"      • 文件路径列表（前20个）:")
                                for fp in sorted(list(file_paths))[:20]:
                                    print(f"        - {fp}")
                                print(f"        ... 还有 {len(file_paths) - 20} 个文件")
                        
                        if repositories:
                            print(f"      • 仓库列表:")
                            for repo in sorted(list(repositories)):
                                print(f"        - {repo}")
                        
                        if file_types:
                            print(f"      • 文件类型分布:")
                            for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
                                ext_display = ext if ext else "(无扩展名)"
                                print(f"        {ext_display}: {count} 个")
                        
                        # 打印样本metadata（前5条）
                        if sample_data and 'metadatas' in sample_data and sample_data['metadatas']:
                            print(f"\n   📄 样本数据（前5条）:")
                            for idx, metadata in enumerate(sample_data['metadatas'][:5], 1):
                                if metadata:
                                    print(f"      {idx}. Metadata:")
                                    for key, value in metadata.items():
                                        # 截断过长的值
                                        value_str = str(value)
                                        if len(value_str) > 100:
                                            value_str = value_str[:100] + "..."
                                        print(f"         {key}: {value_str}")
                                    
                                    # 如果有对应的文档ID
                                    if 'ids' in sample_data and idx <= len(sample_data['ids']):
                                        doc_id = sample_data['ids'][idx - 1]
                                        print(f"         id: {doc_id}")
                        
                        logger.info(
                            f"Collection详情: 向量数={collection_count}, "
                            f"文件数={len(file_paths)}, "
                            f"仓库数={len(repositories)}, "
                            f"文件类型={len(file_types)}"
                        )
                        
                    except Exception as e:
                        logger.warning(f"获取collection样本数据失败: {e}")
                        print(f"   ⚠️  无法获取样本数据: {e}")
                    
                    # 获取维度信息
                    try:
                        if existing_collection.metadata and 'embedding_dimension' in existing_collection.metadata:
                            dim = existing_collection.metadata['embedding_dimension']
                            print(f"   📏 Embedding维度: {dim}")
                            logger.info(f"Collection维度: {dim}")
                        elif sample_data and 'embeddings' in sample_data and sample_data['embeddings']:
                            dim = len(sample_data['embeddings'][0])
                            print(f"   📏 Embedding维度: {dim} (从样本数据检测)")
                            logger.info(f"Collection维度: {dim} (从样本数据检测)")
                    except Exception as e:
                        logger.debug(f"获取维度信息失败: {e}")
                else:
                    print(f"   ℹ️  Collection为空")
                    logger.info(f"Collection '{self.collection_name}' 为空")
                
            except Exception as e:
                # Collection不存在
                if "does not exist" in str(e) or "not found" in str(e).lower():
                    print(f"   ℹ️  Collection不存在，将创建新collection")
                    logger.info(f"Collection '{self.collection_name}' 不存在，将创建")
                else:
                    print(f"   ⚠️  检查collection时出错: {e}")
                    logger.warning(f"检查collection失败: {e}")
            
            print()  # 空行分隔
            
        except Exception as e:
            logger.error(f"打印数据库信息失败: {e}")
            print(f"⚠️  打印数据库信息失败: {e}")
    
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
            # 检查chroma_collection是否已初始化
            if not hasattr(self, 'chroma_collection') or self.chroma_collection is None:
                logger.warning("⚠️  chroma_collection未初始化，无法获取统计信息")
                print(f"⚠️  chroma_collection未初始化，无法获取统计信息")
                return {
                    "collection_name": self.collection_name,
                    "document_count": 0,
                    "embedding_model": self.embedding_model_name,
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "error": "chroma_collection未初始化"
                }
            
            count = self.chroma_collection.count()
            logger.debug(f"Collection '{self.collection_name}' 向量数量: {count}")
            
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "embedding_model": self.embedding_model_name,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
            }
        except AttributeError as e:
            error_msg = f"chroma_collection属性访问失败: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            return {
                "collection_name": self.collection_name,
                "document_count": 0,
                "embedding_model": self.embedding_model_name,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "error": str(e)
            }
        except Exception as e:
            error_msg = f"获取统计信息失败: {e}"
            logger.error(error_msg, exc_info=True)
            print(f"❌ {error_msg}")
            return {
                "collection_name": self.collection_name,
                "document_count": 0,
                "embedding_model": self.embedding_model_name,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "error": str(e)
            }
    
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

