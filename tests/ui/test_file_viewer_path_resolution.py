"""
Path resolution tests for frontend.components.file_viewer.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class _Ctx:
    """Minimal context manager for Streamlit expander stubs."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def _load_file_viewer_module():
    """Import file_viewer with a minimal Streamlit stub."""
    streamlit_stub = SimpleNamespace(
        dialog=lambda *args, **kwargs: (lambda fn: fn),
        markdown=lambda *args, **kwargs: None,
        caption=lambda *args, **kwargs: None,
        expander=lambda *args, **kwargs: _Ctx(),
        code=lambda *args, **kwargs: None,
        download_button=lambda *args, **kwargs: None,
        divider=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
        info=lambda *args, **kwargs: None,
        text=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
    )

    with patch.dict(sys.modules, {"streamlit": streamlit_stub}):
        sys.modules.pop("frontend.components.file_viewer", None)
        return importlib.import_module("frontend.components.file_viewer")


def test_resolve_file_path_can_fallback_to_sibling_repo(tmp_path, monkeypatch):
    """Should find file in sibling repo when metadata path is historical relative path."""
    project_root = tmp_path / "Creating-Systematology-RAG"
    project_root.mkdir()

    sibling_pdf = (
        tmp_path
        / "Creating-Systematology"
        / "# 系统科学资源"
        / "知网文献PDF"
        / "钱学森 主题 于景元 作者（共37篇）"
        / "钱学森系统科学思想和系统科学体系_于景元.pdf"
    )
    sibling_pdf.parent.mkdir(parents=True)
    sibling_pdf.write_bytes(b"%PDF-1.4 test")

    file_viewer = _load_file_viewer_module()
    file_viewer._search_filename_under_root.cache_clear()

    monkeypatch.setattr(file_viewer.config, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(
        file_viewer,
        "get_file_search_paths",
        lambda: [project_root, project_root / "data" / "raw"],
    )

    resolved = file_viewer.resolve_file_path(
        "钱学森 主题 于景元 作者（共37篇）/钱学森系统科学思想和系统科学体系_于景元.pdf"
    )
    assert resolved == sibling_pdf


def test_resolve_file_path_prefers_best_suffix_match(tmp_path, monkeypatch):
    """When filename duplicates exist, resolver should prefer best path suffix match."""
    project_root = tmp_path / "Creating-Systematology-RAG"
    project_root.mkdir()

    preferred = (
        tmp_path
        / "Creating-Systematology"
        / "钱学森 主题 于景元 作者（共37篇）"
        / "钱学森系统科学思想和系统科学体系_于景元.pdf"
    )
    preferred.parent.mkdir(parents=True)
    preferred.write_bytes(b"%PDF-1.4 preferred")

    other = (
        tmp_path
        / "OtherRepo"
        / "docs"
        / "钱学森系统科学思想和系统科学体系_于景元.pdf"
    )
    other.parent.mkdir(parents=True)
    other.write_bytes(b"%PDF-1.4 other")

    file_viewer = _load_file_viewer_module()
    file_viewer._search_filename_under_root.cache_clear()

    monkeypatch.setattr(file_viewer.config, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(
        file_viewer,
        "get_file_search_paths",
        lambda: [project_root, project_root / "data" / "raw"],
    )

    resolved = file_viewer.resolve_file_path(
        "钱学森 主题 于景元 作者（共37篇）/钱学森系统科学思想和系统科学体系_于景元.pdf"
    )
    assert resolved == preferred
