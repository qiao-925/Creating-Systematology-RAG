"""
Embedding factory smoke tests.
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


def _set_factory_config(
    monkeypatch,
    *,
    embedding_type: str = "local",
    model_name: str = "test-model",
    hf_token: str | None = None,
):
    mock_config = Mock()
    mock_config.EMBEDDING_TYPE = embedding_type
    mock_config.EMBEDDING_MODEL = model_name
    mock_config.HF_TOKEN = hf_token
    monkeypatch.setattr(factory_module, "config", mock_config)
    return mock_config


def _mock_embedding(model_name: str = "test-model") -> Mock:
    instance = Mock(spec=BaseEmbedding)
    instance.get_model_name.return_value = model_name
    return instance


@pytest.fixture(autouse=True)
def clear_cache():
    clear_embedding_cache()
    yield
    clear_embedding_cache()


@pytest.mark.fast
class TestEmbeddingFactory:
    def test_embedding_factory_local(self, monkeypatch):
        _set_factory_config(monkeypatch, embedding_type="local", model_name="local-model")

        with patch("backend.infrastructure.embeddings.local_embedding.LocalEmbedding") as mock_local:
            instance = _mock_embedding("local-model")
            mock_local.return_value = instance

            embedding = create_embedding()

        assert embedding is instance
        assert get_embedding_instance() is instance
        mock_local.assert_called_once_with(model_name="local-model")

    def test_embedding_factory_hf_inference(self, monkeypatch):
        _set_factory_config(
            monkeypatch,
            embedding_type="hf-inference",
            model_name="hf-model",
            hf_token="hf_test_token",
        )

        with patch("backend.infrastructure.embeddings.hf_inference_embedding.HFInferenceEmbedding") as mock_hf:
            instance = _mock_embedding("hf-model")
            mock_hf.return_value = instance

            embedding = create_embedding(embedding_type="hf-inference")

        assert embedding is instance
        mock_hf.assert_called_once_with(model_name="hf-model", api_key="hf_test_token")

    def test_embedding_factory_invalid_type(self, monkeypatch):
        _set_factory_config(monkeypatch, embedding_type="local")

        with pytest.raises(ValueError, match="不支持的Embedding类型"):
            create_embedding(embedding_type="invalid_type")

    def test_embedding_factory_hf_inference_missing_token(self, monkeypatch):
        _set_factory_config(
            monkeypatch,
            embedding_type="hf-inference",
            model_name="hf-model",
            hf_token=None,
        )

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="HF Inference API 需要设置 HF_TOKEN"):
                create_embedding(embedding_type="hf-inference")

    def test_embedding_factory_cache(self, monkeypatch):
        _set_factory_config(monkeypatch, embedding_type="local", model_name="cached-model")

        with patch("backend.infrastructure.embeddings.local_embedding.LocalEmbedding") as mock_local:
            instance = _mock_embedding("cached-model")
            mock_local.return_value = instance

            first = create_embedding(embedding_type="local")
            second = create_embedding(embedding_type="local")

        assert first is second
        assert mock_local.call_count == 1

    def test_reload_embedding_creates_new_instance(self, monkeypatch):
        _set_factory_config(monkeypatch, embedding_type="local", model_name="reload-model")

        with patch("backend.infrastructure.embeddings.local_embedding.LocalEmbedding") as mock_local:
            first = _mock_embedding("reload-model")
            second = _mock_embedding("reload-model")
            mock_local.side_effect = [first, second]

            create_embedding(embedding_type="local")
            reloaded = reload_embedding(embedding_type="local")

        assert reloaded is second
        assert get_embedding_instance() is second
        assert mock_local.call_count == 2
