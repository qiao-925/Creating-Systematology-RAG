"""
Git仓库管理模块 - 向后兼容层：保持向后兼容的接口导出

主要功能：
- GitRepositoryManager类：Git仓库本地管理器，管理GitHub仓库的本地克隆和增量更新

执行流程：
1. 克隆或更新Git仓库
2. 管理本地仓库路径
3. 支持增量更新（git pull）

特性：
- 仓库克隆和更新
- 增量更新支持
- 完整的错误处理
"""

from backend.infrastructure.git.manager import GitRepositoryManager

__all__ = [
    'GitRepositoryManager',
]

