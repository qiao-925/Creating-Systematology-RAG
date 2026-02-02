"""
UI smoke tests aligned to the single-page frontend architecture.
These tests avoid Streamlit runtime side effects by mocking the module.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


class SessionStateStub(dict):
    """Streamlit-like session_state with dict + attribute access."""

    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value) -> None:
        self[name] = value


@pytest.fixture(autouse=True)
def mock_streamlit():
    """Provide a minimal Streamlit stub for module imports."""
    with patch.dict(sys.modules, {"streamlit": MagicMock()}):
        import streamlit as st
        st.session_state = SessionStateStub()
        yield st


def test_app_entrypoint_points_to_frontend_main():
    app_path = PROJECT_ROOT / "app.py"
    assert app_path.exists()
    content = app_path.read_text(encoding="utf-8")
    assert "from frontend.main import main" in content


def test_frontend_main_has_main():
    main_path = PROJECT_ROOT / "frontend" / "main.py"
    assert main_path.exists()
    content = main_path.read_text(encoding="utf-8")
    assert "def main" in content


def test_streamlit_config_sets_page_config(mock_streamlit):
    from frontend.config import configure_streamlit

    configure_streamlit()
    mock_streamlit.set_page_config.assert_called()


def test_sources_formatting_utility(mock_streamlit):
    from frontend.utils.sources import format_answer_with_citation_links

    result = format_answer_with_citation_links("Answer [1]", [])
    assert isinstance(result, str)


def test_core_components_importable(mock_streamlit):
    from frontend.components.file_viewer import resolve_file_path
    from frontend.components.settings_dialog import show_settings_dialog
    from frontend.components.sources_panel import display_sources_below_message

    assert callable(resolve_file_path)
    assert callable(show_settings_dialog)
    assert callable(display_sources_below_message)


def test_state_helpers_importable(mock_streamlit):
    from frontend.utils.state import init_session_state

    assert callable(init_session_state)
