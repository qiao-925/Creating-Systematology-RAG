"""
UI tests for sources_panel dialog state handling.
"""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


@dataclass
class _Ctx:
    """Simple context manager stub used by mocked Streamlit columns."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def _build_streamlit_stub() -> SimpleNamespace:
    """Create a minimal Streamlit stub for sources panel rendering."""
    return SimpleNamespace(
        session_state={},
        columns=lambda _: (_Ctx(), _Ctx()),
        markdown=lambda *args, **kwargs: None,
        button=lambda *args, **kwargs: None,
        dialog=lambda *args, **kwargs: (lambda fn: fn),
    )


def test_display_sources_resets_dialog_state_after_open():
    """Dialog should open once per trigger and reset state to avoid reopen loop."""
    streamlit_stub = _build_streamlit_stub()

    with patch.dict(sys.modules, {"streamlit": streamlit_stub}):
        sys.modules.pop("frontend.components.sources_panel", None)
        sys.modules.pop("frontend.components.file_viewer", None)
        source_panel = importlib.import_module("frontend.components.sources_panel")

        with patch(
            "frontend.components.file_viewer.show_file_viewer_dialog",
            autospec=True,
        ) as show_dialog:
            source_panel.display_sources_below_message(
                sources=[{"text": "preview text", "metadata": {}}],
                message_id="msg_case",
            )
            assert show_dialog.call_count == 0

            dialog_key = "file_viewer_below_msg_case_0_1"
            streamlit_stub.session_state[f"show_file_{dialog_key}"] = True
            streamlit_stub.session_state[f"show_file_path_{dialog_key}"] = ""

            source_panel.display_sources_below_message(
                sources=[{"text": "preview text", "metadata": {}}],
                message_id="msg_case",
            )

            show_dialog.assert_called_once_with("")
            assert streamlit_stub.session_state[f"show_file_{dialog_key}"] is False
            assert streamlit_stub.session_state[f"show_file_path_{dialog_key}"] is None


def test_display_sources_uses_unique_button_keys_when_citation_index_repeats():
    """Widget key must remain unique even if citation index duplicates."""
    streamlit_stub = _build_streamlit_stub()
    streamlit_stub.button = MagicMock()

    with patch.dict(sys.modules, {"streamlit": streamlit_stub}):
        sys.modules.pop("frontend.components.sources_panel", None)
        sys.modules.pop("frontend.components.file_viewer", None)
        source_panel = importlib.import_module("frontend.components.sources_panel")
        source_panel.display_sources_below_message(
            sources=[
                {"index": 1, "text": "a", "metadata": {}},
                {"index": 1, "text": "b", "metadata": {}},
            ],
            message_id="msg_dup",
        )

    keys = [call.kwargs["key"] for call in streamlit_stub.button.call_args_list]
    assert keys == [
        "file_viewer_below_msg_dup_0_1",
        "file_viewer_below_msg_dup_1_1",
    ]
