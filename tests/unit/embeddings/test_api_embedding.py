"""
APIEmbedding 测试

测试 API Embedding 功能。
"""

import pytest
from unittest.mock import Mock, patch
from src.infrastructure.embeddings.base import BaseEmbedding
from src.infrastructure.embeddings.hf_inference_embedding import HFInferenceEmbedding


@pytest.mark.fast
class TestAPIEmbedding:
    """APIEmbedding测试"""
    
    def test_api_embedding_init(self):
        """测试HFInferenceEmbedding初始化"""
        model_name = "test-model"
        dimension = 768
        api_key = "test-token-123"
        
        embedding = HFInferenceEmbedding(
            model_name=model_name,
            dimension=dimension,
            api_key=api_key
        )
        
        assert isinstance(embedding, BaseEmbedding)
        assert isinstance(embedding, HFInferenceEmbedding)
        assert embedding.model_name == model_name
        assert embedding.get_embedding_dimension() == dimension
        assert embedding.get_model_name() == model_name
    
    @patch('src.infrastructure.embeddings.hf_inference_embedding.InferenceClient')
    def test_api_embedding_get_query_embedding(self, mock_client_class):
        """测试API查询向量化（Mock）"""
        mock_client = Mock()
        mock_client.feature_extraction.return_value = [[0.1] * 768]
        mock_client_class.return_value = mock_client
        
        embedding = HFInferenceEmbedding(
            model_name="test-model",
            dimension=768,
            api_key="test-token"
        )
        
        vector = embedding.get_query_embedding("测试查询")
        
        assert isinstance(vector, list)
        assert len(vector) == 768
        assert all(isinstance(x, float) for x in vector)
        
        mock_client.feature_extraction.assert_called_once()
    
    @patch('src.infrastructure.embeddings.hf_inference_embedding.InferenceClient')
    def test_api_embedding_get_text_embeddings_batch(self, mock_client_class):
        """测试API批量向量化（Mock）"""
        mock_client = Mock()
        mock_client.feature_extraction.return_value = [[0.1] * 768, [0.2] * 768, [0.3] * 768]
        mock_client_class.return_value = mock_client
        
        embedding = HFInferenceEmbedding(
            model_name="test-model",
            dimension=768,
            api_key="test-token"
        )
        
        texts = ["文本1", "文本2", "文本3"]
        vectors = embedding.get_text_embeddings(texts)
        
        assert isinstance(vectors, list)
        assert len(vectors) == len(texts)
        assert all(len(v) == 768 for v in vectors)
    
    @patch('src.infrastructure.embeddings.hf_inference_embedding.InferenceClient')
    def test_api_embedding_with_api_key(self, mock_client_class):
        """测试带API密钥的API调用"""
        mock_client = Mock()
        mock_client.feature_extraction.return_value = [[0.1] * 768]
        mock_client_class.return_value = mock_client
        
        embedding = HFInferenceEmbedding(
            model_name="test-model",
            api_key="test-key-123",
            dimension=768
        )
        
        embedding.get_query_embedding("test")
        
        # 验证 InferenceClient 使用正确的 api_key
        mock_client_class.assert_called_once()
        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs.get("api_key") == "test-key-123"
    
    @patch('src.infrastructure.embeddings.hf_inference_embedding.InferenceClient')
    def test_api_embedding_error_handling(self, mock_client_class):
        """测试API错误处理"""
        mock_client = Mock()
        mock_client.feature_extraction.side_effect = Exception("Network error")
        mock_client_class.return_value = mock_client
        
        embedding = HFInferenceEmbedding(
            model_name="test-model",
            api_key="test-token",
            dimension=768
        )
        
        with pytest.raises(RuntimeError):
            embedding.get_query_embedding("test")
