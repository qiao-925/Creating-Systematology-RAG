"""
Git仓库管理 - 核心管理器模块：GitRepositoryManager类实现

主要功能：
- GitRepositoryManager类：Git仓库本地管理器，管理GitHub仓库的本地克隆和增量更新
- get_repo_path()：获取仓库本地路径
- clone_or_update()：克隆或更新仓库

执行流程：
1. 检查仓库是否已存在
2. 如果不存在，执行克隆
3. 如果存在，执行更新（git pull）
4. 返回仓库路径

特性：
- 自动克隆和更新
- 增量更新机制
- 完整的错误处理
- 重试机制
"""

import subprocess
import shutil
import os
import time
from pathlib import Path
from typing import Optional, Tuple

from src.infrastructure.logger import get_logger

logger = get_logger('git_repository_manager')


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
        logger.info(f"[阶段1.1] Git 仓库管理器初始化，存储路径: {self.repos_base_path}")
        
        # 检查 git 是否可用
        if not self._check_git_available():
            logger.warning("[阶段1.1] 系统未安装 git 或 git 不在 PATH 中")
    
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
                logger.info(f"[阶段1.1] 检测到 git: {git_version}")
                return True
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.error(f"[阶段1.1] 检查 git 可用性失败: {e}")
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
        branch: str
    ) -> Tuple[Path, str]:
        """克隆或更新仓库（仅支持公开仓库）
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            
        Returns:
            (本地仓库路径, 当前 commit SHA)
            
        Raises:
            RuntimeError: Git 操作失败时
        """
        from src.infrastructure.git.clone import clone_repository
        from src.infrastructure.git.update import update_repository
        
        repo_path = self.get_repo_path(owner, repo, branch)
        clone_url = self._build_clone_url(owner, repo)
        
        try:
            if not repo_path.exists():
                # 首次克隆
                logger.info(f"[阶段1.1] 📥 开始克隆仓库: {owner}/{repo}@{branch}")
                clone_repository(clone_url, repo_path, branch)
            else:
                # 增量更新
                logger.info(f"[阶段1.1] 🔄 开始更新仓库: {owner}/{repo}@{branch}")
                update_repository(repo_path, branch)
            
            # 获取当前 commit SHA
            commit_sha = self.get_current_commit_sha(repo_path)
            logger.info(f"[阶段1.1] 仓库当前 commit: {commit_sha[:8]}")
            
            return repo_path, commit_sha
            
        except Exception as e:
            error_msg = f"Git 操作失败 ({owner}/{repo}@{branch}): {e}"
            logger.error(f"[阶段1.1] {error_msg}")
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
        from src.infrastructure.git.utils import get_commit_sha
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
                logger.info(f"[阶段1.1] 已删除本地仓库: {repo_path}")
            except Exception as e:
                logger.error(f"[阶段1.1] 删除仓库失败 {repo_path}: {e}")
                raise
        else:
            logger.warning(f"[阶段1.1] 仓库不存在，无需删除: {repo_path}")

