"""
Git仓库管理 - 核心管理器模块
GitRepositoryManager类实现
"""

import subprocess
import shutil
import os
import time
from pathlib import Path
from typing import Optional, Tuple

from src.logger import setup_logger

logger = setup_logger('git_repository_manager')


class GitRepositoryManager:
    """Git 仓库本地管理器
    
    管理 GitHub 仓库的本地克隆，支持增量更新（git pull）
    """
    
    def __init__(self, repos_base_path: Path):
        """初始化 Git 仓库管理器
        
        Args:
            repos_base_path: 本地仓库存储的基础目录
        """
        self.repos_base_path = Path(repos_base_path)
        self.repos_base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Git 仓库管理器初始化，存储路径: {self.repos_base_path}")
        
        # 检查 git 是否可用
        if not self._check_git_available():
            logger.warning("系统未安装 git 或 git 不在 PATH 中")
    
    def _check_git_available(self) -> bool:
        """检查 git 命令是否可用
        
        Returns:
            git 是否可用
        """
        try:
            result = subprocess.run(
                ['git', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_version = result.stdout.strip()
                logger.info(f"检测到 git: {git_version}")
                return True
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.error(f"检查 git 可用性失败: {e}")
            return False
    
    def get_repo_path(self, owner: str, repo: str, branch: str) -> Path:
        """获取仓库的本地存储路径
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            
        Returns:
            本地仓库路径
        """
        repo_dir_name = f"{repo}_{branch}"
        return self.repos_base_path / owner / repo_dir_name
    
    def _build_clone_url(self, owner: str, repo: str) -> str:
        """构建克隆 URL（仅支持公开仓库）
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            
        Returns:
            HTTPS 克隆 URL
        """
        return f"https://github.com/{owner}/{repo}.git"
    
    def clone_or_update(
        self,
        owner: str,
        repo: str,
        branch: str,
        cache_manager=None,
        task_id: Optional[str] = None
    ) -> Tuple[Path, str]:
        """克隆或更新仓库（仅支持公开仓库）
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            cache_manager: 缓存管理器实例（可选）
            task_id: 任务ID（可选，用于缓存）
            
        Returns:
            (本地仓库路径, 当前 commit SHA)
            
        Raises:
            RuntimeError: Git 操作失败时
        """
        from src.git.clone import clone_repository
        from src.git.update import update_repository
        
        repo_path = self.get_repo_path(owner, repo, branch)
        clone_url = self._build_clone_url(owner, repo)
        
        # 如果提供了缓存管理器且启用了缓存，检查缓存
        if cache_manager and task_id:
            from src.config import config
            if config.ENABLE_CACHE:
                step_name = cache_manager.STEP_CLONE
                input_hash = cache_manager.compute_hash(f"{owner}/{repo}@{branch}")
                
                if cache_manager.check_step_cache(task_id, step_name, input_hash):
                    if repo_path.exists():
                        try:
                            commit_sha = self.get_current_commit_sha(repo_path)
                            cached_commit = cache_manager.get_step_data(task_id, step_name).get("commit_sha")
                            
                            if cached_commit and commit_sha == cached_commit:
                                logger.info(f"✅ 使用缓存: 仓库已存在且 commit 匹配 ({commit_sha[:8]})")
                                return repo_path, commit_sha
                            else:
                                logger.info(f"⚠️  缓存中的 commit SHA 不匹配，继续更新仓库")
                        except Exception as e:
                            logger.warning(f"获取 commit SHA 失败，继续正常流程: {e}")
                    else:
                        logger.info(f"⚠️  缓存有效但仓库不存在，继续克隆")
        
        try:
            if not repo_path.exists():
                # 首次克隆
                logger.info(f"📥 开始克隆仓库: {owner}/{repo}@{branch}")
                clone_repository(clone_url, repo_path, branch)
            else:
                # 增量更新
                logger.info(f"🔄 开始更新仓库: {owner}/{repo}@{branch}")
                update_repository(repo_path, branch)
            
            # 获取当前 commit SHA
            commit_sha = self.get_current_commit_sha(repo_path)
            logger.info(f"仓库当前 commit: {commit_sha[:8]}")
            
            # 如果提供了缓存管理器，更新缓存状态
            if cache_manager and task_id:
                from src.config import config
                if config.ENABLE_CACHE:
                    input_hash = cache_manager.compute_hash(f"{owner}/{repo}@{branch}")
                    cache_manager.mark_step_completed(
                        task_id=task_id,
                        step_name=cache_manager.STEP_CLONE,
                        input_hash=input_hash,
                        commit_sha=commit_sha,
                        repo_path=str(repo_path)
                    )
            
            return repo_path, commit_sha
            
        except Exception as e:
            error_msg = f"Git 操作失败 ({owner}/{repo}@{branch}): {e}"
            logger.error(error_msg)
            
            # 如果提供了缓存管理器，标记步骤失败
            if cache_manager and task_id:
                cache_manager.mark_step_failed(
                    task_id=task_id,
                    step_name=cache_manager.STEP_CLONE,
                    error_message=str(e)
                )
            
            raise RuntimeError(error_msg) from e
    
    def get_current_commit_sha(self, repo_path: Path) -> str:
        """获取当前 commit SHA
        
        Args:
            repo_path: 本地仓库路径
            
        Returns:
            完整的 commit SHA（40字符）
            
        Raises:
            RuntimeError: 获取失败时
        """
        from src.git.utils import get_commit_sha
        return get_commit_sha(repo_path)
    
    def cleanup_repo(self, owner: str, repo: str, branch: str):
        """删除本地仓库副本
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
        """
        repo_path = self.get_repo_path(owner, repo, branch)
        
        if repo_path.exists():
            try:
                shutil.rmtree(repo_path)
                logger.info(f"已删除本地仓库: {repo_path}")
            except Exception as e:
                logger.error(f"删除仓库失败 {repo_path}: {e}")
                raise
        else:
            logger.warning(f"仓库不存在，无需删除: {repo_path}")

