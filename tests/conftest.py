"""
pytest core configuration and global test stubs.
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tests.fixtures.chroma_fake import FakeChromaClient


# Ensure project root is importable
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# -------------------- Global dependency stubs --------------------

class SessionStateStub(dict):
    """Streamlit-like session_state with dict + attribute access."""

    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value) -> None:
        self[name] = value


# Streamlit stub (avoid requiring the real runtime)
streamlit_stub = MagicMock()
streamlit_stub.session_state = SessionStateStub()
sys.modules["streamlit"] = streamlit_stub


# ChromaDB stub (avoid real API usage and missing dependency errors)
try:
    import chromadb  # noqa: F401
    chromadb.PersistentClient = MagicMock
    chromadb.Client = MagicMock
    chromadb.CloudClient = MagicMock
    if not hasattr(chromadb, "errors"):
        chromadb.errors = MagicMock()
    if not hasattr(chromadb.errors, "ChromaAuthError"):
        chromadb.errors.ChromaAuthError = Exception
except ImportError:
    chromadb = MagicMock()
    chromadb.PersistentClient = MagicMock
    chromadb.Client = MagicMock
    chromadb.CloudClient = MagicMock
    chromadb.errors = MagicMock()
    chromadb.errors.ChromaAuthError = Exception
    chromadb.Collection = MagicMock
    sys.modules["chromadb"] = chromadb

# Ensure chromadb.api.models.Collection import works even when mocked
chromadb_api_module = sys.modules.get("chromadb.api") or types.ModuleType("chromadb.api")
chromadb_models_module = sys.modules.get("chromadb.api.models") or types.ModuleType("chromadb.api.models")
chromadb_collection_module = sys.modules.get("chromadb.api.models.Collection") or types.ModuleType(
    "chromadb.api.models.Collection"
)
chromadb_collection_module.Collection = getattr(chromadb_collection_module, "Collection", MagicMock)
chromadb_api_module.models = chromadb_models_module
chromadb_models_module.Collection = chromadb_collection_module
sys.modules["chromadb.api"] = chromadb_api_module
sys.modules["chromadb.api.models"] = chromadb_models_module
sys.modules["chromadb.api.models.Collection"] = chromadb_collection_module


# LlamaIndex chroma vector store stub (if missing)
try:
    from llama_index.vector_stores.chroma import ChromaVectorStore  # noqa: F401
except ImportError:
    chroma_vector_store_module = MagicMock()
    chroma_vector_store_module.ChromaVectorStore = MagicMock
    vector_stores_module = MagicMock()
    vector_stores_module.chroma = chroma_vector_store_module
    sys.modules["llama_index.vector_stores.chroma"] = chroma_vector_store_module
    sys.modules["llama_index.vector_stores"] = vector_stores_module


# Windows UTF-8 console setup
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    import io

    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


# -------------------- Fixtures --------------------

@pytest.fixture(scope="session")
def project_root():
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def test_data_dir():
    return Path(__file__).parent / "fixtures" / "sample_docs"


@pytest.fixture(autouse=True, scope="session")
def patch_deepseek_support():
    patches: list[tuple[str, object]] = []

    try:
        from llama_index.llms.openai import utils as openai_utils

        original_fn = openai_utils.openai_modelname_to_contextsize

        def patched_context_fn(modelname: str) -> int:
            if "deepseek" in modelname.lower():
                return 32768
            try:
                return original_fn(modelname)
            except ValueError:
                return 4096

        openai_utils.openai_modelname_to_contextsize = patched_context_fn
        patches.append(("openai_utils", original_fn))
    except ImportError:
        pass

    try:
        import tiktoken

        original_encoding_fn = tiktoken.encoding_for_model

        def patched_encoding_fn(model_name: str):
            if "deepseek" in model_name.lower():
                return tiktoken.get_encoding("cl100k_base")
            return original_encoding_fn(model_name)

        tiktoken.encoding_for_model = patched_encoding_fn
        patches.append(("tiktoken", original_encoding_fn))
    except ImportError:
        pass

    yield

    for patch_type, original_fn in patches:
        if patch_type == "openai_utils":
            from llama_index.llms.openai import utils as openai_utils

            openai_utils.openai_modelname_to_contextsize = original_fn
        elif patch_type == "tiktoken":
            import tiktoken

            tiktoken.encoding_for_model = original_fn


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_key_12345")
    monkeypatch.setenv("CHUNK_SIZE", "256")
    monkeypatch.setenv("CHUNK_OVERLAP", "20")
    monkeypatch.setenv("SIMILARITY_TOP_K", "3")
    monkeypatch.setenv("CHROMA_CLOUD_API_KEY", "test_mock_api_key")
    monkeypatch.setenv("CHROMA_CLOUD_DATABASE", "test_mock_database")
    monkeypatch.setenv("CHROMA_CLOUD_TENANT", "test_mock_tenant")


@pytest.fixture(autouse=True)
def mock_chromadb_client(monkeypatch):
    try:
        import chromadb
        from backend.infrastructure.indexer.core.chroma_client import ChromaClientManager
        from tests.fixtures.chroma_fake import FakeChromaClient

        ChromaClientManager.reset()
        monkeypatch.setattr(chromadb, "CloudClient", FakeChromaClient)
        monkeypatch.setattr(chromadb, "PersistentClient", FakeChromaClient)
        monkeypatch.setattr(chromadb, "Client", FakeChromaClient)
        yield
        ChromaClientManager.reset()
    except ImportError:
        yield


# -------------------- pytest hooks --------------------

def pytest_configure(config):
    config.addinivalue_line("markers", "requires_real_api: requires real API keys")
    config.addinivalue_line("markers", "github_e2e: GitHub end-to-end tests")
    config.addinivalue_line("markers", "pending_practice: pending practice tests")
    config.addinivalue_line("markers", "fast: fast tests without external deps")
    config.addinivalue_line("markers", "slow: slow tests requiring external deps")


def pytest_collection_modifyitems(config, items):
    has_api_key = os.getenv("DEEPSEEK_API_KEY") and not os.getenv("DEEPSEEK_API_KEY").startswith("test_")
    if not has_api_key:
        skip_api = pytest.mark.skip(
            reason="Requires real DEEPSEEK_API_KEY; test environment uses mock value."
        )
        for item in items:
            nodeid = item.nodeid.replace("\\", "/")
            is_e2e = "tests/e2e/" in nodeid
            is_perf = "tests/performance/" in nodeid
            is_integration = "tests/integration/" in nodeid

            if "requires_real_api" in item.keywords or "slow" in item.keywords:
                item.add_marker(skip_api)
            elif is_e2e or is_perf:
                item.add_marker(skip_api)
            elif is_integration and "fast" not in item.keywords:
                item.add_marker(skip_api)


# Explicitly import shared fixtures
pytest_plugins = [
    "tests.fixtures.data",
    "tests.fixtures.indexer",
    "tests.fixtures.github",
    "tests.fixtures.embeddings",
    "tests.fixtures.llm",
    "tests.fixtures.mocks",
]


def _uses_real_embedding_tests(nodeid: str) -> bool:
    normalized = nodeid.replace("\\", "/")
    file_nodeid = normalized.split("::", 1)[0]
    return (
        "tests/unit/embeddings/" in normalized
        or file_nodeid.endswith("tests/unit/test_embeddings_factory.py")
        or file_nodeid.endswith("tests/unit/test_hf_inference_embedding.py")
    )


@pytest.fixture(autouse=True)
def mock_indexer_embeddings(request, monkeypatch):
    """为非 embedding 专项测试提供离线 embedding，避免依赖 HF_TOKEN/network。"""
    if _uses_real_embedding_tests(request.node.nodeid):
        yield
        return

    from llama_index.core.embeddings import MockEmbedding
    import backend.infrastructure.indexer.core.init as indexer_init
    import backend.infrastructure.embeddings.factory as embedding_factory

    embedding = MockEmbedding(embed_dim=8, model_name="test-mock-embedding")

    monkeypatch.setattr(indexer_init, "get_embedding_instance", lambda: None)
    monkeypatch.setattr(indexer_init, "create_embedding", lambda *args, **kwargs: embedding)
    monkeypatch.setattr(embedding_factory, "get_embedding_instance", lambda: None)
    monkeypatch.setattr(embedding_factory, "create_embedding", lambda *args, **kwargs: embedding)
    embedding_factory.clear_embedding_cache()

    yield

    embedding_factory.clear_embedding_cache()
