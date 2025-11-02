"""
Git仓库管理 - 工具函数模块
Git操作相关的工具函数
"""

import subprocess
from pathlib import Path

from src.logger import setup_logger

logger = setup_logger('git_repository_manager')


def get_commit_sha(repo_path: Path) -> str:
    """获取当前 commit SHA
    
    Args:
        repo_path: 本地仓库路径
        
    Returns:
        完整的 commit SHA（40字符）
        
    Raises:
        RuntimeError: 获取失败时
    """
    try:
        cmd = ['git', 'rev-parse', 'HEAD']
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"获取 commit SHA 失败: {result.stderr}")
        
        commit_sha = result.stdout.strip()
        
        # 验证格式（40字符的十六进制）
        if len(commit_sha) != 40 or not all(c in '0123456789abcdef' for c in commit_sha.lower()):
            raise RuntimeError(f"无效的 commit SHA: {commit_sha}")
        
        return commit_sha
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("获取 commit SHA 超时")

