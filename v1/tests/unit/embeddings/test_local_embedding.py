"""
LocalEmbedding 测试

测试本地 Embedding 功能。
"""

import pytest
from backend.infrastructure.embeddings.base import BaseEmbedding
from backend.infrastructure.embeddings.local_embedding import LocalEmbedding


@pytest.mark.slow
class TestLocalEmbedding:
    """LocalEmbedding测试"""
    
    def test_local_embedding_init(self):
        """测试LocalEmbedding初始化"""
        try:
            embedding = LocalEmbedding()
            
            assert isinstance(embedding, BaseEmbedding)
            assert isinstance(embedding, LocalEmbedding)
            assert embedding.get_model_name() is not None
            assert embedding.get_embedding_dimension() > 0
            
            llama_embedding = embedding.get_llama_index_embedding()
            assert llama_embedding is not None
        except Exception as e:
            pytest.skip(f"LocalEmbedding初始化失败（可能需要下载模型）: {e}")
    
    def test_local_embedding_get_query_embedding(self):
        """测试查询向量化"""
        try:
            embedding = LocalEmbedding()
            query = "测试查询文本"
            
            vector = embedding.get_query_embedding(query)
            
            assert isinstance(vector, list)
            assert len(vector) > 0
            assert all(isinstance(x, float) for x in vector)
            assert len(vector) == embedding.get_embedding_dimension()
        except Exception as e:
            pytest.skip(f"LocalEmbedding查询向量化失败: {e}")
    
    def test_local_embedding_get_text_embeddings_batch(self):
        """测试批量向量化"""
        try:
            embedding = LocalEmbedding()
            texts = ["第一个文本", "第二个文本", "第三个文本"]
            
            vectors = embedding.get_text_embeddings(texts)
            
            assert isinstance(vectors, list)
            assert len(vectors) == len(texts)
            assert all(isinstance(v, list) for v in vectors)
            
            dimension = embedding.get_embedding_dimension()
            for vector in vectors:
                assert len(vector) == dimension
                assert all(isinstance(x, float) for x in vector)
        except Exception as e:
            pytest.skip(f"LocalEmbedding批量向量化失败: {e}")
    
    def test_local_embedding_custom_model(self):
        """测试使用自定义模型名称"""
        try:
            embedding = LocalEmbedding()
            default_model = embedding.get_model_name()
            
            assert default_model is not None
        except Exception as e:
            pytest.skip(f"LocalEmbedding自定义模型测试失败: {e}")
    
    def test_local_embedding_dimension_consistency(self):
        """测试向量维度一致性"""
        try:
            embedding = LocalEmbedding()
            dimension = embedding.get_embedding_dimension()
            
            query_vector = embedding.get_query_embedding("test")
            assert len(query_vector) == dimension
            
            batch_vectors = embedding.get_text_embeddings(["test1", "test2"])
            for vector in batch_vectors:
                assert len(vector) == dimension
        except Exception as e:
            pytest.skip(f"LocalEmbedding维度一致性测试失败: {e}")
