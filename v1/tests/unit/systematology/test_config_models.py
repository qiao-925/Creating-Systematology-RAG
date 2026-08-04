"""Unit tests: config models — Pydantic validation for configuration."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.infrastructure.config.models import (
    AppConfig,
    DeepSeekConfig,
    EmbeddingConfig,
    IndexConfig,
    LLMModelConfig,
    LLMModelsConfig,
    PathsConfig,
    RerankerConfig,
    SystematologyConfig,
    SystematologyD2DConfig,
    SystematologyFCMConfig,
    VectorStoreConfig,
)


# =====================================================================
# IndexConfig Tests
# =====================================================================

class TestIndexConfig:
    def test_default_valid_config(self):
        cfg = IndexConfig(chunk_size=256, chunk_overlap=20, similarity_top_k=3, similarity_threshold=0.5)
        assert cfg.chunk_size == 256
        assert cfg.chunk_overlap == 20

    def test_chunk_overlap_ge_chunk_size_raises(self):
        with pytest.raises(ValidationError):
            IndexConfig(chunk_size=100, chunk_overlap=100, similarity_top_k=3, similarity_threshold=0.5)

    def test_chunk_overlap_negative_raises(self):
        with pytest.raises(ValidationError):
            IndexConfig(chunk_size=100, chunk_overlap=-1, similarity_top_k=3, similarity_threshold=0.5)

    def test_chunk_size_zero_raises(self):
        with pytest.raises(ValidationError):
            IndexConfig(chunk_size=0, chunk_overlap=0, similarity_top_k=3, similarity_threshold=0.5)

    def test_chunk_size_negative_raises(self):
        with pytest.raises(ValidationError):
            IndexConfig(chunk_size=-10, chunk_overlap=0, similarity_top_k=3, similarity_threshold=0.5)


# =====================================================================
# SystematologyConfig Tests
# =====================================================================

class TestSystematologyConfig:
    def test_default_values(self):
        cfg = SystematologyConfig()
        assert cfg.specialist_model == "deepseek-chat"
        assert cfg.budget_turns == 10
        assert cfg.budget_tokens == 100000
        assert cfg.timeout_seconds == 180
        assert cfg.max_perspectives == 3

    def test_fcm_subconfig_defaults(self):
        cfg = SystematologyConfig()
        assert cfg.fcm.max_iterations == 100
        assert cfg.fcm.convergence_threshold == 1e-6

    def test_d2d_subconfig_defaults(self):
        cfg = SystematologyConfig()
        assert cfg.d2d.perturbation_pct == 0.1

    def test_custom_values(self):
        cfg = SystematologyConfig(
            specialist_model="gpt-4o",
            budget_turns=5,
            fcm=SystematologyFCMConfig(max_iterations=50),
            d2d=SystematologyD2DConfig(perturbation_pct=0.2),
        )
        assert cfg.specialist_model == "gpt-4o"
        assert cfg.budget_turns == 5
        assert cfg.fcm.max_iterations == 50
        assert cfg.d2d.perturbation_pct == 0.2


# =====================================================================
# LLMModelConfig Tests
# =====================================================================

class TestLLMModelConfig:
    def test_minimal_config(self):
        cfg = LLMModelConfig(
            id="deepseek-chat",
            name="DeepSeek Chat",
            litellm_model="deepseek/deepseek-chat",
            api_key_env="DEEPSEEK_API_KEY",
        )
        assert cfg.id == "deepseek-chat"
        assert cfg.supports_reasoning is False

    def test_default_optional_fields(self):
        cfg = LLMModelConfig(
            id="test",
            name="Test",
            litellm_model="test/test",
            api_key_env="TEST_KEY",
        )
        assert cfg.temperature == 0.7
        assert cfg.max_tokens == 4096
        assert cfg.request_timeout == 30.0

    def test_custom_temperature(self):
        cfg = LLMModelConfig(
            id="test", name="Test", litellm_model="test/test",
            api_key_env="TEST", temperature=0.1, max_tokens=1024,
        )
        assert cfg.temperature == 0.1
        assert cfg.max_tokens == 1024

    def test_extra_fields_are_ignored(self):
        # LLMModelConfig does not have extra="forbid", so unknown fields are silently ignored
        cfg = LLMModelConfig(
            id="test", name="Test", litellm_model="test/test",
            api_key_env="TEST",
        )
        assert cfg.id == "test"


# =====================================================================
# LLMModelsConfig Tests
# =====================================================================

class TestLLMModelsConfig:
    def test_default_model_id(self):
        cfg = LLMModelsConfig()
        assert cfg.default == "deepseek-chat"
        assert cfg.available == []

    def test_with_available_models(self):
        cfg = LLMModelsConfig(
            available=[
                LLMModelConfig(
                    id="deepseek-chat", name="DeepSeek",
                    litellm_model="deepseek/deepseek-chat", api_key_env="DEEPSEEK_API_KEY",
                ),
            ]
        )
        assert len(cfg.available) == 1

    def test_retry_defaults(self):
        cfg = LLMModelsConfig()
        assert cfg.max_retries == 3
        assert cfg.retry_delay == 2.0


# =====================================================================
# Other Config Model Tests
# =====================================================================

class TestAppConfig:
    def test_basic(self):
        cfg = AppConfig(title="Systematology", port=8000)
        assert cfg.title == "Systematology"
        assert cfg.port == 8000
        assert cfg.dev_mode is True  # default


class TestDeepSeekConfig:
    def test_defaults(self):
        cfg = DeepSeekConfig()
        assert cfg.enable_reasoning_display is True
        assert cfg.store_reasoning is False
        assert cfg.json_output_enabled is False

    def test_custom(self):
        cfg = DeepSeekConfig(store_reasoning=True, json_output_enabled=True)
        assert cfg.store_reasoning is True
        assert cfg.json_output_enabled is True


class TestEmbeddingConfig:
    def test_defaults(self):
        cfg = EmbeddingConfig(type="local")
        assert cfg.batch_size == 10
        assert cfg.max_length == 512
        assert cfg.api_url is None


class TestRerankerConfig:
    def test_defaults(self):
        cfg = RerankerConfig()
        assert cfg.type == "sentence-transformer"
        assert cfg.top_n == 3
        assert cfg.model is None

    def test_type_affects_behavior(self):
        cfg = RerankerConfig(type="cross-encoder", model="BAAI/bge-reranker-base")
        assert cfg.type == "cross-encoder"
        assert cfg.model == "BAAI/bge-reranker-base"


class TestVectorStoreConfig:
    def test_default_collection(self):
        cfg = VectorStoreConfig()
        assert cfg.collection_name == "default"


class TestPathsConfig:
    def test_all_paths_are_strings(self):
        cfg = PathsConfig(
            raw_data="./data/raw",
            processed_data="./data/processed",
            vector_store="./data/vector",
            activity_log="./data/activity.log",
            github_repos="./data/github",
            github_sync_state="./data/sync_state.json",
        )
        assert isinstance(cfg.raw_data, str)
        assert isinstance(cfg.vector_store, str)

    def test_optional_fields_have_defaults(self):
        cfg = PathsConfig(
            raw_data="./raw",
            processed_data="./processed",
            vector_store="./vec",
            activity_log="./log",
            github_repos="./gh",
            github_sync_state="./sync",
        )
        assert cfg.cache_state == "./data/cache_state.json"
        assert cfg.sessions == "./data/sessions"
