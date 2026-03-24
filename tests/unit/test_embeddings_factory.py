"""
Embedding factory unit tests aligned with the current backend modules.
"""

from __future__ import annotations

import os
from unittest.mock import Mock, patch

import pytest

import backend.infrastructure.embeddings.factory as factory_module
from backend.infrastructure.embeddings.base import BaseEmbedding
from backend.infrastructure.embeddings.factory import (
    clear_embedding_cache,
    create_embedding,
    get_embedding_instance,
    reload_embedding,
)


def _mock_factory_config(
    monkeypatch,
    *,
    embedding_type: str = "local",
    model_name: str = "test-model",
    hf_token: str | None = None,
):
    config = Mock()
    config.EMBEDDING_TYPE = embedding_type
    config.EMBEDDING_MODEL = model_name
    config.HF_TOKEN = hf_token
    monkeypatch.setattr(factory_module, "config", config)
    return config


def _embedding_instance(model_name: str = "test-model") -> Mock:
    instance = Mock(spec=BaseEmbedding)
    instance.get_model_name.return_value = model_name
    return instance


@pytest.fixture(autouse=True)
def reset_embedding_cache():
    clear_embedding_cache()
    yield
    clear_embedding_cache()


class TestCreateEmbeddingLocal:
    def test_create_local_embedding_with_defaults(self, monkeypatch):
        _mock_factory_config(monkeypatch, embedding_type="local", model_name="default-model")

        with patch("backend.infrastructure.embeddings.local_embedding.LocalEmbedding") as mock_local:
            instance = _embedding_instance("default-model")
            mock_local.return_value = instance

            result = create_embedding()

        assert result is instance
        mock_local.assert_called_once_with(model_name="default-model")

    def test_create_local_embedding_with_custom_model(self, monkeypatch):
        _mock_factory_config(monkeypatch, embedding_type="local", model_name="default-model")

        with patch("backend.infrastructure.embeddings.local_embedding.LocalEmbedding") as mock_local:
            instance = _embedding_instance("custom-model")
            mock_local.return_value = instance

            result = create_embedding(model_name="custom-model")

        assert result is instance
        mock_local.assert_called_once_with(model_name="custom-model")

    def test_create_local_embedding_with_kwargs(self, monkeypatch):
        _mock_factory_config(monkeypatch, embedding_type="local", model_name="kw-model")

        with patch("backend.infrastructure.embeddings.local_embedding.LocalEmbedding") as mock_local:
            instance = _embedding_instance("kw-model")
            mock_local.return_value = instance

            result = create_embedding(
                embedding_type="local",
                model_name="kw-model",
                custom_param="value",
            )

        assert result is instance
        mock_local.assert_called_once_with(model_name="kw-model", custom_param="value")


class TestCreateEmbeddingHFInference:
    def test_create_hf_inference_embedding(self, monkeypatch):
        _mock_factory_config(
            monkeypatch,
            embedding_type="hf-inference",
            model_name="Qwen/Qwen3-Embedding-0.6B",
            hf_token="hf_test_token_123",
        )

        with patch("backend.infrastructure.embeddings.hf_inference_embedding.HFInferenceEmbedding") as mock_hf:
            instance = _embedding_instance("Qwen/Qwen3-Embedding-0.6B")
            mock_hf.return_value = instance

            result = create_embedding(embedding_type="hf-inference")

        assert result is instance
        mock_hf.assert_called_once_with(
            model_name="Qwen/Qwen3-Embedding-0.6B",
            api_key="hf_test_token_123",
        )

    def test_create_hf_inference_embedding_with_custom_model(self, monkeypatch):
        _mock_factory_config(
            monkeypatch,
            embedding_type="hf-inference",
            model_name="default-model",
            hf_token="hf_test_token_123",
        )

        with patch("backend.infrastructure.embeddings.hf_inference_embedding.HFInferenceEmbedding") as mock_hf:
            instance = _embedding_instance("custom-model")
            mock_hf.return_value = instance

            result = create_embedding(
                embedding_type="hf-inference",
                model_name="custom-model",
            )

        assert result is instance
        mock_hf.assert_called_once_with(model_name="custom-model", api_key="hf_test_token_123")

    def test_create_hf_inference_embedding_missing_token(self, monkeypatch):
        _mock_factory_config(
            monkeypatch,
            embedding_type="hf-inference",
            model_name="Qwen/Qwen3-Embedding-0.6B",
            hf_token=None,
        )

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="HF Inference API 需要设置 HF_TOKEN"):
                create_embedding(embedding_type="hf-inference")


class TestCreateEmbeddingErrors:
    def test_unsupported_embedding_type(self, monkeypatch):
        _mock_factory_config(monkeypatch, embedding_type="local")

        with pytest.raises(ValueError, match="不支持的Embedding类型"):
            create_embedding(embedding_type="unsupported_type")


class TestEmbeddingCache:
    def test_cache_mechanism(self, monkeypatch):
        _mock_factory_config(monkeypatch, embedding_type="local", model_name="cached-model")

        with patch("backend.infrastructure.embeddings.local_embedding.LocalEmbedding") as mock_local:
            instance = _embedding_instance("cached-model")
            mock_local.return_value = instance

            first = create_embedding(embedding_type="local")
            second = create_embedding(embedding_type="local")

        assert first is second
        assert mock_local.call_count == 1

    def test_force_reload_creates_new_instance(self, monkeypatch):
        _mock_factory_config(monkeypatch, embedding_type="local", model_name="reload-model")

        with patch("backend.infrastructure.embeddings.local_embedding.LocalEmbedding") as mock_local:
            first = _embedding_instance("reload-model")
            second = _embedding_instance("reload-model")
            mock_local.side_effect = [first, second]

            create_embedding(embedding_type="local")
            reloaded = create_embedding(embedding_type="local", force_reload=True)

        assert reloaded is second
        assert mock_local.call_count == 2


class TestEmbeddingState:
    def test_get_instance_when_cache_is_empty(self):
        assert get_embedding_instance() is None

    def test_get_instance_after_creation(self, monkeypatch):
        _mock_factory_config(monkeypatch, embedding_type="local", model_name="state-model")

        with patch("backend.infrastructure.embeddings.local_embedding.LocalEmbedding") as mock_local:
            instance = _embedding_instance("state-model")
            mock_local.return_value = instance

            created = create_embedding(embedding_type="local")

        assert created is get_embedding_instance()

    def test_clear_cache_after_creation(self, monkeypatch):
        _mock_factory_config(monkeypatch, embedding_type="local", model_name="clear-model")

        with patch("backend.infrastructure.embeddings.local_embedding.LocalEmbedding") as mock_local:
            mock_local.return_value = _embedding_instance("clear-model")
            create_embedding(embedding_type="local")

        assert get_embedding_instance() is not None
        clear_embedding_cache()
        assert get_embedding_instance() is None

    def test_reload_with_new_parameters(self, monkeypatch):
        _mock_factory_config(monkeypatch, embedding_type="local", model_name="old-model")

        with patch("backend.infrastructure.embeddings.local_embedding.LocalEmbedding") as mock_local:
            instance = _embedding_instance("new-model")
            mock_local.return_value = instance

            result = reload_embedding(
                embedding_type="local",
                model_name="new-model",
            )

        assert result is instance
        mock_local.assert_called_once_with(model_name="new-model")
