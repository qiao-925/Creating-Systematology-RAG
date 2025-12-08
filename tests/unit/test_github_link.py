"""
GitHub 链接生成器测试
"""
import pytest
from src.infrastructure.github_link import generate_github_url, get_display_title


class TestGitHubUrlGeneration:
    """测试 GitHub URL 生成"""
    
    def test_standard_case(self):
        """测试标准情况"""
        metadata = {
            'repository': 'qiao-925/Creating-Systematology-Test',
            'branch': 'main',
            'file_path': 'README.md'
        }
        url = generate_github_url(metadata)
        assert url == 'https://github.com/qiao-925/Creating-Systematology-Test/blob/main/README.md'
    
    def test_nested_path(self):
        """测试嵌套路径"""
        metadata = {
            'repository': 'owner/repo',
            'branch': 'dev',
            'file_path': 'docs/architecture/design.md'
        }
        url = generate_github_url(metadata)
        assert url == 'https://github.com/owner/repo/blob/dev/docs/architecture/design.md'
    
    def test_leading_slash(self):
        """测试路径有前导斜杠"""
        metadata = {
            'repository': 'owner/repo',
            'branch': 'main',
            'file_path': '/src/main.py'
        }
        url = generate_github_url(metadata)
        assert url == 'https://github.com/owner/repo/blob/main/src/main.py'
    
    def test_missing_repository(self):
        """测试缺少 repository"""
        metadata = {
            'branch': 'main',
            'file_path': 'local/test.md'
        }
        url = generate_github_url(metadata)
        assert url is None
    
    def test_missing_file_path(self):
        """测试缺少 file_path"""
        metadata = {
            'repository': 'owner/repo',
            'branch': 'main'
        }
        url = generate_github_url(metadata)
        assert url is None
    
    def test_default_branch(self):
        """测试默认分支"""
        metadata = {
            'repository': 'owner/repo',
            'file_path': 'README.md'
            # 缺少 branch，应使用默认值 'main'
        }
        url = generate_github_url(metadata)
        assert url == 'https://github.com/owner/repo/blob/main/README.md'


class TestDisplayTitle:
    """测试显示标题获取"""
    
    def test_with_title(self):
        """测试有 title 字段"""
        metadata = {'title': 'Document Title'}
        assert get_display_title(metadata) == 'Document Title'
    
    def test_with_file_name(self):
        """测试有 file_name 字段"""
        metadata = {'file_name': 'test.md'}
        assert get_display_title(metadata) == 'test.md'
    
    def test_with_file_path(self):
        """测试从 file_path 提取"""
        metadata = {'file_path': 'docs/readme.md'}
        assert get_display_title(metadata) == 'readme.md'
    
    def test_priority(self):
        """测试字段优先级"""
        metadata = {
            'title': 'Title',
            'file_name': 'file.md',
            'file_path': 'path/to/doc.md'
        }
        assert get_display_title(metadata) == 'Title'
    
    def test_empty_metadata(self):
        """测试空元数据"""
        metadata = {}
        assert get_display_title(metadata) == 'Unknown'

