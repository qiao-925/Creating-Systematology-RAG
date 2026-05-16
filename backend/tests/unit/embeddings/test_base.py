"""
BaseEmbedding 接口测试

测试 BaseEmbedding 抽象接口。
"""

import pytest
from backend.infrastructure.embeddings.base import BaseEmbedding


@pytest.mark.fast
class TestBaseEmbedding:
    """BaseEmbedding接口测试"""
    
    def test_base_embedding_interface(self):
        """测试BaseEmbedding接口定义"""
        assert hasattr(BaseEmbedding, 'get_query_embedding')
        assert hasattr(BaseEmbedding, 'get_text_embeddings')
        assert hasattr(BaseEmbedding, 'get_embedding_dimension')
        assert hasattr(BaseEmbedding, 'get_model_name')
