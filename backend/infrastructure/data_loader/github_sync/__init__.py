"""
GitHub同步管理模块 - 向后兼容层：保持向后兼容的接口导出

主要功能：
- FileChange类：文件变更记录类，包含新增、修改、删除的文件列表
- GitHubSyncManager类：GitHub同步管理器，管理GitHub仓库的同步状态，追踪文件变化
- sync_github_repository()：增量同步GitHub仓库的函数

执行流程：
1. 初始化GitHub同步管理器
2. 检测文件变更
3. 更新同步状态
4. 支持增量更新

特性：
- 文件变更追踪
- 同步状态持久化
- 增量更新支持
- 完整的错误处理
"""

from backend.infrastructure.data_loader.github_sync.file_change import FileChange
from backend.infrastructure.data_loader.github_sync.manager import GitHubSyncManager

# 从父目录的 github_sync.py 文件导入函数（避免与目录名冲突）
# 使用 importlib 动态导入，因为文件名与目录名冲突
import importlib.util
from pathlib import Path

_parent_dir = Path(__file__).parent.parent
_sync_file_path = _parent_dir / "github_sync.py"

if _sync_file_path.exists():
    spec = importlib.util.spec_from_file_location("_github_sync_module", _sync_file_path)
    _sync_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_sync_module)
    sync_github_repository = _sync_module.sync_github_repository
else:
    # 如果文件不存在，创建一个占位符函数
    def sync_github_repository(*args, **kwargs):
        raise ImportError("github_sync.py 文件不存在")

__all__ = [
    'FileChange',
    'GitHubSyncManager',
    'sync_github_repository',
]

