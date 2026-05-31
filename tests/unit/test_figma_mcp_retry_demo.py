"""Tests for the Figma MCP retry demo script.

These tests cover the script's retry/session parsing logic without making
real network calls.
"""

from __future__ import annotations

import importlib
import urllib.error
from email.message import Message
from unittest.mock import Mock

import pytest


@pytest.fixture()
def demo_module(monkeypatch):
    """Import the demo module with stable environment variables."""
    monkeypatch.setenv("FIGMA_MCP_BASE_URL", "https://example.test/mcp")
    monkeypatch.setenv("FIGMA_MCP_TOKEN", "")
    monkeypatch.setenv("FIGMA_MCP_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("FIGMA_MCP_WAIT_SECONDS", "0")
    return importlib.import_module("scripts.figma_mcp_retry_demo")


def test_parse_session_id_supports_common_header_casing(demo_module):
    headers = {
        "mcp-session-id": "lower",
        "Mcp-Session-Id": "title",
        "MCP-Session-Id": "upper",
    }

    assert demo_module.parse_session_id(headers) == "lower"


def test_post_returns_http_error_body_and_headers(demo_module, monkeypatch):
    response_headers = Message()
    response_headers["Retry-After"] = "7"
    http_error = urllib.error.HTTPError(
        url="https://example.test/mcp",
        code=429,
        msg="Too Many Requests",
        hdrs=response_headers,
        fp=None,
    )
    http_error.read = Mock(return_value=b'{"error":"rate limited"}')

    monkeypatch.setattr(demo_module.urllib.request, "urlopen", Mock(side_effect=http_error))

    status, headers, body = demo_module.post({"jsonrpc": "2.0", "id": 1, "method": "ping"})

    assert status == 429
    assert headers["Retry-After"] == "7"
    assert body == '{"error":"rate limited"}'


def test_main_retries_initialize_then_calls_whoami(demo_module, monkeypatch):
    calls: list[tuple[dict, str | None]] = []
    sleeps: list[int] = []

    def fake_post(payload, session_id=None):
        calls.append((payload, session_id))
        method = payload.get("method")
        if method == "initialize":
            if len([call for call in calls if call[0].get("method") == "initialize"]) == 1:
                return 401, {}, "unauthorized"
            return 200, {"mcp-session-id": "session-123"}, "initialized"
        if method == "notifications/initialized":
            assert session_id == "session-123"
            return 200, {}, ""
        if method == "tools/call":
            assert session_id == "session-123"
            return 200, {}, '{"result":"ok"}'
        raise AssertionError(f"Unexpected payload: {payload}")

    monkeypatch.setattr(demo_module, "post", fake_post)
    monkeypatch.setattr(demo_module.time, "sleep", lambda seconds: sleeps.append(seconds))

    exit_code = demo_module.main()

    assert exit_code == 0
    assert sleeps == [0]
    assert [call[0]["method"] for call in calls] == [
        "initialize",
        "initialize",
        "notifications/initialized",
        "tools/call",
    ]


def test_main_returns_1_when_session_never_appears(demo_module, monkeypatch):
    monkeypatch.setattr(demo_module, "post", lambda payload, session_id=None: (200, {}, "no session"))
    monkeypatch.setattr(demo_module.time, "sleep", lambda seconds: None)

    assert demo_module.main() == 1
