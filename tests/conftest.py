"""
pytest配置和共享fixtures
"""

import os
import sys
import pytest
from pathlib import Path

# 添加src到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))


# ==================== 环境配置 ====================

@pytest.fixture(scope="session")
def project_root():
    """项目根目录"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent / "fixtures" / "sample_docs"


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """为所有测试设置基本环境变量"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_key_12345")
    monkeypatch.setenv("CHUNK_SIZE", "256")
    monkeypatch.setenv("CHUNK_OVERLAP", "20")
    monkeypatch.setenv("SIMILARITY_TOP_K", "3")


# ==================== 临时目录 ====================

@pytest.fixture
def temp_vector_store(tmp_path):
    """临时向量存储目录"""
    store_path = tmp_path / "test_vector_store"
    store_path.mkdir()
    return store_path


@pytest.fixture
def temp_data_dir(tmp_path):
    """临时数据目录"""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir


# ==================== 测试文档 ====================

@pytest.fixture
def sample_markdown_file(tmp_path):
    """创建单个测试Markdown文件"""
    md_file = tmp_path / "test_doc.md"
    content = """# 系统科学简介

系统科学是研究系统的一般规律和方法的科学。

## 主要分支

系统科学包括以下分支：
- 系统论
- 控制论
- 信息论
"""
    md_file.write_text(content, encoding='utf-8')
    return md_file


@pytest.fixture
def sample_markdown_dir(tmp_path):
    """创建包含多个Markdown文件的目录"""
    data_dir = tmp_path / "sample_data"
    data_dir.mkdir()
    
    # 文档1
    (data_dir / "doc1.md").write_text(
        "# 系统科学\n\n系统科学研究系统的一般规律。",
        encoding='utf-8'
    )
    
    # 文档2
    (data_dir / "doc2.md").write_text(
        "# 钱学森\n\n钱学森是中国系统科学的创建者之一。",
        encoding='utf-8'
    )
    
    # 子目录和文档3
    subdir = data_dir / "subdir"
    subdir.mkdir()
    (subdir / "doc3.md").write_text(
        "# 系统工程\n\n系统工程是一种组织管理技术。",
        encoding='utf-8'
    )
    
    return data_dir


@pytest.fixture
def sample_documents():
    """创建LlamaIndex Document对象列表"""
    from llama_index.core import Document
    
    return [
        Document(
            text="系统科学是研究系统的一般规律和方法的科学。它包括系统论、控制论、信息论等分支。",
            metadata={"title": "系统科学", "source": "test", "id": 1}
        ),
        Document(
            text="钱学森是中国著名科学家，被誉为中国航天之父。他在系统科学领域做出了杰出贡献。",
            metadata={"title": "钱学森", "source": "test", "id": 2}
        ),
        Document(
            text="系统工程是一种组织管理技术，用于解决大规模复杂系统的设计和实施问题。",
            metadata={"title": "系统工程", "source": "test", "id": 3}
        )
    ]


# ==================== Mock配置 ====================

@pytest.fixture
def mock_openai_response(mocker):
    """Mock OpenAI API响应"""
    mock_llm = mocker.Mock()
    mock_llm.complete.return_value.text = "这是一个测试回答。系统科学是研究系统的科学。"
    return mock_llm


# ==================== 跳过条件 ====================

def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line(
        "markers",
        "requires_real_api: 需要真实API密钥的测试"
    )


def pytest_collection_modifyitems(config, items):
    """根据环境变量跳过需要API的测试"""
    # 检查是否有真实的API密钥
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

@pytest.fixture(autouse=True)
def test_header(request):
    """在每个测试前后打印分隔线"""
    print(f"\n{'=' * 60}")
    print(f"测试: {request.node.name}")
    print(f"{'=' * 60}")
    yield
    print(f"{'=' * 60}\n")

