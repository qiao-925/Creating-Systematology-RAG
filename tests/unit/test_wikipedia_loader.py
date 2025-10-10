"""
维基百科加载器测试
"""

import pytest
from src.data_loader import load_documents_from_wikipedia


def test_load_wikipedia_basic():
    """测试基本的维基百科加载功能"""
    # 加载一个简单的页面
    docs = load_documents_from_wikipedia(
        pages=["Python (programming language)"],
        lang="en",
        auto_suggest=True,
        clean=True,
        show_progress=False
    )
    
    # 验证结果
    assert docs is not None
    assert len(docs) > 0
    
    # 验证元数据
    doc = docs[0]
    assert doc.metadata.get('source_type') == 'wikipedia'
    assert doc.metadata.get('language') == 'en'
    assert 'wikipedia_url' in doc.metadata
    assert 'Python' in doc.metadata.get('title', '')


def test_load_wikipedia_chinese():
    """测试中文维基百科加载"""
    docs = load_documents_from_wikipedia(
        pages=["系统科学"],
        lang="zh",
        auto_suggest=True,
        clean=True,
        show_progress=False
    )
    
    assert docs is not None
    assert len(docs) > 0
    assert docs[0].metadata.get('language') == 'zh'


def test_load_wikipedia_multiple_pages():
    """测试加载多个页面"""
    docs = load_documents_from_wikipedia(
        pages=["Python", "Java"],
        lang="en",
        auto_suggest=True,
        clean=True,
        show_progress=False
    )
    
    # 应该加载到至少1个页面（可能某个页面不存在）
    assert docs is not None
    assert len(docs) >= 1


def test_load_wikipedia_nonexistent_page():
    """测试加载不存在的页面"""
    docs = load_documents_from_wikipedia(
        pages=["ThisPageDefinitelyDoesNotExist12345"],
        lang="en",
        auto_suggest=False,
        clean=True,
        show_progress=False
    )
    
    # 不存在的页面应该返回空列表
    assert docs == []


def test_load_wikipedia_empty_list():
    """测试空页面列表"""
    docs = load_documents_from_wikipedia(
        pages=[],
        lang="en",
        show_progress=False
    )
    
    assert docs == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

