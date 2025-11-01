"""
本地Embedding模型适配器
封装HuggingFace本地模型，提供统一接口
"""

import os
from pathlib import Path
from typing import List, Optional
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from src.embeddings.base import BaseEmbedding
from src.config import config, get_gpu_device, is_gpu_available
from src.logger import setup_logger

logger = setup_logger('local_embedding')


class LocalEmbedding(BaseEmbedding):
    """本地HuggingFace模型适配器
    
    封装现有的HuggingFaceEmbedding逻辑，实现BaseEmbedding接口
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        embed_batch_size: Optional[int] = None,
        max_length: Optional[int] = None,
        cache_folder: Optional[str] = None,
    ):
        """初始化本地Embedding模型
        
        Args:
            model_name: 模型名称（默认使用配置）
            device: 设备（cuda/cpu，默认自动检测）
            embed_batch_size: 批处理大小（默认使用配置）
            max_length: 最大长度（默认使用配置）
            cache_folder: 缓存目录（默认~/.cache/huggingface）
        """
        self.model_name = model_name or config.EMBEDDING_MODEL
        self.device = device or get_gpu_device()
        self.embed_batch_size = embed_batch_size or config.EMBED_BATCH_SIZE
        self.max_length = max_length or config.EMBED_MAX_LENGTH
        self.cache_folder = cache_folder or str(Path.home() / ".cache" / "huggingface")
        
        # 配置HuggingFace环境
        self._setup_huggingface_env()
        
        # 加载模型
        self._load_model()
    
    def _setup_huggingface_env(self):
        """配置HuggingFace环境变量"""
        # 设置镜像地址
        if config.HF_ENDPOINT:
            os.environ['HF_ENDPOINT'] = config.HF_ENDPOINT
            os.environ['HUGGINGFACE_HUB_ENDPOINT'] = config.HF_ENDPOINT
            os.environ['HF_HUB_ENDPOINT'] = config.HF_ENDPOINT
            logger.info(f"🌐 使用 HuggingFace 镜像: {config.HF_ENDPOINT}")
        
        # 设置离线模式
        if config.HF_OFFLINE_MODE:
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            logger.info(f"📴 启用离线模式")
        else:
            os.environ.pop('HF_HUB_OFFLINE', None)
            os.environ.pop('TRANSFORMERS_OFFLINE', None)
    
    def _load_model(self):
        """加载模型"""
        logger.info(f"📦 加载本地 Embedding 模型: {self.model_name}")
        
        # 输出设备信息
        if self.device.startswith("cuda") and is_gpu_available():
            import torch
            device_name = torch.cuda.get_device_name()
            logger.info(f"✅ 使用GPU加速: {self.device} ({device_name})")
        else:
            logger.warning("⚠️  使用CPU模式（性能较慢）")
        
        # 构建模型参数
        model_kwargs = {
            "trust_remote_code": True,
            "cache_folder": self.cache_folder,
        }
        
        # 创建HuggingFaceEmbedding实例
        self._model = HuggingFaceEmbedding(
            model_name=self.model_name,
            embed_batch_size=self.embed_batch_size,
            max_length=self.max_length,
            **model_kwargs
        )
        
        # 移动到指定设备
        try:
            if self.device.startswith("cuda") and is_gpu_available():
                if hasattr(self._model, '_model') and hasattr(self._model._model, 'to'):
                    self._model._model = self._model._model.to(self.device)
                    logger.info(f"✅ 模型已移动到GPU: {self.device}")
                elif hasattr(self._model, 'model') and hasattr(self._model.model, 'to'):
                    self._model.model = self._model.model.to(self.device)
                    logger.info(f"✅ 模型已移动到GPU: {self.device}")
        except Exception as e:
            logger.warning(f"⚠️  无法将模型移动到GPU: {e}")
        
        logger.info(f"✅ 模型加载完成")
        logger.info(f"   批处理大小: {self.embed_batch_size}")
        logger.info(f"   最大长度: {self.max_length}")
    
    def get_query_embedding(self, query: str) -> List[float]:
        """生成查询向量"""
        return self._model.get_query_embedding(query)
    
    def get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量"""
        return self._model.get_text_embedding_batch(texts)
    
    def get_embedding_dimension(self) -> int:
        """获取向量维度"""
        # 生成一个测试向量来获取维度
        test_embedding = self.get_query_embedding("test")
        return len(test_embedding)
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.model_name
    
    def get_llama_index_embedding(self) -> HuggingFaceEmbedding:
        """获取底层的LlamaIndex Embedding实例
        
        用于向后兼容，直接传递给LlamaIndex组件
        
        Returns:
            HuggingFaceEmbedding实例
        """
        return self._model

