"""
E2E conftest：覆盖全局 mock，使用真实 API

全局 conftest 做了两层 mock：
  1. 模块级：chromadb.CloudClient = MagicMock（import 时）
  2. fixture 级：mock_env_vars / mock_chromadb_client（autouse）
这里恢复两层，让 E2E 测试连接真实服务。
"""

from __future__ import annotations

import importlib
import os

import pytest
from dotenv import load_dotenv

# ── 恢复 chromadb 真实类（被全局 conftest 替换为 MagicMock） ──
# reload chromadb 包拿回原始定义
import chromadb
importlib.reload(chromadb)

# 清除 ChromaClientManager 单例缓存（可能缓存了 mock 实例）
try:
    from backend.infrastructure.indexer.core.chroma_client import ChromaClientManager
    ChromaClientManager._client = None
    ChromaClientManager._collections = {}
except ImportError:
    pass


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """覆盖全局 mock：加载真实 .env"""
    load_dotenv(override=True)

    required = ["DEEPSEEK_API_KEY", "CHROMA_CLOUD_API_KEY", "CHROMA_CLOUD_TENANT", "CHROMA_CLOUD_DATABASE"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        pytest.skip(f"E2E 需要真实环境变量: {', '.join(missing)}")


@pytest.fixture(autouse=True)
def mock_chromadb_client():
    """覆盖全局 mock：不 mock Chroma，使用真实连接"""
    yield
