"""
pytest核心配置

只保留核心配置和全局设置，具体 fixtures 已拆分到 tests/fixtures/ 模块。
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# 添加src到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# ==================== 全局 Mock 依赖 ====================
# 在导入任何模块之前 mock 可选依赖，避免导入错误

# Mock chromadb 模块（测试环境必须使用 Mock，避免调用真实 API）
try:
    import chromadb
    # 即使 chromadb 已安装，也要 Mock 客户端类，避免测试调用真实 API
    chromadb.PersistentClient = MagicMock
    chromadb.Client = MagicMock
    chromadb.CloudClient = MagicMock  # Mock CloudClient，避免调用真实 Chroma Cloud API
    # Mock chromadb.errors 模块
    if not hasattr(chromadb, 'errors'):
        chromadb.errors = MagicMock()
    if not hasattr(chromadb.errors, 'ChromaAuthError'):
        chromadb.errors.ChromaAuthError = Exception
except ImportError:
    # 如果 chromadb 未安装，创建完整的 Mock
    chromadb = MagicMock()
    chromadb.PersistentClient = MagicMock
    chromadb.Client = MagicMock
    chromadb.CloudClient = MagicMock
    chromadb.errors = MagicMock()
    chromadb.errors.ChromaAuthError = Exception
    chromadb.Collection = MagicMock
    sys.modules['chromadb'] = chromadb

# Mock llama_index.vector_stores.chroma 模块（如果未安装）
try:
    from llama_index.vector_stores.chroma import ChromaVectorStore
except ImportError:
    ChromaVectorStore = MagicMock
    chroma_vector_store_module = MagicMock()
    chroma_vector_store_module.ChromaVectorStore = ChromaVectorStore
    vector_stores_module = MagicMock()
    vector_stores_module.chroma = chroma_vector_store_module
    llama_index_module = MagicMock()
    llama_index_module.vector_stores = vector_stores_module
    sys.modules['llama_index.vector_stores.chroma'] = chroma_vector_store_module
    sys.modules['llama_index.vector_stores'] = vector_stores_module

# 设置环境编码为 UTF-8（Windows兼容）
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# ==================== 环境配置 ====================

@pytest.fixture(scope="session")
def project_root():
    """项目根目录"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent / "fixtures" / "sample_docs"


@pytest.fixture(autouse=True, scope="session")
def patch_deepseek_support():
    """全局 patch llama_index 和 tiktoken 以支持 DeepSeek 模型"""
    patches = []
    
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
        patches.append(('openai_utils', original_fn))
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
        patches.append(('tiktoken', original_encoding_fn))
    except ImportError:
        pass
    
    yield
    
    # 恢复原始函数
    for patch_type, original_fn in patches:
        if patch_type == 'openai_utils':
            from llama_index.llms.openai import utils as openai_utils
            openai_utils.openai_modelname_to_contextsize = original_fn
        elif patch_type == 'tiktoken':
            import tiktoken
            tiktoken.encoding_for_model = original_fn


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """为所有测试设置基本环境变量"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_key_12345")
    monkeypatch.setenv("CHUNK_SIZE", "256")
    monkeypatch.setenv("CHUNK_OVERLAP", "20")
    monkeypatch.setenv("SIMILARITY_TOP_K", "3")
    # 确保测试环境不会使用真实的 Chroma Cloud API
    monkeypatch.setenv("CHROMA_CLOUD_API_KEY", "test_mock_api_key")
    monkeypatch.setenv("CHROMA_CLOUD_DATABASE", "test_mock_database")
    monkeypatch.setenv("CHROMA_CLOUD_TENANT", "test_mock_tenant")


@pytest.fixture(autouse=True)
def mock_chromadb_client(monkeypatch):
    """全局 Mock ChromaDB 客户端，确保测试不会调用真实 API"""
    try:
        import chromadb
        from unittest.mock import MagicMock
        
        # 创建 Mock 的 CloudClient 实例
        def create_mock_cloud_client(*args, **kwargs):
            """创建 Mock 的 CloudClient，返回预配置的 Mock 对象"""
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_collection.count.return_value = 0
            mock_collection.get.return_value = {"ids": [], "documents": [], "metadatas": []}
            mock_collection.query.return_value = {"ids": [], "documents": [], "metadatas": []}
            mock_collection.add.return_value = None
            mock_collection.update.return_value = None
            mock_collection.delete.return_value = None
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_client.get_collection.return_value = mock_collection
            mock_client.list_collections.return_value = []
            mock_client.delete_collection.return_value = None
            return mock_client
        
        # 替换 CloudClient 类为返回 Mock 实例的函数
        monkeypatch.setattr(chromadb, "CloudClient", create_mock_cloud_client)
        
        # 同时替换 PersistentClient 和 Client（如果存在）
        monkeypatch.setattr(chromadb, "PersistentClient", create_mock_cloud_client)
        monkeypatch.setattr(chromadb, "Client", create_mock_cloud_client)
        
    except ImportError:
        pass


def pytest_runtest_setup(item):
    """在测试运行前检查是否应该跳过"""
    pass


# ==================== pytest 配置 ====================

def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line("markers", "requires_real_api: 需要真实API密钥的测试")
    config.addinivalue_line("markers", "github_e2e: GitHub端到端集成测试")
    config.addinivalue_line("markers", "pending_practice: 待实践验证的测试")
    config.addinivalue_line("markers", "fast: 快速测试（不依赖外部资源）")
    config.addinivalue_line("markers", "slow: 慢速测试（需要真实API或网络）")


def pytest_collection_modifyitems(config, items):
    """根据环境变量跳过需要API的测试"""
    has_api_key = os.getenv("DEEPSEEK_API_KEY") and \
                  not os.getenv("DEEPSEEK_API_KEY").startswith("test_")
    
    if not has_api_key:
        skip_api = pytest.mark.skip(
            reason="需要真实的DEEPSEEK_API_KEY环境变量（当前是mock值）"
        )
        for item in items:
            if "requires_real_api" in item.keywords or "slow" in item.keywords:
                item.add_marker(skip_api)


# ==================== 测试输出美化 ====================

# 注释掉 test_header，减少输出噪音（可选）
# @pytest.fixture(autouse=True)
# def test_header(request):
#     """在每个测试前后打印分隔线"""
#     print(f"\n{'=' * 60}")
#     print(f"测试: {request.node.name}")
#     print(f"{'=' * 60}")
#     yield
#     print(f"{'=' * 60}\n")

# 注意：fixtures 已拆分到 tests/fixtures/ 目录
# 显式导入 fixtures 模块以确保 pytest 能够发现它们
pytest_plugins = [
    "tests.fixtures.data",
    "tests.fixtures.indexer",
    "tests.fixtures.github",
    "tests.fixtures.embeddings",
    "tests.fixtures.llm",
    "tests.fixtures.mocks",
]

