"""
本地Embedding模型适配器：封装HuggingFace本地模型，提供统一接口

主要功能：
- LocalEmbedding类：本地HuggingFace模型适配器，实现BaseEmbedding接口
- get_query_embedding()：生成查询向量
- get_text_embeddings()：批量生成文本向量

执行流程：
1. 初始化HuggingFaceEmbedding模型
2. 配置GPU设备（如果可用）
3. 执行向量化操作
4. 返回向量结果

特性：
- 支持本地模型加载
- GPU加速支持
- 批量处理优化
- 完整的错误处理
"""

import os
from pathlib import Path
from typing import List, Optional

from backend.infrastructure.embeddings.base import BaseEmbedding
from backend.infrastructure.config import config, get_gpu_device
from backend.infrastructure.logger import get_logger

logger = get_logger('local_embedding')


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
        logger.info("🖥️  使用 CPU 模式")

        # 构建模型参数
        model_kwargs = {
            "trust_remote_code": True,
            "cache_folder": self.cache_folder,
        }

        # 创建HuggingFaceEmbedding实例
        try:
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        except ImportError as e:
            raise ImportError(
                "LocalEmbedding 需要安装可选依赖 `llama-index-embeddings-huggingface`（以及其底层依赖如 torch/sentence-transformers）。\n"
                "请运行：`uv sync --extra local` 或 `pip install .[local]`。"
            ) from e

        self._model = HuggingFaceEmbedding(
            model_name=self.model_name,
            embed_batch_size=self.embed_batch_size,
            max_length=self.max_length,
            **model_kwargs
        )

        logger.info("✅ 模型加载完成")
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
    
    def get_llama_index_embedding(self):
        """获取底层LlamaIndex兼容的Embedding实例
        
        Returns:
            HuggingFaceEmbedding: LlamaIndex兼容的Embedding实例
        """
        return self._model

