"""
测试数据 Fixtures

提供测试文档、文件、目录等测试数据。
"""

import pytest
from pathlib import Path
from llama_index.core import Document


@pytest.fixture
def temp_data_dir(tmp_path):
    """临时数据目录"""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir


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


@pytest.fixture(scope="module")  # 优化：module 级别，可复用
def sample_documents():
    """创建LlamaIndex Document对象列表"""
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


# ==================== 测试数据工厂 ====================

class DocumentFactory:
    """测试文档工厂"""
    
    @staticmethod
    def create_simple(text: str = "测试文档内容", metadata: dict = None) -> Document:
        """创建简单文档"""
        return Document(
            text=text,
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_with_metadata(title: str, text: str, **kwargs) -> Document:
        """创建带元数据的文档"""
        metadata = {"title": title, **kwargs}
        return Document(text=text, metadata=metadata)
    
    @staticmethod
    def create_markdown(title: str, content: str) -> Document:
        """创建Markdown格式文档"""
        text = f"# {title}\n\n{content}"
        return Document(
            text=text,
            metadata={"title": title, "source_type": "markdown"}
        )


@pytest.fixture
def document_factory():
    """文档工厂 fixture"""
    return DocumentFactory
