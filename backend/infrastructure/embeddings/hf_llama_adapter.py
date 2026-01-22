"""
Hugging Face Inference API LlamaIndex 适配器

主要功能：
- 创建 LlamaIndex 兼容的 Embedding 适配器
- 提供同步和异步接口
"""

import asyncio
from typing import List

from backend.infrastructure.logger import get_logger
from backend.infrastructure.embeddings.hf_thread_pool import _get_or_create_executor

logger = get_logger('hf_llama_adapter')


def create_llama_index_adapter(embedding_instance):
    """创建 LlamaIndex 兼容的 Embedding 适配器
    
    Args:
        embedding_instance: HFInferenceEmbedding 实例
        
    Returns:
        LlamaIndex兼容的适配器包装器（继承自LlamaIndex BaseEmbedding）
        
    Raises:
        ImportError: 如果无法导入LlamaIndex BaseEmbedding
    """
    # 延迟导入，避免模块加载时出错
    LlamaBaseEmbedding = None
    try:
        from llama_index.core.embeddings.base import BaseEmbedding as LlamaBaseEmbedding
        logger.debug("✅ 成功导入 llama_index.core.embeddings.base.BaseEmbedding")
    except ImportError:
        try:
            from llama_index.embeddings.base import BaseEmbedding as LlamaBaseEmbedding
            logger.debug("✅ 成功导入 llama_index.embeddings.base.BaseEmbedding")
        except ImportError:
            try:
                from llama_index.embeddings.huggingface import HuggingFaceEmbedding
                for base_class in HuggingFaceEmbedding.__mro__:
                    if base_class.__name__ == 'BaseEmbedding' and 'embeddings' in base_class.__module__:
                        LlamaBaseEmbedding = base_class
                        logger.debug(f"✅ 通过MRO找到BaseEmbedding: {base_class.__module__}.{base_class.__name__}")
                        break
                
                if LlamaBaseEmbedding is None:
                    raise ImportError("无法在 HuggingFaceEmbedding 的 MRO 中找到 BaseEmbedding")
            except (ImportError, AttributeError) as e:
                error_msg = (
                    "无法导入LlamaIndex BaseEmbedding。"
                    "请确保已安装 llama-index 或 llama-index-core。"
                    f"错误详情: {e}"
                )
                logger.error(error_msg)
                raise ImportError(error_msg) from e
    
    if LlamaBaseEmbedding and LlamaBaseEmbedding.__name__ != 'BaseEmbedding':
        error_msg = (
            f"获取到的基类不是 BaseEmbedding，而是 {LlamaBaseEmbedding.__name__}。"
            f"这可能导致适配器需要实现额外的抽象方法。"
        )
        logger.warning(error_msg)
    
    # 动态创建继承LlamaBaseEmbedding的适配器类
    class LlamaIndexEmbeddingAdapter(LlamaBaseEmbedding):
        """LlamaIndex兼容的Embedding适配器包装器"""
        
        def __init__(self, embedding):
            model_name = embedding.get_model_name()
            try:
                super().__init__(model_name=model_name)
            except (TypeError, AttributeError):
                try:
                    super().__init__()
                except Exception:
                    pass
            
            object.__setattr__(self, '_embedding', embedding)
            if not hasattr(self, 'model_name') or self.model_name != model_name:
                try:
                    self.model_name = model_name
                except (AttributeError, ValueError):
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
            executor = _get_or_create_executor()
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(executor, self._embedding.get_query_embedding, query)
        
        async def _aget_text_embedding(self, text: str) -> List[float]:
            """生成单个文本向量（LlamaIndex接口，私有方法，异步）"""
            executor = _get_or_create_executor()
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(executor, self._embedding.get_text_embeddings, [text])
            return embeddings[0] if embeddings else []
        
        async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
            """批量生成文本向量（LlamaIndex接口，私有方法，异步）"""
            executor = _get_or_create_executor()
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(executor, self._embedding.get_text_embeddings, texts)
        
        def get_query_embedding(self, query: str) -> List[float]:
            """生成查询向量（公共方法，兼容LlamaIndex接口）"""
            return self._get_query_embedding(query)
        
        def get_text_embedding(self, text: str) -> List[float]:
            """生成单个文本向量（公共方法，兼容LlamaIndex接口）"""
            return self._get_text_embedding(text)
        
        def get_text_embedding_batch(self, texts: List[str], **kwargs) -> List[List[float]]:
            """批量生成文本向量（公共方法，兼容LlamaIndex接口）"""
            return self._get_text_embeddings(texts)
    
    try:
        adapter = LlamaIndexEmbeddingAdapter(embedding_instance)
    except TypeError as e:
        error_msg = (
            f"无法创建LlamaIndex适配器: {e}。"
            f"这可能是因为基类 {LlamaBaseEmbedding.__name__} 有未实现的抽象方法。"
        )
        logger.error(error_msg)
        raise TypeError(error_msg) from e
    
    if not isinstance(adapter, LlamaBaseEmbedding):
        error_msg = (
            f"创建的适配器不是LlamaIndex BaseEmbedding的实例。"
            f"类型: {type(adapter)}, 期望: {LlamaBaseEmbedding}"
        )
        logger.error(error_msg)
        raise TypeError(error_msg)
    
    logger.debug(f"✅ 成功创建LlamaIndex适配器: {type(adapter)}")
    return adapter
