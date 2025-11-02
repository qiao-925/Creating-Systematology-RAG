"""
Git仓库管理模块 - 向后兼容层
保持向后兼容的接口导出
"""

from src.git.manager import GitRepositoryManager

__all__ = [
    'GitRepositoryManager',
]

