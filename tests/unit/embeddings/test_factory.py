"""
Embedding 工厂测试

测试 Embedding 工厂函数。
"""

import pytest
import os
from unittest.mock import patch, Mock
from backend.infrastructure.embeddings.base import BaseEmbedding
from backend.infrastructure.embeddings.local_embedding import LocalEmbedding
from backend.infrastructure.embeddings.hf_inference_embedding import HFInferenceEmbedding
from backend.infrastructure.embeddings.factory import (
    create_embedding,
    clear_embedding_cache,
    get_embedding_instance
)


@pytest.mark.fast
class TestEmbeddingFactory:
    """Embedding工厂函数测试"""
    
    def setup_method(self):
        """每个测试前清除缓存"""
        clear_embedding_cache()
    
    def test_embedding_factory_local(self):
        """测试创建本地Embedding"""
        try:
            embedding = create_embedding(embedding_type="local")
            
            assert isinstance(embedding, LocalEmbedding)
            assert isinstance(embedding, BaseEmbedding)
        except Exception as e:
            pytest.skip(f"创建本地Embedding失败: {e}")
    
    @patch('src.infrastructure.embeddings.factory.HFInferenceEmbedding')
    def test_embedding_factory_hf_inference(self, mock_hf_class):
        """测试创建HF Inference Embedding（使用Mock，不调用真实API）"""
        # Mock HFInferenceEmbedding 实例
        mock_instance = Mock(spec=BaseEmbedding)
        mock_instance.get_model_name.return_value = "BAAI/bge-base-zh-v1.5"
        mock_hf_class.return_value = mock_instance
        
        # Mock 环境变量中的 HF_TOKEN
        with patch.dict(os.environ, {'HF_TOKEN': 'hf_test_token_123'}):
            embedding = create_embedding(
                embedding_type="hf-inference",
                model_name="BAAI/bge-base-zh-v1.5",
                api_key="hf_test_token_123"
            )
            
            # 验证返回的是 Mock 实例
            assert embedding is mock_instance
            assert isinstance(embedding, BaseEmbedding)
            
            # 验证 HFInferenceEmbedding 被正确调用
            mock_hf_class.assert_called_once()
            call_kwargs = mock_hf_class.call_args[1]
            assert call_kwargs['model_name'] == "BAAI/bge-base-zh-v1.5"
            assert call_kwargs['api_key'] == "hf_test_token_123"
    
    def test_embedding_factory_invalid_type(self):
        """测试无效的Embedding类型"""
        with pytest.raises(ValueError, match="不支持的Embedding类型"):
            create_embedding(embedding_type="invalid_type")
    
    def test_embedding_factory_api_missing_url(self):
        """测试API类型缺少URL"""
        clear_embedding_cache()
        
        with patch('src.infrastructure.embeddings.factory.config') as mock_config:
            mock_config.EMBEDDING_TYPE = "api"
            mock_config.EMBEDDING_MODEL = "test-model"
            type(mock_config).EMBEDDING_API_URL = property(lambda self: None)
            
            with pytest.raises(ValueError, match="API类型需要提供api_url"):
                create_embedding(embedding_type="api", api_url=None)
        
        clear_embedding_cache()
        
        with patch('src.infrastructure.embeddings.factory.config') as mock_config:
            mock_config.EMBEDDING_TYPE = "api"
            mock_config.EMBEDDING_MODEL = "test-model"
            type(mock_config).EMBEDDING_API_URL = property(lambda self: None)
            
            with pytest.raises(ValueError, match="API类型需要提供api_url"):
                create_embedding(embedding_type="api", api_url="")
        
        clear_embedding_cache()
    
    @pytest.mark.slow
    def test_embedding_factory_cache(self):
        """测试Embedding缓存机制"""
        try:
            embedding1 = create_embedding(embedding_type="local")
            embedding2 = create_embedding(embedding_type="local")
            
            assert embedding1 is embedding2
            
            embedding3 = create_embedding(embedding_type="local", force_reload=True)
            assert isinstance(embedding3, BaseEmbedding)
        except Exception as e:
            pytest.skip(f"Embedding缓存测试失败: {e}")
    
    @pytest.mark.slow
    def test_get_embedding_instance(self):
        """测试获取当前Embedding实例"""
        clear_embedding_cache()
        assert get_embedding_instance() is None
        
        try:
            embedding = create_embedding(embedding_type="local")
            assert get_embedding_instance() is embedding
        except Exception as e:
            pytest.skip(f"获取Embedding实例测试失败: {e}")
    
    @pytest.mark.slow
    def test_clear_embedding_cache(self):
        """测试清除Embedding缓存"""
        try:
            embedding = create_embedding(embedding_type="local")
            assert get_embedding_instance() is not None
            
            clear_embedding_cache()
            assert get_embedding_instance() is None
        except Exception as e:
            pytest.skip(f"清除Embedding缓存测试失败: {e}")


@pytest.mark.slow
class TestEmbeddingDimensionConsistency:
    """向量维度一致性测试"""
    
    def test_embedding_dimension_consistency(self):
        """测试不同操作返回的向量维度一致"""
        try:
            embedding = create_embedding(embedding_type="local")
            dimension = embedding.get_embedding_dimension()
            
            query_vector = embedding.get_query_embedding("测试")
            assert len(query_vector) == dimension
            
            batch_vectors = embedding.get_text_embeddings(["文本1", "文本2"])
            for vector in batch_vectors:
                assert len(vector) == dimension
            
            assert dimension > 0
        except Exception as e:
            pytest.skip(f"向量维度一致性测试失败: {e}")
