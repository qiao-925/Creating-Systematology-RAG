"""
Embedding模型加载和管理工具
"""

import os
from pathlib import Path
from typing import Optional

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from src.config import config, get_gpu_device, is_gpu_available
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

