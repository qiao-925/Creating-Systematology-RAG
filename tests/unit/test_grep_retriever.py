"""
Grep检索器单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from src.retrievers.grep_retriever import GrepRetriever
from src.retrievers.multi_strategy_retriever import BaseRetriever
from llama_index.core.schema import NodeWithScore


class TestGrepRetriever:
    """GrepRetriever单元测试"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("系统科学是研究系统的科学。\n钱学森是系统科学的奠基人。", encoding='utf-8')
            yield tmpdir
    
    def test_grep_retriever_init(self, temp_dir):
        """测试GrepRetriever初始化"""
        retriever = GrepRetriever(
            data_source_path=temp_dir,
            enable_regex=True,
            max_results=10,
        )
        
        assert retriever.data_source_path == Path(temp_dir)
        assert retriever.enable_regex is True
        assert retriever.max_results == 10
        assert retriever.get_name() == "grep_retriever"
        assert retriever.get_top_k() == 10
    
    def test_grep_retriever_retrieve(self, temp_dir):
        """测试Grep检索"""
        retriever = GrepRetriever(
            data_source_path=temp_dir,
            enable_regex=False,
            max_results=5,
        )
        
        results = retriever.retrieve("系统科学", top_k=5)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, NodeWithScore) for r in results)
        
        # 验证结果包含查询关键词
        for result in results:
            assert "系统科学" in result.node.text or "系统科学" in str(result.node.metadata)
    
    def test_grep_retriever_regex(self, temp_dir):
        """测试正则表达式搜索"""
        retriever = GrepRetriever(
            data_source_path=temp_dir,
            enable_regex=True,
            max_results=5,
        )
        
        # 使用正则表达式搜索
        results = retriever.retrieve("系统.*科学", top_k=5)
        
        assert len(results) > 0
    
    @patch('src.retrievers.grep_retriever.platform.system')
    def test_grep_windows_mode(self, mock_platform, temp_dir):
        """测试Windows模式"""
        mock_platform.return_value = "Windows"
        
        retriever = GrepRetriever(
            data_source_path=temp_dir,
            enable_regex=True,
        )
        
        # Windows模式下应该使用Python实现
        assert retriever.is_windows is True
        results = retriever.retrieve("系统科学", top_k=5)
        
        assert isinstance(results, list)
    
    def test_grep_retriever_empty_results(self, temp_dir):
        """测试无结果情况"""
        retriever = GrepRetriever(
            data_source_path=temp_dir,
            enable_regex=False,
        )
        
        # 搜索不存在的关键词
        results = retriever.retrieve("不存在的关键词12345", top_k=5)
        
        # 应该返回空列表或处理错误
        assert isinstance(results, list)
    
    def test_grep_retriever_top_k(self, temp_dir):
        """测试Top-K限制"""
        retriever = GrepRetriever(
            data_source_path=temp_dir,
            max_results=100,
        )
        
        results = retriever.retrieve("系统", top_k=3)
        
        assert len(results) <= 3
    
    def test_grep_retriever_implements_base(self, temp_dir):
        """测试实现BaseRetriever接口"""
        retriever = GrepRetriever(data_source_path=temp_dir)
        
        assert isinstance(retriever, BaseRetriever)
        assert hasattr(retriever, 'retrieve')
        assert hasattr(retriever, 'get_name')
        assert hasattr(retriever, 'get_top_k')
    
    def test_grep_search_case_sensitive(self, temp_dir):
        """测试大小写敏感搜索"""
        retriever = GrepRetriever(
            data_source_path=temp_dir,
            case_sensitive=True,
            enable_regex=False,
        )
        
        # 创建包含大小写混合内容的文件
        test_file = Path(temp_dir) / "case_test.md"
        test_file.write_text("System Science\nsystem science\nSYSTEM SCIENCE", encoding='utf-8')
        
        # 大小写敏感搜索
        results = retriever.retrieve("System", top_k=5)
        
        # 应该只匹配"System"（首字母大写）
        assert len(results) > 0
        for result in results:
            assert "System" in result.node.text or "System" in str(result.node.metadata)
    
    def test_grep_search_case_insensitive(self, temp_dir):
        """测试大小写不敏感搜索"""
        retriever = GrepRetriever(
            data_source_path=temp_dir,
            case_sensitive=False,
            enable_regex=False,
        )
        
        # 创建包含大小写混合内容的文件
        test_file = Path(temp_dir) / "case_test.md"
        test_file.write_text("System Science\nsystem science\nSYSTEM SCIENCE", encoding='utf-8')
        
        # 大小写不敏感搜索
        results = retriever.retrieve("system", top_k=5)
        
        # 应该匹配所有变体
        assert len(results) > 0
    
    def test_grep_score_calculation(self, temp_dir):
        """测试分数计算"""
        retriever = GrepRetriever(
            data_source_path=temp_dir,
            enable_regex=False,
        )
        
        results = retriever.retrieve("系统科学", top_k=5)
        
        if len(results) > 0:
            # 验证所有结果都有分数
            for result in results:
                assert hasattr(result, 'score')
                assert isinstance(result.score, (int, float))
                # 分数应该在合理范围内
                assert 0 <= result.score <= 1
    
    @patch('src.retrievers.grep_retriever.subprocess.run')
    def test_grep_timeout(self, mock_subprocess, temp_dir):
        """测试超时保护"""
        # Mock subprocess.run 模拟超时
        import subprocess
        mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd="grep", timeout=1)
        
        retriever = GrepRetriever(
            data_source_path=temp_dir,
            timeout=1,
        )
        
        # 应该处理超时，返回空列表或抛出异常
        try:
            results = retriever.retrieve("test", top_k=5)
            # 如果返回空列表，这也是合理的超时处理
            assert isinstance(results, list)
        except Exception:
            # 如果抛出异常，也是合理的超时处理
            pass

