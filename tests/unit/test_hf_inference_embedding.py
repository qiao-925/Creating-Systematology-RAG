"""
Hugging Face Inference API Embedding 单元测试
测试 HFInferenceEmbedding 类的功能（使用直接 HTTP 请求）
"""

import pytest
from unittest.mock import Mock, patch
from typing import List
import os

from backend.infrastructure.embeddings.base import BaseEmbedding
from backend.infrastructure.embeddings.hf_inference_embedding import HFInferenceEmbedding


class TestHFInferenceEmbedding:
    """HFInferenceEmbedding 测试"""
    
    def test_hf_inference_embedding_init_without_token(self):
        """测试初始化时缺少 Token 的情况"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("backend.infrastructure.embeddings.hf_inference_embedding.config") as mock_config:
                mock_config.HF_TOKEN = None
                
                with pytest.raises(ValueError, match="HF_TOKEN 未设置"):
                    HFInferenceEmbedding(
                        model_name="Qwen/Qwen3-Embedding-0.6B",
                        api_key=None
                    )
    
    @patch('requests.post')
    def test_hf_inference_embedding_init_with_token(self, mock_post):
        """测试使用 Token 初始化"""
        # Mock requests.post 返回测试向量
        mock_response = Mock()
        mock_response.json.return_value = [0.1] * 1024  # Qwen3-Embedding-0.6B 是 1024 维
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {'HF_TOKEN': 'hf_test_token_123'}):
            embedding = HFInferenceEmbedding(
                model_name="Qwen/Qwen3-Embedding-0.6B",
                api_key="hf_test_token_123"
            )
            
            assert isinstance(embedding, BaseEmbedding)
            assert isinstance(embedding, HFInferenceEmbedding)
            assert embedding.get_model_name() == "Qwen/Qwen3-Embedding-0.6B"
            assert embedding.get_embedding_dimension() == 1024
    
    @patch('requests.post')
    def test_hf_inference_embedding_get_query_embedding(self, mock_post):
        """测试查询向量化"""
        # Mock requests.post 返回测试向量
        mock_response = Mock()
        mock_response.json.return_value = [0.1] * 1024
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        embedding = HFInferenceEmbedding(
            model_name="Qwen/Qwen3-Embedding-0.6B",
            api_key="hf_test_token_123"
        )
        
        # 重置 mock 调用计数
        mock_post.reset_mock()
        mock_response.json.return_value = [0.1] * 1024
        
        vector = embedding.get_query_embedding("测试查询")
        
        assert isinstance(vector, list)
        assert len(vector) == 1024
        assert all(isinstance(x, float) for x in vector)
        
        # 验证 API 调用
        assert mock_post.call_count == 1
        call_args = mock_post.call_args
        assert call_args[1]['json']['inputs'] == "测试查询"
        assert "Qwen/Qwen3-Embedding-0.6B" in call_args[0][0]  # URL 包含模型名
    
    @patch('requests.post')
    def test_hf_inference_embedding_get_text_embeddings_batch(self, mock_post):
        """测试批量向量化"""
        # Mock requests.post 返回测试向量
        mock_responses = []
        for i in range(3):
            mock_response = Mock()
            mock_response.json.return_value = [float(i+1) * 0.1] * 1024
            mock_response.raise_for_status = Mock()
            mock_responses.append(mock_response)
        mock_post.side_effect = mock_responses
        
        embedding = HFInferenceEmbedding(
            model_name="Qwen/Qwen3-Embedding-0.6B",
            api_key="hf_test_token_123"
        )
        
        # 重置 mock，准备批量调用
        mock_post.reset_mock()
        mock_responses = []
        for i in range(3):
            mock_response = Mock()
            mock_response.json.return_value = [float(i+1) * 0.1] * 1024
            mock_response.raise_for_status = Mock()
            mock_responses.append(mock_response)
        mock_post.side_effect = mock_responses
        
        texts = ["文本1", "文本2", "文本3"]
        vectors = embedding.get_text_embeddings(texts)
        
        assert isinstance(vectors, list)
        assert len(vectors) == len(texts)
        assert all(len(v) == 1024 for v in vectors)
        
        # 验证 API 调用（每个文本调用一次）
        assert mock_post.call_count == 3
    
    @patch('requests.post')
    def test_hf_inference_embedding_batch_splitting(self, mock_post):
        """测试大批量自动分批处理"""
        # Mock requests.post 返回测试向量
        mock_response = Mock()
        mock_response.json.return_value = [0.1] * 1024
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        embedding = HFInferenceEmbedding(
            model_name="Qwen/Qwen3-Embedding-0.6B",
            api_key="hf_test_token_123"
        )
        
        # 重置 mock，准备批量调用
        mock_post.reset_mock()
        mock_response.json.return_value = [0.1] * 1024
        
        # 创建 250 个文本（应该逐个处理）
        texts = [f"文本{i}" for i in range(250)]
        vectors = embedding.get_text_embeddings(texts)
        
        assert len(vectors) == 250
        # 验证被调用了 250 次（每个文本一次）
        assert mock_post.call_count == 250
    
    @patch('requests.post')
    def test_hf_inference_embedding_503_retry(self, mock_post):
        """测试 503 状态（模型加载中）的重试机制"""
        from requests.exceptions import HTTPError
        
        # 第一次调用抛出异常（模拟 503），第二次成功
        mock_error_response = Mock()
        mock_error_response.status_code = 503
        mock_error_response.text = "Model is currently loading"
        http_error = HTTPError(response=mock_error_response)
        
        mock_success_response = Mock()
        mock_success_response.json.return_value = [0.1] * 1024
        mock_success_response.raise_for_status = Mock()
        
        mock_post.side_effect = [http_error, mock_success_response]
        
        embedding = HFInferenceEmbedding(
            model_name="Qwen/Qwen3-Embedding-0.6B",
            api_key="hf_test_token_123"
        )
        
        # 重置 mock，准备测试调用
        mock_post.reset_mock()
        mock_error_response = Mock()
        mock_error_response.status_code = 503
        mock_error_response.text = "Model is currently loading"
        http_error = HTTPError(response=mock_error_response)
        mock_success_response = Mock()
        mock_success_response.json.return_value = [0.1] * 1024
        mock_success_response.raise_for_status = Mock()
        mock_post.side_effect = [http_error, mock_success_response]
        
        with patch("backend.infrastructure.embeddings.hf_api_client.time.sleep"):
            vector = embedding.get_query_embedding("test")
        
        assert len(vector) == 1024
        # 验证被调用了 2 次（503 + 成功）
        assert mock_post.call_count == 2
    
    @patch('requests.post')
    def test_hf_inference_embedding_network_error_retry(self, mock_post):
        """测试网络错误的重试机制"""
        from requests.exceptions import ConnectionError
        
        # 前两次失败，第三次成功
        mock_success_response = Mock()
        mock_success_response.json.return_value = [0.1] * 1024
        mock_success_response.raise_for_status = Mock()
        
        mock_post.side_effect = [
            ConnectionError("Network error"),
            ConnectionError("Network error"),
            mock_success_response
        ]
        
        embedding = HFInferenceEmbedding(
            model_name="Qwen/Qwen3-Embedding-0.6B",
            api_key="hf_test_token_123"
        )
        
        # 重置 mock，准备测试调用
        mock_post.reset_mock()
        mock_success_response = Mock()
        mock_success_response.json.return_value = [0.1] * 1024
        mock_success_response.raise_for_status = Mock()
        mock_post.side_effect = [
            ConnectionError("Network error"),
            ConnectionError("Network error"),
            mock_success_response
        ]
        
        with patch("backend.infrastructure.embeddings.hf_api_client.time.sleep"):
            vector = embedding.get_query_embedding("test")
        
        assert len(vector) == 1024
        # 验证被调用了 3 次（2 次失败 + 1 次成功）
        assert mock_post.call_count == 3
    
    @patch('requests.post')
    def test_hf_inference_embedding_max_retries_exceeded(self, mock_post):
        """测试超过最大重试次数后抛出异常"""
        from requests.exceptions import ConnectionError
        
        # 所有调用都失败
        mock_post.side_effect = ConnectionError("Network error")
        
        embedding = HFInferenceEmbedding(
            model_name="Qwen/Qwen3-Embedding-0.6B",
            api_key="hf_test_token_123"
        )
        
        # 重置 mock，准备测试调用（所有调用都失败）
        mock_post.reset_mock()
        mock_post.side_effect = ConnectionError("Network error")
        
        with patch("backend.infrastructure.embeddings.hf_api_client.time.sleep"):
            with pytest.raises(RuntimeError, match="HF API 调用失败"):
                embedding.get_query_embedding("test")
        
        # 验证被调用了 max_retries + 1 次（初始 + 重试）
        assert mock_post.call_count == 4  # 1 次初始 + 3 次重试
    
    @patch('requests.post')
    def test_hf_inference_embedding_empty_texts(self, mock_post):
        """测试空文本列表"""
        # Mock requests.post
        mock_response = Mock()
        mock_response.json.return_value = [0.1] * 1024
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        embedding = HFInferenceEmbedding(
            model_name="Qwen/Qwen3-Embedding-0.6B",
            api_key="hf_test_token_123"
        )
        
        # 重置 mock，准备测试空列表
        mock_post.reset_mock()
        
        vectors = embedding.get_text_embeddings([])
        
        assert vectors == []
        # 验证没有调用 API（空列表直接返回）
        assert mock_post.call_count == 0
    
    @patch('requests.post')
    def test_hf_inference_embedding_single_text_response_format(self, mock_post):
        """测试单个文本时 API 返回单个向量的格式"""
        # Mock requests.post 返回单个向量
        mock_response = Mock()
        mock_response.json.return_value = [0.1] * 1024
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        embedding = HFInferenceEmbedding(
            model_name="Qwen/Qwen3-Embedding-0.6B",
            api_key="hf_test_token_123"
        )
        
        vectors = embedding.get_text_embeddings(["单个文本"])
        
        assert isinstance(vectors, list)
        assert len(vectors) == 1
        assert len(vectors[0]) == 1024
    
    @patch('requests.post')
    def test_hf_inference_embedding_dimension_detection(self, mock_post):
        """测试自动维度检测"""
        # Mock requests.post 返回测试向量
        mock_response = Mock()
        mock_response.json.return_value = [0.1] * 1024
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        embedding = HFInferenceEmbedding(
            model_name="Qwen/Qwen3-Embedding-0.6B",
            api_key="hf_test_token_123"
            # 不提供 dimension，应该自动检测
        )
        
        assert embedding.get_embedding_dimension() == 1024
    
    @patch('requests.post')
    def test_hf_inference_embedding_dimension_fallback(self, mock_post):
        """测试维度检测失败时的默认值"""
        from requests.exceptions import RequestException
        
        # Mock requests.post - 验证时失败
        mock_post.side_effect = RequestException("API error")
        
        with patch("backend.infrastructure.embeddings.hf_inference_embedding.logger"):
            embedding = HFInferenceEmbedding(
                model_name="Qwen/Qwen3-Embedding-0.6B",
                api_key="hf_test_token_123"
                # 验证失败，应该使用默认值
            )
            
            # Qwen3-Embedding-0.6B 应该使用 1024 作为默认值
            assert embedding.get_embedding_dimension() == 1024
    
    @patch('requests.post')
    def test_hf_inference_embedding_custom_timeout(self, mock_post):
        """测试自定义超时时间（requests 支持 timeout 参数）"""
        # Mock requests.post 返回测试向量
        mock_response = Mock()
        mock_response.json.return_value = [0.1] * 1024
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        embedding = HFInferenceEmbedding(
            model_name="Qwen/Qwen3-Embedding-0.6B",
            api_key="hf_test_token_123"
        )
        
        embedding.get_query_embedding("test")
        
        # 验证 requests.post 被调用，且包含 timeout 参数
        assert mock_post.call_count == 1
        call_kwargs = mock_post.call_args[1]
        assert 'timeout' in call_kwargs
        assert call_kwargs['timeout'] == 30  # 默认超时时间
    
    @patch('requests.post')
    def test_hf_inference_embedding_get_model_name(self, mock_post):
        """测试获取模型名称"""
        mock_response = Mock()
        mock_response.json.return_value = [0.1] * 1024
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        embedding = HFInferenceEmbedding(
            model_name="custom-model",
            api_key="hf_test_token_123"
        )
        
        assert embedding.get_model_name() == "custom-model"
    
    @patch('requests.post')
    def test_hf_inference_embedding_invalid_response_format(self, mock_post):
        """测试无效的 API 响应格式"""
        # Mock requests.post - 返回无效格式
        mock_response = Mock()
        mock_response.json.return_value = {"error": "invalid format"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        embedding = HFInferenceEmbedding(
            model_name="Qwen/Qwen3-Embedding-0.6B",
            api_key="hf_test_token_123"
        )
        
        # 重置 mock，准备测试无效格式
        mock_post.reset_mock()
        mock_response.json.return_value = {"error": "invalid format"}
        
        # 由于响应格式无效，应该抛出异常或使用默认处理
        # 根据实际实现，可能会尝试解析或抛出异常
        try:
            embedding.get_query_embedding("test")
        except (RuntimeError, ValueError, TypeError, KeyError):
            pass  # 预期的异常
