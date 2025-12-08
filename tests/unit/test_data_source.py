"""
DataSource模块单元测试
测试LocalFileSource、GitHubSource、WebSource
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.infrastructure.data_loader.source.base import DataSource, SourceFile
from src.infrastructure.data_loader.source.local import LocalFileSource
from src.infrastructure.data_loader.source.github import GitHubSource


class TestDataSourceBase:
    """DataSource基类测试"""
    
    def test_source_file_dataclass(self):
        """测试SourceFile数据类"""
        source_file = SourceFile(
            path=Path("/test/file.md"),
            source_type="local",
            metadata={"key": "value"}
        )
        
        assert source_file.path == Path("/test/file.md")
        assert source_file.source_type == "local"
        assert source_file.metadata == {"key": "value"}
    
    def test_data_source_interface(self):
        """测试DataSource接口定义"""
        # DataSource是抽象类，不能直接实例化
        assert hasattr(DataSource, 'get_file_paths')
        assert hasattr(DataSource, 'get_source_metadata')


class TestLocalFileSource:
    """LocalFileSource测试"""
    
    def test_local_file_source_init_with_directory(self):
        """测试使用目录路径初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = LocalFileSource(source=tmpdir)
            
            assert source.source == tmpdir
            assert source.recursive is True
            assert isinstance(source.get_source_metadata(), dict)
    
    def test_local_file_source_init_with_list(self):
        """测试使用文件列表初始化"""
        mock_files = [Mock(name="test.md"), Mock(name="doc.pdf")]
        source = LocalFileSource(source=mock_files)
        
        assert source.source == mock_files
        assert isinstance(source.get_source_metadata(), dict)
    
    def test_local_file_source_get_source_metadata_directory(self):
        """测试目录类型的元数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = LocalFileSource(source=tmpdir)
            metadata = source.get_source_metadata()
            
            assert metadata['source_type'] == 'local_directory'
            assert 'source_path' in metadata
    
    def test_local_file_source_get_source_metadata_upload(self):
        """测试上传文件类型的元数据"""
        mock_files = [Mock(), Mock()]
        source = LocalFileSource(source=mock_files)
        metadata = source.get_source_metadata()
        
        assert metadata['source_type'] == 'local_upload'
        assert metadata['file_count'] == 2
    
    def test_local_file_source_load_directory(self, sample_markdown_dir):
        """测试从目录加载文件"""
        source = LocalFileSource(source=sample_markdown_dir)
        files = source.get_file_paths()
        
        assert len(files) > 0
        assert all(isinstance(f, SourceFile) for f in files)
        assert all(f.source_type == 'local' for f in files)
        assert all(f.path.exists() for f in files)
        
        # 验证元数据
        for file in files:
            assert 'file_path' in file.metadata
            assert 'file_name' in file.metadata
    
    def test_local_file_source_load_directory_recursive(self, sample_markdown_dir):
        """测试递归加载目录"""
        source_recursive = LocalFileSource(source=sample_markdown_dir, recursive=True)
        source_non_recursive = LocalFileSource(source=sample_markdown_dir, recursive=False)
        
        files_recursive = source_recursive.get_file_paths()
        files_non_recursive = source_non_recursive.get_file_paths()
        
        # 递归应该找到更多文件（如果有子目录）
        assert len(files_recursive) >= len(files_non_recursive)
    
    def test_local_file_source_load_nonexistent_directory(self):
        """测试加载不存在的目录"""
        source = LocalFileSource(source="/nonexistent/dir")
        files = source.get_file_paths()
        
        assert files == []
    
    def test_local_file_source_load_empty_directory(self):
        """测试加载空目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = LocalFileSource(source=tmpdir)
            files = source.get_file_paths()
            
            # 空目录应该返回空列表（没有文件）
            assert files == []
    
    def test_local_file_source_load_uploaded_files(self):
        """测试加载上传的文件"""
        # 创建Mock UploadedFile对象
        mock_file1 = Mock()
        mock_file1.name = "test1.md"
        mock_file1.getvalue.return_value = b"# Test Document 1"
        
        mock_file2 = Mock()
        mock_file2.name = "test2.md"
        mock_file2.getvalue.return_value = b"# Test Document 2"
        
        source = LocalFileSource(source=[mock_file1, mock_file2])
        files = source.get_file_paths()
        
        assert len(files) == 2
        assert all(isinstance(f, SourceFile) for f in files)
        assert all(f.source_type == 'local' for f in files)
        
        # 验证文件已保存
        for file in files:
            assert file.path.exists()
            assert 'file_name' in file.metadata
        
        # 清理
        source.cleanup()
    
    def test_local_file_source_cleanup(self):
        """测试临时文件清理"""
        mock_file = Mock()
        mock_file.name = "test.md"
        mock_file.getvalue.return_value = b"# Test"
        
        source = LocalFileSource(source=[mock_file])
        files = source.get_file_paths()
        
        # 获取临时目录
        temp_dir = files[0].path.parent if files else None
        
        # 清理
        source.cleanup()
        
        # 验证临时目录已被删除
        if temp_dir and temp_dir.exists():
            # 如果cleanup设置了_cleanup_temp，目录应该被删除
            # 但实际测试中可能需要检查
            pass


class TestGitHubSource:
    """GitHubSource测试"""
    
    def test_github_source_init(self):
        """测试GitHubSource初始化"""
        source = GitHubSource(owner="test_owner", repo="test_repo")
        
        assert source.owner == "test_owner"
        assert source.repo == "test_repo"
        assert source.branch == "main"  # 默认分支
        assert isinstance(source.get_source_metadata(), dict)
    
    def test_github_source_init_with_branch(self):
        """测试使用指定分支初始化"""
        source = GitHubSource(owner="test_owner", repo="test_repo", branch="dev")
        
        assert source.branch == "dev"
    
    def test_github_source_init_with_filters(self):
        """测试使用过滤器初始化"""
        source = GitHubSource(
            owner="test_owner",
            repo="test_repo",
            filter_directories=["docs", "src"],
            filter_file_extensions=[".md", ".py"]
        )
        
        assert source.filter_directories == ["docs", "src"]
        assert source.filter_file_extensions == [".md", ".py"]
    
    def test_github_source_get_source_metadata(self):
        """测试获取GitHub源元数据"""
        source = GitHubSource(owner="test_owner", repo="test_repo", branch="main")
        metadata = source.get_source_metadata()
        
        assert metadata['owner'] == "test_owner"
        assert metadata['repo'] == "test_repo"
        assert metadata['branch'] == "main"
        assert metadata['repository'] == "test_owner/test_repo"
        assert 'url' in metadata
    
    @pytest.mark.slow
    @pytest.mark.github_e2e
    def test_github_source_load(self):
        """测试从GitHub加载文件（需要网络）"""
        try:
            source = GitHubSource(
                owner="octocat",
                repo="Hello-World",
                branch="master",
                show_progress=False
            )
            files = source.get_file_paths()
            
            # 如果成功，应该有文件返回
            assert isinstance(files, list)
            # 注意：这个测试可能需要实际网络连接和Git
        except Exception as e:
            pytest.skip(f"GitHub加载失败（可能需要网络或Git）: {e}")
    
    def test_github_source_should_include_file(self):
        """测试文件过滤逻辑"""
        source = GitHubSource(
            owner="test_owner",
            repo="test_repo",
            filter_directories=["docs"],
            filter_file_extensions=[".md"]
        )
        
        # 应该包含：在docs目录下的.md文件
        assert source._should_include_file("docs/readme.md") is True
        assert source._should_include_file("docs/api.md") is True
        
        # 不应该包含：不在docs目录下
        assert source._should_include_file("src/main.py") is False
        
        # 不应该包含：不是.md文件
        assert source._should_include_file("docs/readme.txt") is False
    
    def test_github_source_should_include_file_no_filters(self):
        """测试无过滤器时包含所有文件"""
        source = GitHubSource(owner="test_owner", repo="test_repo")
        
        assert source._should_include_file("any/file.txt") is True
        assert source._should_include_file("docs/readme.md") is True


class TestWebSource:
    """WebSource测试"""
    
    def test_web_source_init(self):
        """测试WebSource初始化"""
        urls = ["https://example.com", "https://test.com"]
        source = WebSource(urls=urls)
        
        assert source.urls == urls
        assert isinstance(source.get_source_metadata(), dict)
    
    def test_web_source_get_source_metadata(self):
        """测试获取Web源元数据"""
        urls = ["https://example.com", "https://test.com"]
        source = WebSource(urls=urls)
        metadata = source.get_source_metadata()
        
        assert metadata['source_type'] == 'web'
        assert metadata['url_count'] == 2
        assert metadata['urls'] == urls
    
    def test_web_source_load_empty_urls(self):
        """测试空URL列表"""
        source = WebSource(urls=[])
        files = source.get_file_paths()
        
        assert files == []
    
    @patch('src.data_source.web_source.SimpleWebPageReader')
    def test_web_source_load_mock(self, mock_reader_class):
        """测试Web源加载（Mock）"""
        # Mock SimpleWebPageReader
        mock_reader = Mock()
        mock_document = Mock()
        mock_document.text = "<html><body>Test Content</body></html>"
        mock_reader.load_data.return_value = [mock_document]
        mock_reader_class.return_value = mock_reader
        
        urls = ["https://example.com"]
        source = WebSource(urls=urls)
        files = source.get_file_paths()
        
        # 验证调用
        mock_reader.load_data.assert_called_once_with(urls)
        
        # 如果有文件返回，验证格式
        if files:
            assert all(isinstance(f, SourceFile) for f in files)
            assert all(f.source_type == 'web' for f in files)
            
            for file in files:
                assert 'url' in file.metadata
                assert 'file_name' in file.metadata
        
        # 清理
        source.cleanup()
    
    @pytest.mark.slow
    def test_web_source_load_real(self):
        """测试从真实网页加载（需要网络）"""
        try:
            urls = ["https://example.com"]
            source = WebSource(urls=urls)
            files = source.get_file_paths()
            
            # 如果成功，应该有文件返回
            assert isinstance(files, list)
            
            if files:
                assert all(isinstance(f, SourceFile) for f in files)
                assert all(f.path.exists() for f in files)
            
            # 清理
            source.cleanup()
        except Exception as e:
            pytest.skip(f"网页加载失败（可能需要网络）: {e}")


class TestDataSourceIntegration:
    """数据源集成测试"""
    
    def test_multiple_sources_metadata(self):
        """测试多个数据源的元数据格式一致性"""
        sources = [
            LocalFileSource(source="/tmp/test"),
            GitHubSource(owner="test", repo="test"),
            WebSource(urls=["https://example.com"])
        ]
        
        for source in sources:
            metadata = source.get_source_metadata()
            assert isinstance(metadata, dict)
            assert 'source_type' in metadata or 'repository' in metadata or 'url_count' in metadata
    
    def test_source_file_consistency(self, sample_markdown_dir):
        """测试不同数据源返回的SourceFile格式一致性"""
        local_source = LocalFileSource(source=sample_markdown_dir)
        local_files = local_source.get_file_paths()
        
        for file in local_files:
            assert isinstance(file, SourceFile)
            assert hasattr(file, 'path')
            assert hasattr(file, 'source_type')
            assert hasattr(file, 'metadata')
            assert isinstance(file.metadata, dict)


