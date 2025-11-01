"""
Embedding模块
提供统一的向量化接口，支持本地模型和API模型
"""

# 延迟导入，避免初始化时加载所有依赖
# 使用时再导入：from src.embeddings.base import BaseEmbedding

__all__ = [
    'BaseEmbedding',
    'LocalEmbedding',
    'APIEmbedding',
    'create_embedding',
]


def __getattr__(name):
    """延迟导入支持"""
    if name == 'BaseEmbedding':
        from src.embeddings.base import BaseEmbedding
        return BaseEmbedding
    elif name == 'LocalEmbedding':
        from src.embeddings.local_embedding import LocalEmbedding
        return LocalEmbedding
    elif name == 'APIEmbedding':
        from src.embeddings.api_embedding import APIEmbedding
        return APIEmbedding
    elif name == 'create_embedding':
        from src.embeddings.factory import create_embedding
        return create_embedding
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

