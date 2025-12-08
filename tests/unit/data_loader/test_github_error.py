"""
GitHub 错误处理测试

测试 GitHub 错误处理功能。
"""

import pytest
from src.infrastructure.data_loader import _handle_github_error


@pytest.mark.fast
class TestHandleGithubError:
    """测试GitHub错误处理"""
    
    def test_handle_404_error(self):
        """测试404错误"""
        error = Exception("404: Repository not found")
        msg = _handle_github_error(error, "owner", "repo", show_progress=False)
        
        assert "仓库不存在(404)" in msg
    
    def test_handle_403_error(self):
        """测试403错误"""
        error = Exception("403: Forbidden - rate limit exceeded")
        msg = _handle_github_error(error, "owner", "repo", show_progress=False)
        
        assert "访问被拒绝(403)" in msg
    
    def test_handle_401_error(self):
        """测试401错误"""
        error = Exception("401: Unauthorized - Bad credentials")
        msg = _handle_github_error(error, "owner", "repo", show_progress=False)
        
        assert "认证失败(401)" in msg
    
    def test_handle_timeout_error(self):
        """测试超时错误"""
        error = Exception("Request timed out")
        msg = _handle_github_error(error, "owner", "repo", show_progress=False)
        
        assert "网络超时" in msg
    
    def test_handle_connection_error(self):
        """测试连接错误"""
        error = Exception("Connection refused")
        msg = _handle_github_error(error, "owner", "repo", show_progress=False)
        
        assert "网络连接失败" in msg
    
    def test_handle_generic_error(self):
        """测试通用错误"""
        error = ValueError("Some other error")
        msg = _handle_github_error(error, "owner", "repo", show_progress=False)
        
        assert "ValueError" in msg
