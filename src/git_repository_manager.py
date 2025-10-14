"""
Git 仓库本地管理器
负责克隆、更新和管理本地 Git 仓库副本
"""

import subprocess
import shutil
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
            本地仓库路径，格式: repos_base_path/owner/repo_branch/
        """
        # 使用 owner/repo_branch 的目录结构
        # 例如: data/github_repos/microsoft/TypeScript_main/
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
        
        如果本地不存在，执行 git clone
        如果已存在，执行 git pull
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            
        Returns:
            (本地仓库路径, 当前 commit SHA)
            
        Raises:
            RuntimeError: Git 操作失败时
        """
        repo_path = self.get_repo_path(owner, repo, branch)
        clone_url = self._build_clone_url(owner, repo)
        
        try:
            if not repo_path.exists():
                # 首次克隆
                logger.info(f"克隆仓库: {owner}/{repo}@{branch} -> {repo_path}")
                self._clone_repository(clone_url, repo_path, branch)
            else:
                # 增量更新
                logger.info(f"更新仓库: {owner}/{repo}@{branch}")
                self._update_repository(repo_path, branch)
            
            # 获取当前 commit SHA
            commit_sha = self.get_current_commit_sha(repo_path)
            logger.info(f"仓库当前 commit: {commit_sha[:8]}")
            
            return repo_path, commit_sha
            
        except Exception as e:
            error_msg = f"Git 操作失败 ({owner}/{repo}@{branch}): {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def _clone_repository(self, clone_url: str, repo_path: Path, branch: str):
        """克隆仓库
        
        Args:
            clone_url: 克隆 URL
            repo_path: 本地存储路径
            branch: 分支名称
            
        Raises:
            RuntimeError: 克隆失败时
        """
        # 确保父目录存在
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 执行 git clone
        cmd = [
            'git', 'clone',
            '--branch', branch,
            '--depth', '1',  # 浅克隆，节省空间和时间
            '--single-branch',
            clone_url,
            str(repo_path)
        ]
        
        try:
            logger.debug(f"执行 git clone 到 {repo_path}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                env={'GIT_TERMINAL_PROMPT': '0'}  # 禁用交互式提示
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"git clone 失败: {result.stderr}")
            
            logger.info(f"克隆成功: {repo_path}")
            
        except subprocess.TimeoutExpired:
            # 超时清理
            if repo_path.exists():
                shutil.rmtree(repo_path, ignore_errors=True)
            raise RuntimeError("git clone 超时（5分钟）")
        except Exception as e:
            # 其他错误清理
            if repo_path.exists():
                shutil.rmtree(repo_path, ignore_errors=True)
            raise
    
    def _update_repository(self, repo_path: Path, branch: str):
        """更新仓库（git pull）
        
        Args:
            repo_path: 本地仓库路径
            branch: 分支名称
            
        Raises:
            RuntimeError: 更新失败时
        """
        try:
            # 1. 切换到指定分支
            checkout_cmd = ['git', 'checkout', branch]
            result = subprocess.run(
                checkout_cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.warning(f"切换分支失败: {result.stderr}")
            
            # 2. 拉取最新更改
            pull_cmd = ['git', 'pull', 'origin', branch]
            result = subprocess.run(
                pull_cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                env={'GIT_TERMINAL_PROMPT': '0'}
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"git pull 失败: {result.stderr}")
            
            stdout = result.stdout.strip()
            if "Already up to date" in stdout or "已经是最新的" in stdout:
                logger.info("仓库已是最新版本")
            else:
                logger.info(f"仓库已更新: {stdout[:100]}")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("git pull 超时（5分钟）")
    
    def get_current_commit_sha(self, repo_path: Path) -> str:
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


if __name__ == "__main__":
    # 测试代码
    import tempfile
    from pathlib import Path
    
    print("=== 测试 Git 仓库管理器 ===\n")
    
    # 使用临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        manager = GitRepositoryManager(temp_path / "repos")
        
        # 测试 1: 克隆公开仓库
        print("1. 测试克隆公开仓库（小型测试仓库）...")
        try:
            # 使用一个小型测试仓库
            repo_path, commit_sha = manager.clone_or_update(
                "octocat", "Hello-World", "master"
            )
            print(f"   ✅ 克隆成功: {repo_path}")
            print(f"   Commit: {commit_sha[:8]}\n")
            
            # 测试 2: 更新仓库（应该显示已是最新）
            print("2. 测试更新仓库...")
            repo_path2, commit_sha2 = manager.clone_or_update(
                "octocat", "Hello-World", "master"
            )
            print(f"   ✅ 更新成功")
            print(f"   Commit 未变: {commit_sha == commit_sha2}\n")
            
            # 测试 3: 清理仓库
            print("3. 测试清理仓库...")
            manager.cleanup_repo("octocat", "Hello-World", "master")
            print(f"   ✅ 清理成功\n")
            
            print("✅ 所有测试通过")
            
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")

