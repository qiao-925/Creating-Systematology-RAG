"""
GitHub同步模块
增量同步GitHub仓库
"""

from typing import List, Optional

from src.config import config
from src.data_loader.processor import safe_print
from src.data_loader.github_loader import load_documents_from_github
from src.logger import setup_logger

logger = setup_logger('data_loader')

try:
    from src.git_repository_manager import GitRepositoryManager
except ImportError:
    GitRepositoryManager = None


def sync_github_repository(
    owner: str,
    repo: str,
    branch: str,
    metadata_manager,
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
        metadata_manager: 元数据管理器实例
        show_progress: 是否显示进度
        filter_directories: 只加载指定目录（可选）
        filter_file_extensions: 只加载指定扩展名（可选）
        
    Returns:
        (所有文档列表, FileChange对象, commit_sha, cache_manager, task_id)
    """
    from src.metadata_manager import FileChange
    
    # 初始化缓存管理器（如果启用缓存）
    cache_manager = None
    task_id = None
    if config.ENABLE_CACHE:
        try:
            from src.cache_manager import CacheManager
            cache_manager = CacheManager(config.CACHE_STATE_PATH)
            task_id = cache_manager.get_task_id(
                owner=owner,
                repo=repo,
                branch=branch,
                filter_directories=filter_directories,
                filter_file_extensions=filter_file_extensions
            )
            task_key = cache_manager.get_task_key(owner, repo, branch)
            cache_manager.init_task(task_id, task_key)
            logger.info(f"初始化缓存任务: {task_id} ({task_key})")
        except Exception as e:
            logger.warning(f"初始化缓存管理器失败，继续不使用缓存: {e}")
    
    # 步骤 1: 克隆/更新仓库，获取最新 commit SHA
    if GitRepositoryManager is None:
        logger.error("GitRepositoryManager 未安装")
        return [], FileChange(), None, cache_manager, task_id
    
    try:
        git_manager = GitRepositoryManager(config.GITHUB_REPOS_PATH)
        repo_path, commit_sha = git_manager.clone_or_update(
            owner=owner,
            repo=repo,
            branch=branch,
            cache_manager=cache_manager,
            task_id=task_id
        )
        
        if show_progress:
            safe_print(f"✅ 仓库已同步 (Commit: {commit_sha[:8]})")
        
    except RuntimeError as e:
        logger.error(f"Git 操作失败: {e}")
        if show_progress:
            safe_print(f"❌ Git 操作失败: {e}")
        return [], FileChange(), None, cache_manager, task_id
    
    # 步骤 2: 快速检测 - 检查 commit SHA 是否变化
    old_metadata = metadata_manager.get_repository_metadata(owner, repo, branch)
    
    if old_metadata:
        old_commit_sha = old_metadata.get('last_commit_sha', '')
        if old_commit_sha == commit_sha:
            # Commit 未变化，跳过加载
            if show_progress:
                safe_print(f"✅ 仓库无新提交，跳过加载")
            logger.info(f"仓库 {owner}/{repo}@{branch} 无新提交 (Commit: {commit_sha[:8]})")
            return [], FileChange(), commit_sha, cache_manager, task_id
    
    # 步骤 3: 有新提交，加载文档
    if show_progress:
        safe_print(f"\n📄 检测到新提交，正在加载文档...")
    
    documents = load_documents_from_github(
        owner=owner,
        repo=repo,
        branch=branch,
        clean=True,
        show_progress=show_progress,
        filter_directories=filter_directories,
        filter_file_extensions=filter_file_extensions
    )
    
    if not documents:
        logger.warning(f"未能加载任何文档从 {owner}/{repo}")
        return [], FileChange(), commit_sha, cache_manager, task_id
    
    # 步骤 4: 精细检测 - 文件级变更
    if show_progress:
        safe_print(f"\n🔍 正在检测文件变更...")
    
    changes = metadata_manager.detect_changes(owner, repo, branch, documents)
    
    if show_progress:
        if changes.has_changes():
            safe_print(f"📊 检测结果: {changes.summary()}")
        else:
            safe_print(f"✅ 没有检测到文件变更")
    
    return documents, changes, commit_sha, cache_manager, task_id

