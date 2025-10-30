"""
GitHub 数据源
从 GitHub 仓库获取文件路径
"""

import os
from pathlib import Path
from typing import List, Optional
from src.data_source.base import DataSource, SourceFile
from src.logger import setup_logger

try:
    from src.git_repository_manager import GitRepositoryManager
except ImportError:
    GitRepositoryManager = None

from src.config import config

logger = setup_logger('github_source')


class GitHubSource(DataSource):
    """GitHub 仓库数据源"""
    
    def __init__(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        filter_directories: Optional[List[str]] = None,
        filter_file_extensions: Optional[List[str]] = None,
        show_progress: bool = True
    ):
        """初始化 GitHub 数据源
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称（可选，默认 main）
            filter_directories: 只包含指定目录的文件
            filter_file_extensions: 只包含指定扩展名的文件
            show_progress: 是否显示进度信息
        """
        self.owner = owner
        self.repo = repo
        self.branch = branch or "main"
        self.filter_directories = filter_directories
        self.filter_file_extensions = filter_file_extensions
        self.show_progress = show_progress
        self.repo_path: Optional[Path] = None
        self.commit_sha: Optional[str] = None
    
    def get_source_metadata(self) -> dict:
        """获取数据源的元数据"""
        return {
            'owner': self.owner,
            'repo': self.repo,
            'branch': self.branch,
            'commit_sha': self.commit_sha,
            'repository': f"{self.owner}/{self.repo}",
            'url': f"https://github.com/{self.owner}/{self.repo}/blob/{self.branch}"
        }
    
    def get_file_paths(self, cache_manager=None, task_id: Optional[str] = None) -> List[SourceFile]:
        """获取 GitHub 仓库中的文件路径列表
        
        Args:
            cache_manager: 缓存管理器实例（可选）
            task_id: 任务ID（可选，用于缓存）
        
        Returns:
            文件路径列表
        """
        import time
        start_time = time.time()
        
        if GitRepositoryManager is None:
            logger.error("GitRepositoryManager 未安装")
            return []
        
        try:
            # 步骤 1: 克隆或更新仓库
            logger.info(f"开始从 GitHub 获取文件: {self.owner}/{self.repo}@{self.branch}")
            
            git_manager = GitRepositoryManager(config.GITHUB_REPOS_PATH)
            
            try:
                git_start_time = time.time()
                self.repo_path, self.commit_sha = git_manager.clone_or_update(
                    owner=self.owner,
                    repo=self.repo,
                    branch=self.branch,
                    cache_manager=cache_manager,
                    task_id=task_id
                )
                git_elapsed = time.time() - git_start_time
                logger.info(f"仓库同步完成: {self.repo_path} (Commit: {self.commit_sha[:8]}, 耗时: {git_elapsed:.2f}s)")
                
            except RuntimeError as e:
                logger.error(f"Git 操作失败: {e}", exc_info=True)
                return []
            
            # 步骤 2: 遍历仓库目录，获取所有文件路径
            logger.debug(f"开始遍历仓库目录: {self.repo_path}")
            walk_start_time = time.time()
            
            all_files = self._walk_repository(self.repo_path)
            walk_elapsed = time.time() - walk_start_time
            
            logger.info(f"目录遍历完成: 找到 {len(all_files)} 个文件 (耗时: {walk_elapsed:.2f}s)")
            
            # 步骤 3: 应用过滤器
            source_files = []
            source_metadata = self.get_source_metadata()
            
            filter_start_time = time.time()
            filtered_count = 0
            
            for file_path in all_files:
                # 构建相对于仓库根目录的相对路径
                try:
                    relative_path = file_path.relative_to(self.repo_path)
                except ValueError:
                    logger.warning(f"无法构建相对路径: {file_path}")
                    continue
                
                # 应用过滤器
                if not self._should_include_file(str(relative_path)):
                    filtered_count += 1
                    continue
                
                source_files.append(SourceFile(
                    path=file_path,
                    source_type='github',
                    metadata={
                        **source_metadata,
                        'file_path': str(relative_path),
                        'file_name': file_path.name,
                        'url': f"https://github.com/{self.owner}/{self.repo}/blob/{self.branch}/{relative_path}"
                    }
                ))
            
            filter_elapsed = time.time() - filter_start_time
            total_elapsed = time.time() - start_time
            
            logger.info(
                f"文件过滤完成: "
                f"总文件数={len(all_files)}, "
                f"过滤后={len(source_files)}, "
                f"过滤掉={filtered_count}, "
                f"过滤耗时={filter_elapsed:.2f}s, "
                f"总耗时={total_elapsed:.2f}s"
            )
            
            # 记录过滤器信息
            if self.filter_directories:
                logger.debug(f"目录过滤: {self.filter_directories}")
            if self.filter_file_extensions:
                logger.debug(f"扩展名过滤: {self.filter_file_extensions}")
            
            return source_files
            
        except Exception as e:
            logger.error(f"获取 GitHub 文件路径失败: {e}", exc_info=True)
            return []
    
    def _walk_repository(self, repo_path: Path) -> List[Path]:
        """递归遍历仓库目录，返回所有文件路径
        
        Args:
            repo_path: 仓库根路径
            
        Returns:
            文件路径列表
        """
        files = []
        excluded_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.pytest_cache'}
        excluded_exts = {'.pyc', '.pyo', '.lock', '.log'}
        
        dir_count = 0
        skipped_file_count = 0
        
        for root, dirs, filenames in os.walk(repo_path):
            dir_count += 1
            # 移除排除的目录，避免遍历
            removed_dirs = [d for d in dirs if d in excluded_dirs]
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            if removed_dirs:
                logger.debug(f"跳过目录: {removed_dirs} (在 {root})")
            
            root_path = Path(root)
            for filename in filenames:
                file_path = root_path / filename
                
                # 排除特定扩展名
                if any(file_path.suffix == ext for ext in excluded_exts):
                    skipped_file_count += 1
                    continue
                
                # 只包含文件，排除符号链接等
                if file_path.is_file():
                    files.append(file_path)
                else:
                    logger.debug(f"跳过非文件路径: {file_path}")
        
        logger.debug(
            f"目录遍历统计: "
            f"遍历目录数={dir_count}, "
            f"找到文件数={len(files)}, "
            f"跳过文件数={skipped_file_count}"
        )
        
        return files
    
    def _should_include_file(self, relative_path: str) -> bool:
        """判断文件是否应该被包含
        
        Args:
            relative_path: 相对于仓库根目录的文件路径
            
        Returns:
            是否包含该文件
        """
        # 如果指定了目录过滤
        if self.filter_directories:
            if not any(
                relative_path.startswith(d.rstrip('/') + '/') or 
                relative_path.startswith(d.rstrip('/'))
                for d in self.filter_directories
            ):
                return False
        
        # 如果指定了扩展名过滤
        if self.filter_file_extensions:
            if not any(relative_path.endswith(ext) for ext in self.filter_file_extensions):
                return False
        
        return True

