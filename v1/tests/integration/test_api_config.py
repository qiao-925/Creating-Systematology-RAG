"""Integration tests: API config endpoints."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.fastapi.routes.config import router as config_router


@pytest.fixture
def client(monkeypatch):
    """Create app with config router, patch the global config singleton."""
    import backend.fastapi.routes.config as config_module

    # Mock config attributes used by the route
    monkeypatch.setattr(config_module.config, "get_default_llm_id", lambda: "deepseek-chat")
    monkeypatch.setattr(config_module.config, "RETRIEVAL_STRATEGY", "vector")
    monkeypatch.setattr(config_module.config, "SIMILARITY_TOP_K", 3)
    monkeypatch.setattr(config_module.config, "SIMILARITY_THRESHOLD", 0.4)
    monkeypatch.setattr(config_module.config, "ENABLE_RERANK", False)
    monkeypatch.setattr(config_module.config, "DEEPSEEK_ENABLE_REASONING_DISPLAY", True)

    app = FastAPI()
    app.include_router(config_router)
    return TestClient(app)


# =====================================================================
# GET /api/config
# =====================================================================

class TestGetConfig:
    def test_returns_200(self, client):
        response = client.get("/config")
        assert response.status_code == 200

    def test_response_shape(self, client):
        response = client.get("/config")
        data = response.json()
        assert "selected_model" in data
        assert "llm_preset" in data
        assert "retrieval_strategy" in data
        assert "similarity_top_k" in data
        assert "similarity_threshold" in data
        assert "enable_rerank" in data
        assert "show_reasoning" in data

    def test_default_values(self, client):
        response = client.get("/config")
        data = response.json()
        assert data["selected_model"] == "deepseek-chat"
        assert data["retrieval_strategy"] == "vector"
        assert data["similarity_top_k"] == 3
        assert data["enable_rerank"] is False


# =====================================================================
# GET /api/config/models
# =====================================================================

class TestListModels:
    def test_returns_200(self, client, monkeypatch):
        monkeypatch.setattr(
            config_module_with_import(),
            "get_available_llm_models",
            lambda: [],
        )
        response = client.get("/config/models")
        assert response.status_code == 200

    def test_empty_list(self, client, monkeypatch):
        import backend.fastapi.routes.config as config_module
        monkeypatch.setattr(config_module.config, "get_available_llm_models", lambda: [])

        response = client.get("/config/models")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_with_models(self, client, monkeypatch):
        from backend.infrastructure.config.models import LLMModelConfig

        models = [
            LLMModelConfig(
                id="deepseek-chat", name="DeepSeek Chat",
                litellm_model="deepseek/deepseek-chat", api_key_env="DEEPSEEK_API_KEY",
                supports_reasoning=True,
            ),
        ]

        import backend.fastapi.routes.config as config_module
        monkeypatch.setattr(config_module.config, "get_available_llm_models", lambda: models)

        response = client.get("/config/models")
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "deepseek-chat"
        assert data[0]["name"] == "DeepSeek Chat"
        assert data[0]["supports_reasoning"] is True


def config_module_with_import():
    """Helper to get the config module for monkeypatching."""
    import backend.fastapi.routes.config as config_module
    return config_module.config
