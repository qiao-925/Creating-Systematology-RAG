"""
Embedding 工厂单元测试
测试 create_embedding 函数、缓存机制、错误处理等
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Optional

from src.embeddings.base import BaseEmbedding
from src.embeddings.local_embedding import LocalEmbedding
from src.embeddings.api_embedding import APIEmbedding
from src.embeddings.factory import (
    create_embedding,
    get_embedding_instance,
    clear_embedding_cache,
    reload_embedding,
)


class TestCreateEmbeddingLocal:
    """测试创建 Local Embedding"""

    def test_create_local_embedding_with_defaults(self, monkeypatch):
        """测试使用默认配置创建 Local Embedding"""
        # Mock config
        mock_config = Mock()
        mock_config.EMBEDDING_TYPE = "local"
        mock_config.EMBEDDING_MODEL = "test-model"
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        
        # 清除缓存
        clear_embedding_cache()
        
        # Mock LocalEmbedding 以避免真实加载模型
        with patch("src.embeddings.factory.LocalEmbedding") as mock_local:
            mock_instance = Mock(spec=BaseEmbedding)
            mock_instance.get_model_name.return_value = "test-model"
            mock_local.return_value = mock_instance
            
            result = create_embedding()
            
            assert result == mock_instance
            mock_local.assert_called_once_with(model_name="test-model")

    def test_create_local_embedding_with_custom_model(self, monkeypatch):
        """测试使用自定义模型名称创建 Local Embedding"""
        mock_config = Mock()
        mock_config.EMBEDDING_TYPE = "local"
        mock_config.EMBEDDING_MODEL = "default-model"
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        with patch("src.embeddings.factory.LocalEmbedding") as mock_local:
            mock_instance = Mock(spec=BaseEmbedding)
            mock_instance.get_model_name.return_value = "custom-model"
            mock_local.return_value = mock_instance
            
            result = create_embedding(model_name="custom-model")
            
            assert result == mock_instance
            mock_local.assert_called_once_with(model_name="custom-model")

    def test_create_local_embedding_with_kwargs(self, monkeypatch):
        """测试使用额外参数创建 Local Embedding"""
        mock_config = Mock()
        mock_config.EMBEDDING_TYPE = "local"
        mock_config.EMBEDDING_MODEL = "test-model"
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        with patch("src.embeddings.factory.LocalEmbedding") as mock_local:
            mock_instance = Mock(spec=BaseEmbedding)
            mock_local.return_value = mock_instance
            
            result = create_embedding(
                embedding_type="local",
                model_name="test-model",
                custom_param="value"
            )
            
            assert result == mock_instance
            mock_local.assert_called_once_with(
                model_name="test-model",
                custom_param="value"
            )


class TestCreateEmbeddingAPI:
    """测试创建 API Embedding"""

    def test_create_api_embedding_with_api_url(self, monkeypatch):
        """测试使用 api_url 参数创建 API Embedding"""
        mock_config = Mock()
        mock_config.EMBEDDING_TYPE = "api"
        mock_config.EMBEDDING_MODEL = "api-model"
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        with patch("src.embeddings.factory.APIEmbedding") as mock_api:
            mock_instance = Mock(spec=BaseEmbedding)
            mock_instance.get_model_name.return_value = "api-model"
            mock_api.return_value = mock_instance
            
            result = create_embedding(
                embedding_type="api",
                api_url="http://example.com/api",
                model_name="api-model"
            )
            
            assert result == mock_instance
            mock_api.assert_called_once_with(
                api_url="http://example.com/api",
                model_name="api-model"
            )

    def test_create_api_embedding_from_config(self, monkeypatch):
        """测试从配置中读取 EMBEDDING_API_URL"""
        mock_config = Mock()
        mock_config.EMBEDDING_TYPE = "api"
        mock_config.EMBEDDING_MODEL = "api-model"
        mock_config.EMBEDDING_API_URL = "http://config-api.com/api"
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        with patch("src.embeddings.factory.APIEmbedding") as mock_api:
            mock_instance = Mock(spec=BaseEmbedding)
            mock_api.return_value = mock_instance
            
            result = create_embedding(embedding_type="api")
            
            assert result == mock_instance
            mock_api.assert_called_once_with(
                api_url="http://config-api.com/api",
                model_name="api-model"
            )

    def test_create_api_embedding_missing_url(self, monkeypatch):
        """测试缺少 api_url 时抛出错误"""
        # 创建一个不包含 EMBEDDING_API_URL 的 Mock 对象
        mock_config = Mock(spec=['EMBEDDING_TYPE', 'EMBEDDING_MODEL'])
        mock_config.EMBEDDING_TYPE = "api"
        mock_config.EMBEDDING_MODEL = "api-model"
        # 不设置 EMBEDDING_API_URL，getattr 会触发 AttributeError，然后返回默认值 None
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        with pytest.raises(ValueError, match="API类型需要提供api_url"):
            create_embedding(embedding_type="api", api_url=None)

    def test_create_api_embedding_empty_url(self, monkeypatch):
        """测试 api_url 为空字符串时抛出错误"""
        # 创建一个不包含 EMBEDDING_API_URL 的 Mock 对象
        mock_config = Mock(spec=['EMBEDDING_TYPE', 'EMBEDDING_MODEL'])
        mock_config.EMBEDDING_TYPE = "api"
        mock_config.EMBEDDING_MODEL = "api-model"
        # 不设置 EMBEDDING_API_URL
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        with pytest.raises(ValueError, match="API类型需要提供api_url"):
            create_embedding(embedding_type="api", api_url="")


class TestCreateEmbeddingHFInference:
    """测试创建 HF Inference API Embedding"""

    @patch('src.embeddings.factory.HFInferenceEmbedding')
    def test_create_hf_inference_embedding(self, mock_hf_class, monkeypatch):
        """测试创建 HF Inference API Embedding"""
        mock_config = Mock()
        mock_config.EMBEDDING_TYPE = "hf-inference"
        mock_config.EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-0.6B"
        mock_config.HF_TOKEN = "hf_test_token_123"
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        mock_instance = Mock(spec=BaseEmbedding)
        mock_instance.get_model_name.return_value = "Qwen/Qwen3-Embedding-0.6B"
        mock_hf_class.return_value = mock_instance
        
        result = create_embedding(embedding_type="hf-inference")
        
        assert result == mock_instance
        mock_hf_class.assert_called_once()
        call_kwargs = mock_hf_class.call_args[1]
        assert call_kwargs['model_name'] == "Qwen/Qwen3-Embedding-0.6B"
        assert call_kwargs['api_key'] == "hf_test_token_123"

    def test_create_hf_inference_embedding_missing_token(self, monkeypatch):
        """测试缺少 HF_TOKEN 时抛出错误"""
        mock_config = Mock()
        mock_config.EMBEDDING_TYPE = "hf-inference"
        mock_config.EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-0.6B"
        mock_config.HF_TOKEN = None
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="HF Inference API 需要设置 HF_TOKEN"):
                create_embedding(embedding_type="hf-inference")

    @patch('src.embeddings.factory.HFInferenceEmbedding')
    def test_create_hf_inference_embedding_with_custom_model(self, mock_hf_class, monkeypatch):
        """测试使用自定义模型名称创建 HF Inference Embedding"""
        mock_config = Mock()
        mock_config.EMBEDDING_TYPE = "hf-inference"
        mock_config.EMBEDDING_MODEL = "default-model"
        mock_config.HF_TOKEN = "hf_test_token_123"
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        mock_instance = Mock(spec=BaseEmbedding)
        mock_hf_class.return_value = mock_instance
        
        result = create_embedding(
            embedding_type="hf-inference",
            model_name="custom-model"
        )
        
        assert result == mock_instance
        call_kwargs = mock_hf_class.call_args[1]
        assert call_kwargs['model_name'] == "custom-model"


class TestCreateEmbeddingErrors:
    """测试创建 Embedding 时的错误处理"""

    def test_unsupported_embedding_type(self):
        """测试不支持的 Embedding 类型"""
        clear_embedding_cache()
        
        with pytest.raises(ValueError, match="不支持的Embedding类型"):
            create_embedding(embedding_type="unsupported_type")

    def test_none_embedding_type_without_config(self, monkeypatch):
        """测试 embedding_type 为 None 且配置也为 None 的情况"""
        mock_config = Mock()
        mock_config.EMBEDDING_TYPE = None
        mock_config.EMBEDDING_MODEL = "test-model"
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        with pytest.raises(ValueError):
            create_embedding(embedding_type=None)


class TestEmbeddingCache:
    """测试 Embedding 缓存机制"""

    def test_cache_mechanism(self, monkeypatch):
        """测试缓存机制：第二次创建返回缓存的实例"""
        mock_config = Mock()
        mock_config.EMBEDDING_TYPE = "local"
        mock_config.EMBEDDING_MODEL = "test-model"
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        with patch("src.embeddings.factory.LocalEmbedding") as mock_local:
            mock_instance = Mock(spec=BaseEmbedding)
            mock_instance.get_model_name.return_value = "test-model"
            mock_local.return_value = mock_instance
            
            # 第一次创建
            result1 = create_embedding(embedding_type="local")
            
            # 第二次创建应该返回缓存
            result2 = create_embedding(embedding_type="local")
            
            assert result1 is result2
            # LocalEmbedding 应该只被调用一次
            assert mock_local.call_count == 1

    def test_force_reload_creates_new_instance(self, monkeypatch):
        """测试 force_reload=True 时创建新实例"""
        mock_config = Mock()
        mock_config.EMBEDDING_TYPE = "local"
        mock_config.EMBEDDING_MODEL = "test-model"
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        with patch("src.embeddings.factory.LocalEmbedding") as mock_local:
            mock_instance1 = Mock(spec=BaseEmbedding)
            mock_instance1.get_model_name.return_value = "test-model"
            mock_instance2 = Mock(spec=BaseEmbedding)
            mock_instance2.get_model_name.return_value = "test-model"
            
            # 第一次调用返回 instance1
            mock_local.return_value = mock_instance1
            result1 = create_embedding(embedding_type="local")
            
            # 第二次调用返回 instance2（force_reload）
            mock_local.return_value = mock_instance2
            result2 = create_embedding(embedding_type="local", force_reload=True)
            
            # force_reload 应该创建新实例
            assert result2 == mock_instance2
            assert mock_local.call_count == 2

    def test_cache_with_different_models(self, monkeypatch):
        """测试不同模型时，由于缓存机制，需要使用 force_reload 创建新实例"""
        mock_config = Mock()
        mock_config.EMBEDDING_TYPE = "local"
        mock_config.EMBEDDING_MODEL = "model1"
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        with patch("src.embeddings.factory.LocalEmbedding") as mock_local:
            mock_instance1 = Mock(spec=BaseEmbedding)
            mock_instance1.get_model_name.return_value = "model1"
            mock_instance2 = Mock(spec=BaseEmbedding)
            mock_instance2.get_model_name.return_value = "model2"
            
            # 创建 model1
            mock_local.return_value = mock_instance1
            result1 = create_embedding(model_name="model1")
            
            # 注意：由于缓存机制，第二次调用会返回缓存的 instance1
            # 要创建不同模型，需要使用 force_reload
            mock_local.return_value = mock_instance2
            result2 = create_embedding(model_name="model2", force_reload=True)
            
            # 使用 force_reload 应该创建新实例
            assert result1 != result2
            assert mock_local.call_count == 2


class TestGetEmbeddingInstance:
    """测试获取当前 Embedding 实例"""

    def test_get_instance_when_cache_is_empty(self):
        """测试缓存为空时返回 None"""
        clear_embedding_cache()
        
        result = get_embedding_instance()
        
        assert result is None

    def test_get_instance_after_creation(self, monkeypatch):
        """测试创建实例后能获取到"""
        mock_config = Mock()
        mock_config.EMBEDDING_TYPE = "local"
        mock_config.EMBEDDING_MODEL = "test-model"
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        with patch("src.embeddings.factory.LocalEmbedding") as mock_local:
            mock_instance = Mock(spec=BaseEmbedding)
            mock_instance.get_model_name.return_value = "test-model"
            mock_local.return_value = mock_instance
            
            created = create_embedding(embedding_type="local")
            retrieved = get_embedding_instance()
            
            assert created is retrieved
            assert retrieved == mock_instance


class TestClearEmbeddingCache:
    """测试清除 Embedding 缓存"""

    def test_clear_cache_when_empty(self):
        """测试清除空缓存"""
        clear_embedding_cache()
        # 应该不抛出异常
        clear_embedding_cache()

    def test_clear_cache_after_creation(self, monkeypatch):
        """测试创建实例后清除缓存"""
        mock_config = Mock()
        mock_config.EMBEDDING_TYPE = "local"
        mock_config.EMBEDDING_MODEL = "test-model"
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        with patch("src.embeddings.factory.LocalEmbedding") as mock_local:
            mock_instance = Mock(spec=BaseEmbedding)
            mock_instance.get_model_name.return_value = "test-model"
            mock_local.return_value = mock_instance
            
            # 创建实例
            create_embedding(embedding_type="local")
            assert get_embedding_instance() is not None
            
            # 清除缓存
            clear_embedding_cache()
            assert get_embedding_instance() is None


class TestReloadEmbedding:
    """测试重新加载 Embedding"""

    def test_reload_clears_cache_and_creates_new(self, monkeypatch):
        """测试 reload_embedding 清除缓存并创建新实例"""
        mock_config = Mock()
        mock_config.EMBEDDING_TYPE = "local"
        mock_config.EMBEDDING_MODEL = "test-model"
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        with patch("src.embeddings.factory.LocalEmbedding") as mock_local:
            mock_instance1 = Mock(spec=BaseEmbedding)
            mock_instance1.get_model_name.return_value = "test-model"
            mock_instance2 = Mock(spec=BaseEmbedding)
            mock_instance2.get_model_name.return_value = "test-model"
            
            # 第一次创建
            mock_local.return_value = mock_instance1
            create_embedding(embedding_type="local")
            
            # 重新加载
            mock_local.return_value = mock_instance2
            result = reload_embedding(embedding_type="local")
            
            assert result == mock_instance2
            assert get_embedding_instance() == mock_instance2
            assert mock_local.call_count == 2

    def test_reload_with_new_parameters(self, monkeypatch):
        """测试使用新参数重新加载"""
        mock_config = Mock()
        mock_config.EMBEDDING_TYPE = "local"
        mock_config.EMBEDDING_MODEL = "old-model"
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        with patch("src.embeddings.factory.LocalEmbedding") as mock_local:
            mock_instance = Mock(spec=BaseEmbedding)
            mock_instance.get_model_name.return_value = "new-model"
            mock_local.return_value = mock_instance
            
            result = reload_embedding(
                embedding_type="local",
                model_name="new-model"
            )
            
            assert result == mock_instance
            mock_local.assert_called_once_with(model_name="new-model")


class TestEmbeddingFactoryIntegration:
    """测试 Embedding 工厂的集成场景"""

    def test_create_multiple_types_sequentially(self, monkeypatch):
        """测试依次创建不同类型的 Embedding"""
        mock_config = Mock()
        mock_config.EMBEDDING_MODEL = "test-model"
        mock_config.EMBEDDING_API_URL = "http://example.com/api"
        
        monkeypatch.setattr("src.embeddings.factory.config", mock_config)
        clear_embedding_cache()
        
        with patch("src.embeddings.factory.LocalEmbedding") as mock_local, \
             patch("src.embeddings.factory.APIEmbedding") as mock_api:
            
            local_instance = Mock(spec=BaseEmbedding)
            local_instance.get_model_name.return_value = "test-model"
            mock_local.return_value = local_instance
            
            api_instance = Mock(spec=BaseEmbedding)
            api_instance.get_model_name.return_value = "api-model"
            mock_api.return_value = api_instance
            
            # 创建 Local
            result1 = create_embedding(embedding_type="local")
            assert result1 == local_instance
            
            # 创建 API（由于缓存机制，需要清除缓存或使用 force_reload）
            # 在实际场景中，切换类型时应该清除缓存或使用 force_reload
            clear_embedding_cache()
            result2 = create_embedding(embedding_type="api", api_url="http://example.com/api")
            assert result2 == api_instance
            
            # 验证两个实例不同
            assert result1 != result2
            # 验证两种类型都被创建
            assert mock_local.call_count == 1
            assert mock_api.call_count == 1
