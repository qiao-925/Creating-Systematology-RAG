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
    
    @patch('requests.post')
    def test_api_embedding_init(self, mock_post):
        """测试HFInferenceEmbedding初始化"""
        # Mock requests.post 返回测试向量
        mock_response = Mock()
        mock_response.json.return_value = [0.1] * 768
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        model_name = "test-model"
        api_key = "test-token-123"
        
        embedding = HFInferenceEmbedding(
            model_name=model_name,
            api_key=api_key
        )
        
        assert isinstance(embedding, BaseEmbedding)
        assert isinstance(embedding, HFInferenceEmbedding)
        assert embedding.get_model_name() == model_name
        assert embedding.get_embedding_dimension() == 768
    
    @patch('requests.post')
    def test_api_embedding_get_query_embedding(self, mock_post):
        """测试API查询向量化（Mock）"""
        mock_response = Mock()
        mock_response.json.return_value = [0.1] * 768
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        embedding = HFInferenceEmbedding(
            model_name="test-model",
            api_key="test-token"
        )
        
        vector = embedding.get_query_embedding("测试查询")
        
        assert isinstance(vector, list)
        assert len(vector) == 768
        assert all(isinstance(x, float) for x in vector)
        
        assert mock_post.call_count == 1
    
    @patch('requests.post')
    def test_api_embedding_get_text_embeddings_batch(self, mock_post):
        """测试API批量向量化（Mock）"""
        # 为每个文本返回不同的向量
        mock_responses = []
        for i in range(3):
            mock_response = Mock()
            mock_response.json.return_value = [float(i+1) * 0.1] * 768
            mock_response.raise_for_status = Mock()
            mock_responses.append(mock_response)
        mock_post.side_effect = mock_responses
        
        embedding = HFInferenceEmbedding(
            model_name="test-model",
            api_key="test-token"
        )
        
        texts = ["文本1", "文本2", "文本3"]
        vectors = embedding.get_text_embeddings(texts)
        
        assert isinstance(vectors, list)
        assert len(vectors) == len(texts)
        assert all(len(v) == 768 for v in vectors)
    
    @patch('requests.post')
    def test_api_embedding_with_api_key(self, mock_post):
        """测试带API密钥的API调用"""
        mock_response = Mock()
        mock_response.json.return_value = [0.1] * 768
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        embedding = HFInferenceEmbedding(
            model_name="test-model",
            api_key="test-key-123"
        )
        
        embedding.get_query_embedding("test")
        
        # 验证 requests.post 使用正确的 headers（包含 API key）
        assert mock_post.call_count == 1
        call_kwargs = mock_post.call_args[1]
        assert 'headers' in call_kwargs
        assert 'Authorization' in call_kwargs['headers']
        assert 'Bearer test-key-123' in call_kwargs['headers']['Authorization']
    
    @patch('requests.post')
    def test_api_embedding_error_handling(self, mock_post):
        """测试API错误处理"""
        from requests.exceptions import ConnectionError
        
        # Mock requests.post 抛出网络错误
        mock_post.side_effect = ConnectionError("Network error")
        
        embedding = HFInferenceEmbedding(
            model_name="test-model",
            api_key="test-token"
        )
        
        with patch('src.infrastructure.embeddings.hf_inference_embedding.time.sleep'):  # Mock sleep
            with pytest.raises(RuntimeError):
                embedding.get_query_embedding("test")
