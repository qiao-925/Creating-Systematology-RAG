"""
GitHub URL 解析测试

测试 GitHub URL 解析功能。
"""

import pytest
from src.infrastructure.data_loader import parse_github_url


@pytest.mark.fast
class TestParseGithubUrl:
    """测试GitHub URL解析"""
    
    def test_parse_basic_url(self):
        """测试基本URL解析"""
        result = parse_github_url("https://github.com/owner/repo")
        
        assert result is not None
        assert result['owner'] == 'owner'
        assert result['repo'] == 'repo'
        assert result['branch'] == 'main'
    
    def test_parse_url_with_branch(self):
        """测试带分支的URL"""
        result = parse_github_url("https://github.com/owner/repo/tree/dev")
        
        assert result is not None
        assert result['owner'] == 'owner'
        assert result['repo'] == 'repo'
        assert result['branch'] == 'dev'
    
    def test_parse_url_without_protocol(self):
        """测试没有协议的URL"""
        result = parse_github_url("github.com/owner/repo")
        
        assert result is not None
        assert result['owner'] == 'owner'
        assert result['repo'] == 'repo'
    
    def test_parse_url_with_git_suffix(self):
        """测试带.git后缀的URL"""
        result = parse_github_url("https://github.com/owner/repo.git")
        
        assert result is not None
        assert result['repo'] == 'repo'
    
    def test_parse_invalid_url(self):
        """测试无效URL"""
        result = parse_github_url("https://gitlab.com/owner/repo")
        
        assert result is None
    
    def test_parse_incomplete_url(self):
        """测试不完整的URL"""
        result = parse_github_url("https://github.com/owner")
        
        assert result is None
