"""
Hugging Face Inference API Embedding 适配器
支持通过 HF Inference Providers 调用 embedding 模型
使用官方 huggingface_hub SDK
"""

import os
from typing import List, Optional
import time

from huggingface_hub import InferenceClient

from src.embeddings.base import BaseEmbedding
from src.config import config
from src.logger import setup_logger

logger = setup_logger('hf_inference_embedding')


class HFInferenceEmbedding(BaseEmbedding):
    """Hugging Face Inference API Embedding 适配器
    
    使用 Hugging Face Inference Providers 服务调用 embedding 模型
    支持按量付费，PRO 用户每月有 $2.00 免费额度
    """
    
    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-Embedding-0.6B",
        api_key: Optional[str] = None,
        provider: str = "hf-inference",
        dimension: Optional[int] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """初始化 HF Inference API Embedding
        
        Args:
            model_name: Hugging Face 模型名称（默认 Qwen/Qwen3-Embedding-0.6B）
            api_key: Hugging Face API Token（从环境变量 HF_TOKEN 或配置读取）
            provider: Inference Provider（默认 hf-inference）
            dimension: 向量维度（自动检测，如果提供则用于验证）
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv("HF_TOKEN") or getattr(config, 'HF_TOKEN', None)
        self.provider = provider
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._dimension = dimension
        
        if not self.api_key:
            raise ValueError(
                "HF_TOKEN 未设置。请设置环境变量 HF_TOKEN 或配置中的 HF_TOKEN。"
                "获取 Token: https://huggingface.co/settings/tokens"
            )
        
        # 初始化官方 SDK
        self.client = InferenceClient(
            provider=self.provider,
            api_key=self.api_key,
        )
        
        logger.info(f"📡 初始化 Hugging Face Inference API Embedding")
        logger.info(f"   模型: {self.model_name}")
        logger.info(f"   Provider: {self.provider}")
        
        # 验证 API 并获取维度
        self._validate_and_get_dimension()
    
    def _validate_and_get_dimension(self):
        """验证 API 可用性并获取向量维度"""
        try:
            # 使用测试文本获取维度
            test_embedding = self._make_request(["test"])
            if test_embedding:
                self._dimension = len(test_embedding[0])
                logger.info(f"✅ API 连接正常，向量维度: {self._dimension}")
            else:
                raise ValueError("API 返回空结果")
        except Exception as e:
            logger.warning(f"⚠️  API 验证失败: {e}")
            if self._dimension is None:
                # Qwen3-Embedding-0.6B 的默认维度是 1024
                # 如果无法检测，使用模型特定的默认值
                if "qwen" in self.model_name.lower() and "0.6b" in self.model_name.lower():
                    default_dim = 1024
                elif "qwen" in self.model_name.lower() and "8b" in self.model_name.lower():
                    default_dim = 1024
                else:
                    default_dim = 384  # 其他模型的通用默认值
                logger.warning(f"⚠️  无法自动检测维度，将使用默认值 {default_dim}（基于模型名称推断）")
                self._dimension = default_dim
    
    def _make_request(self, texts: List[str], retry_count: int = 0) -> List[List[float]]:
        """发起 API 请求（带重试机制）
        
        Args:
            texts: 文本列表
            retry_count: 当前重试次数
            
        Returns:
            向量列表
            
        Raises:
            RuntimeError: API 调用失败
        """
        try:
            # 使用官方 SDK 的 feature_extraction 方法
            # SDK 的 feature_extraction 一次只能处理一个文本，需要逐个处理
            results = []
            for text in texts:
                embedding = self.client.feature_extraction(
                    text,
                    model=self.model_name,
                )
                # 确保返回的是列表格式
                if isinstance(embedding, list):
                    results.append(embedding)
                elif hasattr(embedding, '__iter__') and not isinstance(embedding, str):
                    # 如果是可迭代对象（如 numpy array），转换为列表
                    results.append(list(embedding))
                else:
                    # 单个值的情况（不太可能，但处理一下）
                    results.append([float(embedding)])
            
            return results
                    
        except Exception as e:
            # 处理模型加载中的情况（503 错误）
            error_str = str(e).lower()
            if "503" in error_str or "loading" in error_str or "model" in error_str:
                if retry_count < self.max_retries:
                    wait_seconds = self.retry_delay * (retry_count + 1)
                    logger.info(f"⏳ 模型正在加载，等待 {wait_seconds} 秒后重试...")
                    time.sleep(wait_seconds)
                    return self._make_request(texts, retry_count + 1)
                else:
                    raise RuntimeError("模型加载超时，请稍后重试")
            
            # 其他错误，使用重试机制
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (retry_count + 1)  # 指数退避
                logger.warning(
                    f"⚠️  API 调用失败，{wait_time}秒后重试 "
                    f"({retry_count + 1}/{self.max_retries}): {e}"
                )
                time.sleep(wait_time)
                return self._make_request(texts, retry_count + 1)
            else:
                logger.error(f"❌ API 调用失败（已重试{self.max_retries}次）: {e}")
                raise RuntimeError(f"Hugging Face Inference API 调用失败: {e}")
    
    def get_query_embedding(self, query: str) -> List[float]:
        """生成查询向量"""
        embeddings = self.get_text_embeddings([query])
        return embeddings[0]
    
    def get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量
        
        支持批量处理，自动分批以避免单次请求过大
        """
        if not texts:
            return []
        
        # HF API 通常支持批量处理，但建议每批不超过 100 个文本
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.debug(f"处理 embedding 批次: {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}")
            
            batch_embeddings = self._make_request(batch)
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    def get_embedding_dimension(self) -> int:
        """获取向量维度"""
        if self._dimension is None:
            # 如果未设置，尝试获取
            test_embedding = self.get_query_embedding("test")
            self._dimension = len(test_embedding)
        return self._dimension
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.model_name

