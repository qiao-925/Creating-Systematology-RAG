"""
Hugging Face Inference API Embedding适配器：支持通过HF Inference Providers调用embedding模型

主要功能：
- HFInferenceEmbedding类：Hugging Face Inference API适配器，实现BaseEmbedding接口
- get_query_embedding()：通过HF Inference API生成查询向量
- get_text_embeddings()：通过HF Inference API批量生成文本向量

特性：
- 使用直接HTTP请求（requests）调用HF Inference API，提高透明度和可调试性
- 支持按量付费（PRO用户每月有$2.00免费额度）
- 统一的错误处理和重试机制
"""

import os
from typing import List, Optional
import time
import asyncio
import json

import requests
from requests.exceptions import RequestException

from backend.infrastructure.embeddings.base import BaseEmbedding
from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger
from backend.infrastructure.embeddings.hf_thread_pool import (
    register_embedding_instance,
    cleanup_hf_embedding_resources,
)
from backend.infrastructure.embeddings.hf_llama_adapter import create_llama_index_adapter
from backend.infrastructure.embeddings.hf_api_client import HFAPIClient

logger = get_logger('hf_inference_embedding')


class HFInferenceEmbedding(BaseEmbedding):
    """Hugging Face Inference API Embedding 适配器
    
    使用 Hugging Face Inference Providers 服务调用 embedding 模型
    支持按量付费，PRO 用户每月有 $2.00 免费额度
    """
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-base-zh-v1.5",
        api_key: Optional[str] = None,
    ):
        """初始化 HF Inference API Embedding
        
        Args:
            model_name: Hugging Face 模型名称（默认 BAAI/bge-base-zh-v1.5）
            api_key: Hugging Face API Token（从环境变量 HF_TOKEN 或配置读取）
        """
        self.model_name = model_name
        self._dimension: Optional[int] = None
        self._closed = False
        self._active_requests: set = set()  # 跟踪正在进行的请求
        
        # 获取 API key（优先级：参数 > 环境变量 > 配置）
        self.api_key = api_key or os.getenv("HF_TOKEN") or getattr(config, 'HF_TOKEN', None)
        
        if not self.api_key:
            raise ValueError(
                "HF_TOKEN 未设置。请设置环境变量 HF_TOKEN 或配置中的 HF_TOKEN。"
                "获取 Token: https://huggingface.co/settings/tokens"
            )
        
        # 构建 API URL 和 headers（使用直接 HTTP 请求）
        self.api_url = f"https://router.huggingface.co/hf-inference/models/{self.model_name}/pipeline/feature-extraction"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # 注册到全局实例集合，以便在退出时清理
        register_embedding_instance(self)
        
        # 创建 API 客户端
        self._api_client = HFAPIClient(
            api_url=self.api_url,
            headers=self.headers,
            model_name=self.model_name,
            closed=self._closed,
            active_requests=self._active_requests
        )
        
        # 缓存已知模型维度，避免维度检测时额外 API 调用
        self._cached_embed_dim = self._get_default_dimension(self.model_name)
        
        logger.info(f"📡 初始化HF Inference API Embedding: {self.model_name}")
    
    def _get_default_dimension(self, model_name: str) -> int:
        """根据模型名称获取默认维度"""
        model_lower = model_name.lower()
        if "qwen" in model_lower and ("0.6b" in model_lower or "8b" in model_lower):
            return 1024
        elif "bge" in model_lower:
            return 768 if "base" in model_lower else 384
        return 384  # 通用默认值
    
    def _make_request(self, texts: List[str]) -> List[List[float]]:
        """发起 API 请求（使用 API 客户端）
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        # 更新 API 客户端状态
        self._api_client._closed = self._closed
        return self._api_client.make_request(texts)
    
    def get_query_embedding(self, query: str) -> List[float]:
        """生成查询向量"""
        embeddings = self.get_text_embeddings([query])
        return embeddings[0]
    
    def get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量
        
        支持批量处理，自动分批以避免单次请求过大。
        由于 feature_extraction 一次只能处理一个文本，内部会逐个处理。
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表，每个文本对应一个向量
        """
        if not texts:
            return []
        
        # 分批处理，每批最多 100 个文本
        batch_size = 100
        total_batches = (len(texts) + batch_size - 1) // batch_size
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            if total_batches > 1:
                logger.debug(f"处理批次 {batch_num}/{total_batches} ({len(batch)} 个文本)")
            
            batch_embeddings = self._make_request(batch)
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    def get_embedding_dimension(self) -> int:
        """获取向量维度（确保总是返回有效值）"""
        if self._dimension is None:
            self._dimension = self._get_default_dimension(self.model_name)
            logger.debug(f"使用默认维度: {self._dimension}")
            try:
                test_embedding = self.get_query_embedding("test")
                detected_dim = len(test_embedding)
                if detected_dim != self._dimension:
                    logger.info(f"🔄 检测到实际维度 {detected_dim}，更新默认值 {self._dimension}")
                    self._dimension = detected_dim
            except Exception as e:
                logger.warning(f"⚠️  无法通过API获取维度，使用默认值: {e}")
        return self._dimension
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.model_name
    
    def close(self) -> None:
        """关闭实例，清理资源
        
        停止所有正在进行的请求，清理线程和连接。
        应该在应用退出时调用此方法。
        """
        if self._closed:
            return
        
        logger.info(f"🔧 开始关闭 HFInferenceEmbedding 实例: {self.model_name}")
        self._closed = True
        
        # 等待正在进行的请求完成（最多等待5秒）
        if self._active_requests:
            logger.debug(f"等待 {len(self._active_requests)} 个正在进行的请求完成...")
            start_wait = time.time()
            while self._active_requests and (time.time() - start_wait) < 5.0:
                time.sleep(0.1)
            
            if self._active_requests:
                logger.warning(f"⚠️  仍有 {len(self._active_requests)} 个请求未完成，强制关闭")
        
        # 清理引用
        self._active_requests.clear()
        logger.info(f"✅ HFInferenceEmbedding 实例已关闭: {self.model_name}")
    
    def __del__(self):
        """析构函数，确保资源被清理"""
        if not self._closed:
            try:
                self.close()
            except Exception:
                pass  # 析构函数中不应该抛出异常
    
    def get_llama_index_embedding(self):
        """获取LlamaIndex兼容的Embedding适配器
        
        Returns:
            LlamaIndex兼容的适配器包装器（继承自LlamaIndex BaseEmbedding）
            
        Raises:
            ImportError: 如果无法导入LlamaIndex BaseEmbedding
        """
        return create_llama_index_adapter(self)
