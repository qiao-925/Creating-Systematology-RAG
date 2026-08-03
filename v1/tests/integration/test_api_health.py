"""Integration tests: API health endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.core.api import router as systematology_router
from backend.fastapi.deps import AppState, get_app_state
from backend.fastapi.main import create_app
from backend.fastapi.routes.health import router as health_router


# =====================================================================
# Systematology /api/systematology/health
# =====================================================================

class TestSystematologyHealth:
    """Systematology health endpoint has no dependencies — direct test."""

    @pytest.fixture
    def client(self):
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(systematology_router)
        return TestClient(app)

    def test_returns_status_ok(self, client):
        response = client.get("/api/systematology/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "systematology"


# =====================================================================
# FastAPI /api/health — state-dependent
# =====================================================================

class TestAppHealth:
    @pytest.fixture
    def client(self, monkeypatch):
        """Create app with health router and reset app state."""
        from backend.fastapi.deps import _app_state as app_state_ref
        import backend.fastapi.deps as deps

        # Reset global app state
        monkeypatch.setattr(deps, "_app_state", None)

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(health_router)
        return TestClient(app)

    def test_initializing_state(self, client):
        """When app is not ready and no error, returns initializing."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "initializing"
        assert "starting" in data["message"].lower()

    def test_ready_state(self, client, monkeypatch):
        """When app is ready, returns ready."""
        state = get_app_state()
        state.set_ready()

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_error_state(self, client):
        """When app has an error, returns error."""
        state = get_app_state()
        state.error = "Database connection failed"

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["message"] == "Database connection failed"
