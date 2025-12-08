"""
Embedding模块：提供统一的向量化接口，支持本地模型和HF Inference API

主要功能：
- BaseEmbedding类：Embedding模型基类，定义统一接口
- LocalEmbedding类：本地HuggingFace模型适配器
- HFInferenceEmbedding类：Hugging Face Inference API适配器
- create_embedding()：工厂函数，创建Embedding实例
- 统一缓存管理：管理BaseEmbedding缓存
- 延迟导入支持，避免初始化时加载所有依赖

执行流程：
1. 延迟导入各个Embedding实现类
2. 通过工厂函数创建实例
3. 提供统一的向量化接口

特性：
- 统一的向量化接口
- 支持本地模型和HF Inference API
- 延迟导入机制
- 工厂模式创建实例
"""

# 延迟导入，避免初始化时加载所有依赖
# 使用时再导入：from src.infrastructure.embeddings.base import BaseEmbedding

from typing import Any

__all__ = [
    'BaseEmbedding',
    'LocalEmbedding',
    'HFInferenceEmbedding',
    'create_embedding',
]


def __getattr__(name: str) -> Any:
    """延迟导入支持"""
    if name == 'BaseEmbedding':
        from src.infrastructure.embeddings.base import BaseEmbedding
        return BaseEmbedding
    elif name == 'LocalEmbedding':
        from src.infrastructure.embeddings.local_embedding import LocalEmbedding
        return LocalEmbedding
    elif name == 'HFInferenceEmbedding':
        from src.infrastructure.embeddings.hf_inference_embedding import HFInferenceEmbedding
        return HFInferenceEmbedding
    elif name == 'create_embedding':
        from src.infrastructure.embeddings.factory import create_embedding
        return create_embedding
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

