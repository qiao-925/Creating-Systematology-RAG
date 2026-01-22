"""
数据导入服务：GitHub导入功能

主要功能：
- GitHub仓库同步
- GitHub URL导入
"""

from typing import List, Optional

from backend.infrastructure.logger import get_logger
from backend.infrastructure.data_loader.models import ImportResult, ProgressReporter
from backend.infrastructure.data_loader.source import GitHubSource

logger = get_logger('data_loader_service')


def sync_github_repository(
    progress_reporter: ProgressReporter,
    github_sync_manager,
    owner: str,
    repo: str,
    branch: str = "main",
    filter_directories: Optional[List[str]] = None,
    filter_file_extensions: Optional[List[str]] = None
) -> tuple:
    """同步GitHub仓库并检测变更
    
    Returns:
        (所有文档列表, FileChange对象, commit_sha)
    """
    from backend.infrastructure.data_loader.github_sync import FileChange
    from backend.infrastructure.config import config
    
    try:
        from backend.infrastructure.git import GitRepositoryManager
        if GitRepositoryManager is None:
            error_msg = "GitRepositoryManager 未安装"
            progress_reporter.report_error(error_msg)
            return [], FileChange(), None
        
        git_manager = GitRepositoryManager(config.GITHUB_REPOS_PATH)
        progress_reporter.report_stage("🔄", f"正在同步仓库: {owner}/{repo}@{branch}")
        
        repo_path, commit_sha = git_manager.clone_or_update(
            owner=owner,
            repo=repo,
            branch=branch
        )
        
        progress_reporter.report_success(f"仓库已同步 (Commit: {commit_sha[:8]})")
        
    except RuntimeError as e:
        error_msg = f"Git 操作失败: {str(e)}"
        progress_reporter.report_error(error_msg)
        logger.error(error_msg)
        return [], FileChange(), None
    
    old_sync_state = github_sync_manager.get_repository_sync_state(owner, repo, branch)
    
    if old_sync_state:
        old_commit_sha = old_sync_state.get('last_commit_sha', '')
        if old_commit_sha == commit_sha:
            progress_reporter.report_success("仓库无新提交，跳过加载")
            logger.info(f"仓库 {owner}/{repo}@{branch} 无新提交 (Commit: {commit_sha[:8]})")
            return [], FileChange(), commit_sha
    
    progress_reporter.report_stage("📄", "检测到新提交，正在加载文档...")
    
    # 需要从外部传入 import_from_github 方法
    # 这里返回一个占位符，实际调用在 service.py 中
    return None, None, commit_sha


def import_from_github_url(
    progress_reporter: ProgressReporter,
    import_from_github_func,
    github_url: str,
    clean: bool = True,
    **kwargs
) -> ImportResult:
    """从GitHub URL导入文档"""
    from backend.infrastructure.data_loader.github_url import parse_github_url
    
    repo_info = parse_github_url(github_url)
    if not repo_info:
        error_msg = f"无法解析GitHub URL: {github_url}"
        progress_reporter.report_error(error_msg)
        return ImportResult(
            documents=[],
            success=False,
            errors=[error_msg]
        )
    
    return import_from_github_func(
        owner=repo_info['owner'],
        repo=repo_info['repo'],
        branch=repo_info.get('branch', 'main'),
        clean=clean,
        **kwargs
    )
