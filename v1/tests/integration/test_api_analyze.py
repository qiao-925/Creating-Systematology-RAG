"""Integration tests: /api/systematology/analyze — POST endpoint."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.core.models import CLDNode, SharedCLD, StructuredReport, StructuredFailureReport


@pytest.fixture
def client(monkeypatch):
    """Create app with systematology router, mock _create_lead_agent."""
    from backend.core import api as api_module
    from backend.core.api import router as systematology_router

    # Store the success response to return
    mock_report = StructuredReport(
        cld_visualization={
            "nodes": [{"id": "a", "label": "test"}],
            "edges": [],
        },
        synthesized_insights="Test insights via mock.",
        evidence_tracing={"run_id": "mock-run"},
    )

    class MockAgent:
        def __init__(self, *args, **kwargs):
            pass

        async def run(self, question, documents, run_context):
            return mock_report

    monkeypatch.setattr(api_module, "_create_lead_agent", MockAgent)

    app = FastAPI()
    app.include_router(systematology_router)
    return TestClient(app)


@pytest.fixture
def client_failure(monkeypatch):
    """Create app that returns a StructuredFailureReport."""
    from backend.core import api as api_module
    from backend.core.api import router as systematology_router

    mock_failure = StructuredFailureReport(
        run_id="fail-run",
        stage="cld_analysis",
        reason="mock failure reason",
    )

    class FailingAgent:
        def __init__(self, *args, **kwargs):
            pass

        async def run(self, question, documents, run_context):
            return mock_failure

    monkeypatch.setattr(api_module, "_create_lead_agent", FailingAgent)

    app = FastAPI()
    app.include_router(systematology_router)
    return TestClient(app)


@pytest.fixture
def client_error(monkeypatch):
    """Create app where agent.run() throws an exception."""
    from backend.core import api as api_module
    from backend.core.api import router as systematology_router

    class ErrorAgent:
        def __init__(self, *args, **kwargs):
            pass

        async def run(self, question, documents, run_context):
            raise RuntimeError("simulated server error")

    monkeypatch.setattr(api_module, "_create_lead_agent", ErrorAgent)

    app = FastAPI()
    app.include_router(systematology_router)
    return TestClient(app)


# =====================================================================
# POST /api/systematology/analyze Tests
# =====================================================================

class TestAnalyzeHappyPath:
    def test_valid_question_returns_200(self, client):
        response = client.post("/api/systematology/analyze", json={
            "question": "How does fiscal subsidy affect housing?",
        })
        assert response.status_code == 200

    def test_response_has_success_true(self, client):
        response = client.post("/api/systematology/analyze", json={
            "question": "How does fiscal subsidy affect housing?",
        })
        data = response.json()
        assert data["success"] is True

    def test_report_contains_expected_fields(self, client):
        response = client.post("/api/systematology/analyze", json={
            "question": "test question",
        })
        data = response.json()
        report = data["report"]
        assert "cld_visualization" in report
        assert "synthesized_insights" in report
        assert "evidence_tracing" in report

    def test_with_documents(self, client):
        response = client.post("/api/systematology/analyze", json={
            "question": "test",
            "documents": ["Document one", "Document two"],
        })
        assert response.status_code == 200
        assert response.json()["success"] is True


class TestAnalyzeFailurePath:
    def test_failure_report_returns_success_false(self, client_failure):
        response = client_failure.post("/api/systematology/analyze", json={
            "question": "This is a question that triggers a failure.",
        })
        data = response.json()
        assert data["success"] is False

    def test_failure_report_contains_reason(self, client_failure):
        response = client_failure.post("/api/systematology/analyze", json={
            "question": "test",
        })
        data = response.json()
        report = data["report"]
        assert report["reason"] == "mock failure reason"


class TestAnalyzeValidation:
    def test_empty_question_returns_422(self, client):
        response = client.post("/api/systematology/analyze", json={
            "question": "",
        })
        assert response.status_code == 422

    def test_missing_question_returns_422(self, client):
        response = client.post("/api/systematology/analyze", json={})
        assert response.status_code == 422


class TestAnalyzeServerError:
    def test_exception_returns_500(self, client_error):
        response = client_error.post("/api/systematology/analyze", json={
            "question": "test",
        })
        assert response.status_code == 500
