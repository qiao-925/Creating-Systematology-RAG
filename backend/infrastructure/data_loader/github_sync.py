"""
GitHub同步模块：增量同步GitHub仓库，使用新的DataImportService

主要功能：
- sync_github_repository()：增量同步GitHub仓库，支持两级检测机制

执行流程：
1. 快速检测：比较commit SHA，无变化直接跳过
2. 精细检测：文件级哈希比对，只索引变更文件
3. 使用DataImportService进行导入
4. 返回同步结果

特性：
- 增量同步机制
- 两级检测（快速+精细）
- 支持目录和文件扩展名过滤
- 完整的进度反馈
"""

from typing import List, Optional

from backend.infrastructure.logger import get_logger
from backend.infrastructure.data_loader.service import DataImportService

logger = get_logger('data_loader')


def sync_github_repository(
    owner: str,
    repo: str,
    branch: str,
    github_sync_manager,
    show_progress: bool = True,
    filter_directories: Optional[List[str]] = None,
    filter_file_extensions: Optional[List[str]] = None
) -> tuple:
    """增量同步 GitHub 仓库（仅支持公开仓库）
    
    使用两级检测机制：
    1. 快速检测：比较 commit SHA，无变化直接跳过
    2. 精细检测：文件级哈希比对，只索引变更文件
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        branch: 分支名称
        github_sync_manager: GitHub同步管理器实例
        show_progress: 是否显示进度
        filter_directories: 只加载指定目录（可选）
        filter_file_extensions: 只加载指定扩展名（可选）
        
    Returns:
        (所有文档列表, FileChange对象, commit_sha)
    """
    # 使用新的统一服务
    service = DataImportService(show_progress=show_progress, enable_cache=True)
    return service.sync_github_repository(
        owner=owner,
        repo=repo,
        branch=branch,
        github_sync_manager=github_sync_manager,
        filter_directories=filter_directories,
        filter_file_extensions=filter_file_extensions
    )

