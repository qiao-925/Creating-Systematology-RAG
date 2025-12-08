"""
Hugging Face Inference API Embedding适配器：支持通过HF Inference Providers调用embedding模型

主要功能：
- HFInferenceEmbedding类：Hugging Face Inference API适配器，实现BaseEmbedding接口
- get_query_embedding()：通过HF Inference API生成查询向量
- get_text_embeddings()：通过HF Inference API批量生成文本向量

特性：
- 使用官方huggingface_hub SDK
- 支持按量付费（PRO用户每月有$2.00免费额度）
- 统一的错误处理和重试机制
"""

import os
from typing import List, Optional
import time
import asyncio

from huggingface_hub import InferenceClient

from src.infrastructure.embeddings.base import BaseEmbedding
from src.infrastructure.config import config
from src.infrastructure.logger import get_logger

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
        
        # 获取 API key（优先级：参数 > 环境变量 > 配置）
        self.api_key = api_key or os.getenv("HF_TOKEN") or getattr(config, 'HF_TOKEN', None)
        
        if not self.api_key:
            raise ValueError(
                "HF_TOKEN 未设置。请设置环境变量 HF_TOKEN 或配置中的 HF_TOKEN。"
                "获取 Token: https://huggingface.co/settings/tokens"
            )
        
        # 初始化官方 SDK（使用新模式）
        self.client = InferenceClient(
            provider="hf-inference",
            api_key=self.api_key,
        )
        
        logger.info(f"📡 初始化 Hugging Face Inference API Embedding: {self.model_name}")
    
    def _get_default_dimension(self, model_name: str) -> int:
        """根据模型名称获取默认维度"""
        model_lower = model_name.lower()
        if "qwen" in model_lower and ("0.6b" in model_lower or "8b" in model_lower):
            return 1024
        elif "bge" in model_lower:
            return 768 if "base" in model_lower else 384
        return 384  # 通用默认值
    
    def _make_request(self, texts: List[str], retry_count: int = 0) -> List[List[float]]:
        """发起 API 请求（带重试机制）
        
        使用 HuggingFace Inference API 的 feature_extraction 方法生成向量。
        注意：feature_extraction 一次只能处理一个文本，需要逐个处理。
        
        Args:
            texts: 文本列表
            retry_count: 当前重试次数
            
        Returns:
            向量列表
            
        Raises:
            RuntimeError: API 调用失败
        """
        if retry_count > 0:
            logger.warning(f"⚠️  重试请求 ({retry_count}/3): 模型={self.model_name}, 文本数量={len(texts)}")
        else:
            logger.debug(f"📤 HF Inference API 请求: 模型={self.model_name}, 文本数量={len(texts)}")
        
        try:
            results = []
            total = len(texts)
            
            # feature_extraction 一次只能处理一个文本，逐个处理
            for idx, text in enumerate(texts):
                embedding = self.client.feature_extraction(
                    text,
                    model=self.model_name,
                )
                
                # 转换为列表格式
                if isinstance(embedding, list):
                    results.append(embedding)
                elif hasattr(embedding, '__iter__') and not isinstance(embedding, str):
                    results.append(list(embedding))
                else:
                    results.append([float(embedding)])
                
                # 批量处理时显示进度
                if total > 1 and (idx + 1) % 10 == 0:
                    logger.debug(f"   进度: {idx + 1}/{total}")
            
            if total > 1:
                logger.debug(f"📥 批量处理完成: {len(results)}/{total} 个文本")
            
            return results
                    
        except Exception as e:
            # 统一错误处理：全部重试
            return self._handle_request_error(e, texts, retry_count)
    
    def _handle_request_error(
        self,
        error: Exception,
        texts: List[str],
        retry_count: int
    ) -> List[List[float]]:
        """处理 API 请求错误（统一重试策略）
        
        Args:
            error: 捕获的异常
            texts: 请求的文本列表
            retry_count: 当前重试次数
            
        Returns:
            向量列表（重试成功时）
            
        Raises:
            RuntimeError: 重试次数用尽
        """
        max_retries = 3
        
        if retry_count < max_retries:
            wait_time = (retry_count + 1) * 1.0
            logger.warning(
                f"❌ API 请求失败: {error.__class__.__name__}: {str(error)}。"
                f"{wait_time:.1f}秒后重试 ({retry_count + 1}/{max_retries})"
            )
            time.sleep(wait_time)
            return self._make_request(texts, retry_count + 1)
        else:
            logger.error(f"❌ API 调用失败（已重试 {max_retries} 次）")
            raise RuntimeError(
                f"Hugging Face Inference API 调用失败（模型: {self.model_name}）: {error}"
            ) from error
    
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
    
    def get_llama_index_embedding(self):
        """获取LlamaIndex兼容的Embedding适配器
        
        Returns:
            LlamaIndex兼容的适配器包装器（继承自LlamaIndex BaseEmbedding）
            
        Raises:
            ImportError: 如果无法导入LlamaIndex BaseEmbedding
        """
        # 延迟导入，避免模块加载时出错
        # 优先直接导入 BaseEmbedding（而不是通过 HuggingFaceEmbedding 获取）
        LlamaBaseEmbedding = None
        try:
            from llama_index.core.embeddings.base import BaseEmbedding as LlamaBaseEmbedding
            logger.debug("✅ 成功导入 llama_index.core.embeddings.base.BaseEmbedding")
        except ImportError:
            try:
                from llama_index.embeddings.base import BaseEmbedding as LlamaBaseEmbedding
                logger.debug("✅ 成功导入 llama_index.embeddings.base.BaseEmbedding")
            except ImportError:
                # 如果直接导入失败，尝试通过 HuggingFaceEmbedding 的 MRO 找到 BaseEmbedding
                try:
                    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
                    # 通过 MRO 找到 BaseEmbedding（而不是直接取 __bases__[0]）
                    for base_class in HuggingFaceEmbedding.__mro__:
                        if base_class.__name__ == 'BaseEmbedding' and 'embeddings' in base_class.__module__:
                            LlamaBaseEmbedding = base_class
                            logger.debug(f"✅ 通过MRO找到BaseEmbedding: {base_class.__module__}.{base_class.__name__}")
                            break
                    
                    if LlamaBaseEmbedding is None:
                        raise ImportError("无法在 HuggingFaceEmbedding 的 MRO 中找到 BaseEmbedding")
                except (ImportError, AttributeError) as e:
                    # 如果都失败，抛出错误而不是返回不兼容的对象
                    error_msg = (
                        "无法导入LlamaIndex BaseEmbedding。"
                        "请确保已安装 llama-index 或 llama-index-core。"
                        f"错误详情: {e}"
                    )
                    logger.error(error_msg)
                    raise ImportError(error_msg) from e
        
        # 验证获取到的确实是 BaseEmbedding（不是 MultiModalEmbedding 或其他）
        if LlamaBaseEmbedding and LlamaBaseEmbedding.__name__ != 'BaseEmbedding':
            error_msg = (
                f"获取到的基类不是 BaseEmbedding，而是 {LlamaBaseEmbedding.__name__}。"
                f"这可能导致适配器需要实现额外的抽象方法。"
            )
            logger.warning(error_msg)
        
        # 动态创建继承LlamaBaseEmbedding的适配器类
        class LlamaIndexEmbeddingAdapter(LlamaBaseEmbedding):
            """LlamaIndex兼容的Embedding适配器包装器"""
            
            def __init__(self, embedding: HFInferenceEmbedding):
                # 先调用父类初始化（Pydantic 模型需要先初始化）
                model_name = embedding.get_model_name()
                try:
                    # 尝试使用 model_name 参数初始化
                    super().__init__(model_name=model_name)
                except (TypeError, AttributeError) as e:
                    try:
                        # 尝试无参数初始化
                        super().__init__()
                    except Exception as init_error:
                        # 如果父类初始化失败，记录警告但继续
                        logger.debug(f"父类初始化失败: {init_error}")
                        # 即使初始化失败，也继续（可能不需要参数）
                        pass
                
                # 父类初始化后再设置属性（使用 object.__setattr__ 绕过 Pydantic 验证）
                # 这样可以避免 Pydantic 的字段验证问题
                object.__setattr__(self, '_embedding', embedding)
                # model_name 可能已经在 super().__init__() 中设置了，如果没有则设置
                if not hasattr(self, 'model_name') or self.model_name != model_name:
                    try:
                        self.model_name = model_name
                    except (AttributeError, ValueError):
                        # 如果 Pydantic 不允许直接设置，使用 object.__setattr__
                        object.__setattr__(self, 'model_name', model_name)
            
            def _get_query_embedding(self, query: str) -> List[float]:
                """生成查询向量（LlamaIndex接口，私有方法，同步）"""
                return self._embedding.get_query_embedding(query)
            
            def _get_text_embedding(self, text: str) -> List[float]:
                """生成单个文本向量（LlamaIndex接口，私有方法，同步）"""
                embeddings = self._embedding.get_text_embeddings([text])
                return embeddings[0] if embeddings else []
            
            def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
                """批量生成文本向量（LlamaIndex接口，私有方法，同步）"""
                return self._embedding.get_text_embeddings(texts)
            
            async def _aget_query_embedding(self, query: str) -> List[float]:
                """生成查询向量（LlamaIndex接口，私有方法，异步）"""
                # 异步包装同步调用
                return await asyncio.to_thread(self._embedding.get_query_embedding, query)
            
            async def _aget_text_embedding(self, text: str) -> List[float]:
                """生成单个文本向量（LlamaIndex接口，私有方法，异步）"""
                # 异步包装同步调用
                embeddings = await asyncio.to_thread(self._embedding.get_text_embeddings, [text])
                return embeddings[0] if embeddings else []
            
            async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
                """批量生成文本向量（LlamaIndex接口，私有方法，异步）"""
                # 异步包装同步调用
                return await asyncio.to_thread(self._embedding.get_text_embeddings, texts)
            
            def get_query_embedding(self, query: str) -> List[float]:
                """生成查询向量（公共方法，兼容LlamaIndex接口）"""
                return self._get_query_embedding(query)
            
            def get_text_embedding(self, text: str) -> List[float]:
                """生成单个文本向量（公共方法，兼容LlamaIndex接口）"""
                return self._get_text_embedding(text)
            
            def get_text_embedding_batch(self, texts: List[str], **kwargs) -> List[List[float]]:
                """批量生成文本向量（公共方法，兼容LlamaIndex接口）
                
                Args:
                    texts: 文本列表
                    **kwargs: 额外参数（如 show_progress），会被忽略
                """
                return self._get_text_embeddings(texts)
        
        try:
            adapter = LlamaIndexEmbeddingAdapter(self)
        except TypeError as e:
            # 如果创建适配器失败（可能是抽象方法未实现），提供更详细的错误信息
            error_msg = (
                f"无法创建LlamaIndex适配器: {e}。"
                f"这可能是因为基类 {LlamaBaseEmbedding.__name__} 有未实现的抽象方法。"
                f"请检查是否需要实现额外的抽象方法。"
            )
            logger.error(error_msg)
            raise TypeError(error_msg) from e
        
        # 验证适配器确实是BaseEmbedding的实例
        if not isinstance(adapter, LlamaBaseEmbedding):
            error_msg = (
                f"创建的适配器不是LlamaIndex BaseEmbedding的实例。"
                f"类型: {type(adapter)}, 期望: {LlamaBaseEmbedding}"
            )
            logger.error(error_msg)
            raise TypeError(error_msg)
        
        logger.debug(f"✅ 成功创建LlamaIndex适配器: {type(adapter)}")
        return adapter


class _SimpleAdapter:
    """简单的适配器包装器（当无法导入LlamaIndex BaseEmbedding时使用）"""
    
    def __init__(self, embedding: HFInferenceEmbedding):
        self._embedding = embedding
        self.model_name = embedding.get_model_name()
    
    def get_query_embedding(self, query: str) -> List[float]:
        return self._embedding.get_query_embedding(query)
    
    def get_text_embedding(self, text: str) -> List[float]:
        embeddings = self._embedding.get_text_embeddings([text])
        return embeddings[0] if embeddings else []
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """生成查询向量（LlamaIndex接口，私有方法）"""
        return self._embedding.get_query_embedding(query)
    
    def _get_text_embedding(self, text: str) -> List[float]:
        """生成单个文本向量（LlamaIndex接口，私有方法）"""
        embeddings = self._embedding.get_text_embeddings([text])
        return embeddings[0] if embeddings else []
    
    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量（LlamaIndex接口，私有方法）"""
        return self._embedding.get_text_embeddings(texts)
    
    def get_query_embedding(self, query: str) -> List[float]:
        """生成查询向量（公共方法，兼容LlamaIndex接口）"""
        return self._get_query_embedding(query)
    
    def get_text_embedding(self, text: str) -> List[float]:
        """生成单个文本向量（公共方法，兼容LlamaIndex接口）"""
        return self._get_text_embedding(text)
    
    def get_text_embedding_batch(self, texts: List[str], **kwargs) -> List[List[float]]:
        """批量生成文本向量（公共方法，兼容LlamaIndex接口）
        
        Args:
            texts: 文本列表
            **kwargs: 额外参数（如 show_progress），会被忽略
        """
        return self._get_text_embeddings(texts)
