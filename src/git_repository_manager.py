"""
Git 仓库本地管理器
负责克隆、更新和管理本地 Git 仓库副本
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
        branch: str,
        cache_manager=None,
        task_id: Optional[str] = None
    ) -> Tuple[Path, str]:
        """克隆或更新仓库（仅支持公开仓库）
        
        如果本地不存在，执行 git clone
        如果已存在，执行 git pull
        如果缓存有效且仓库存在，可能跳过操作
        
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
        repo_path = self.get_repo_path(owner, repo, branch)
        clone_url = self._build_clone_url(owner, repo)
        
        # 如果提供了缓存管理器且启用了缓存，检查缓存
        if cache_manager and task_id:
            from src.config import config
            if config.ENABLE_CACHE:
                # 检查克隆步骤缓存
                step_name = cache_manager.STEP_CLONE
                input_hash = cache_manager.compute_hash(f"{owner}/{repo}@{branch}")
                
                if cache_manager.check_step_cache(task_id, step_name, input_hash):
                    # 缓存有效，检查仓库是否存在
                    if repo_path.exists():
                        # 获取当前 commit SHA
                        try:
                            commit_sha = self.get_current_commit_sha(repo_path)
                            cached_commit = cache_manager.get_step_data(task_id, step_name).get("commit_sha")
                            
                            # 验证 commit SHA 是否匹配
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
                logger.info(f"   目标路径: {repo_path}")
                logger.info(f"   克隆URL: {clone_url}")
                logger.info(f"   分支: {branch}")
                self._clone_repository(clone_url, repo_path, branch)
            else:
                # 增量更新
                logger.info(f"🔄 开始更新仓库: {owner}/{repo}@{branch}")
                logger.info(f"   仓库路径: {repo_path}")
                logger.info(f"   分支: {branch}")
                self._update_repository(repo_path, branch)
            
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
    
    def _clone_repository(self, clone_url: str, repo_path: Path, branch: str, max_retries: int = 3):
        """克隆仓库
        
        Args:
            clone_url: 克隆 URL
            repo_path: 本地存储路径
            branch: 分支名称
            max_retries: 最大重试次数（默认3次）
            
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
        
        # 继承当前进程的环境变量，确保 DNS、代理等配置可用
        env = os.environ.copy()
        env['GIT_TERMINAL_PROMPT'] = '0'  # 禁用交互式提示
        # 添加 Git 配置以改善网络连接稳定性
        env['GIT_HTTP_LOW_SPEED_LIMIT'] = '1000'  # 1KB/s 最低速度
        env['GIT_HTTP_LOW_SPEED_TIME'] = '30'  # 30秒
        env['GIT_HTTP_TIMEOUT'] = '300'  # 5分钟超时
        
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                # 如果不是第一次尝试，先清理可能存在的部分克隆
                if attempt > 1 and repo_path.exists():
                    logger.info(f"清理之前的克隆尝试 (第 {attempt} 次重试)")
                    shutil.rmtree(repo_path, ignore_errors=True)
                    time.sleep(2)  # 等待文件系统释放
                
                logger.debug(f"执行 git clone 到 {repo_path} (尝试 {attempt}/{max_retries})")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5分钟超时
                    env=env
                )
                
                if result.returncode == 0:
                    logger.info(f"✅ 克隆成功: {repo_path}")
                    logger.info(f"   仓库已克隆到本地，准备解析文件")
                    return
                
                # 检查是否是网络相关错误（需要重试）
                error_msg = result.stderr.lower()
                is_network_error = any(keyword in error_msg for keyword in [
                    'tls', 'ssl', 'connection', 'timeout', 'timed out', 
                    'handshake', 'gnutls', 'unable to access'
                ])
                
                if is_network_error and attempt < max_retries:
                    last_error = RuntimeError(f"git clone 失败 (网络错误): {result.stderr}")
                    wait_time = 2 ** attempt  # 指数退避：2秒、4秒、8秒
                    logger.warning(f"网络错误，{wait_time} 秒后重试 (尝试 {attempt}/{max_retries})")
                    logger.debug(f"错误详情: {result.stderr[:200]}")
                    time.sleep(wait_time)
                    continue
                else:
                    # 非网络错误或已达到最大重试次数
                    raise RuntimeError(f"git clone 失败: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                last_error = RuntimeError("git clone 超时（5分钟）")
                if attempt < max_retries:
                    logger.warning(f"克隆超时，{2 ** attempt} 秒后重试 (尝试 {attempt}/{max_retries})")
                    time.sleep(2 ** attempt)
                    continue
                # 超时清理
                if repo_path.exists():
                    shutil.rmtree(repo_path, ignore_errors=True)
                raise last_error
            except RuntimeError as e:
                # 如果是网络错误且还有重试机会，已经在上面处理了
                # 这里处理其他运行时错误
                last_error = e
                if attempt < max_retries:
                    error_msg = str(e).lower()
                    is_network_error = any(keyword in error_msg for keyword in [
                        'tls', 'ssl', 'connection', 'timeout', 'handshake', 
                        'gnutls', 'unable to access'
                    ])
                    if is_network_error:
                        wait_time = 2 ** attempt
                        logger.warning(f"网络错误，{wait_time} 秒后重试 (尝试 {attempt}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                raise
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    error_msg = str(e).lower()
                    is_network_error = any(keyword in error_msg for keyword in [
                        'tls', 'ssl', 'connection', 'timeout', 'handshake', 
                        'gnutls', 'unable to access'
                    ])
                    if is_network_error:
                        wait_time = 2 ** attempt
                        logger.warning(f"网络错误，{wait_time} 秒后重试 (尝试 {attempt}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                # 其他错误清理
                if repo_path.exists():
                    shutil.rmtree(repo_path, ignore_errors=True)
                raise
        
        # 如果所有重试都失败了
        if repo_path.exists():
            shutil.rmtree(repo_path, ignore_errors=True)
        raise last_error or RuntimeError(f"git clone 失败: 已达到最大重试次数 ({max_retries})")
    
    def _update_repository(self, repo_path: Path, branch: str, max_retries: int = 3):
        """更新仓库（git pull）
        
        Args:
            repo_path: 本地仓库路径
            branch: 分支名称
            max_retries: 最大重试次数（默认3次）
            
        Raises:
            RuntimeError: 更新失败时
        """
        # 1. 切换到指定分支（不需要重试，失败只记录警告）
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
        
        # 2. 拉取最新更改（需要重试机制）
        pull_cmd = ['git', 'pull', 'origin', branch]
        # 继承当前进程的环境变量，确保 DNS、代理等配置可用
        env = os.environ.copy()
        env['GIT_TERMINAL_PROMPT'] = '0'  # 禁用交互式提示
        # 添加 Git 配置以改善网络连接稳定性
        env['GIT_HTTP_LOW_SPEED_LIMIT'] = '1000'  # 1KB/s 最低速度
        env['GIT_HTTP_LOW_SPEED_TIME'] = '30'  # 30秒
        env['GIT_HTTP_TIMEOUT'] = '300'  # 5分钟超时
        
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"执行 git pull (尝试 {attempt}/{max_retries})")
                
                result = subprocess.run(
                    pull_cmd,
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5分钟超时
                    env=env
                )
                
                if result.returncode == 0:
                    stdout = result.stdout.strip()
                    if "Already up to date" in stdout or "已经是最新的" in stdout:
                        logger.info("仓库已是最新版本")
                    else:
                        logger.info(f"仓库已更新: {stdout[:100]}")
                    return
                
                # 检查是否是网络相关错误（需要重试）
                error_msg = result.stderr.lower()
                is_network_error = any(keyword in error_msg for keyword in [
                    'tls', 'ssl', 'connection', 'timeout', 'timed out', 
                    'handshake', 'gnutls', 'unable to access'
                ])
                
                if is_network_error and attempt < max_retries:
                    last_error = RuntimeError(f"git pull 失败 (网络错误): {result.stderr}")
                    wait_time = 2 ** attempt  # 指数退避：2秒、4秒、8秒
                    logger.warning(f"网络错误，{wait_time} 秒后重试 (尝试 {attempt}/{max_retries})")
                    logger.debug(f"错误详情: {result.stderr[:200]}")
                    time.sleep(wait_time)
                    continue
                else:
                    # 非网络错误或已达到最大重试次数
                    raise RuntimeError(f"git pull 失败: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                last_error = RuntimeError("git pull 超时（5分钟）")
                if attempt < max_retries:
                    logger.warning(f"拉取超时，{2 ** attempt} 秒后重试 (尝试 {attempt}/{max_retries})")
                    time.sleep(2 ** attempt)
                    continue
                raise last_error
            except RuntimeError as e:
                # 如果是网络错误且还有重试机会，已经在上面处理了
                # 这里处理其他运行时错误
                last_error = e
                if attempt < max_retries:
                    error_msg = str(e).lower()
                    is_network_error = any(keyword in error_msg for keyword in [
                        'tls', 'ssl', 'connection', 'timeout', 'handshake', 
                        'gnutls', 'unable to access'
                    ])
                    if is_network_error:
                        wait_time = 2 ** attempt
                        logger.warning(f"网络错误，{wait_time} 秒后重试 (尝试 {attempt}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                raise
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    error_msg = str(e).lower()
                    is_network_error = any(keyword in error_msg for keyword in [
                        'tls', 'ssl', 'connection', 'timeout', 'handshake', 
                        'gnutls', 'unable to access'
                    ])
                    if is_network_error:
                        wait_time = 2 ** attempt
                        logger.warning(f"网络错误，{wait_time} 秒后重试 (尝试 {attempt}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                raise
        
        # 如果所有重试都失败了
        raise last_error or RuntimeError(f"git pull 失败: 已达到最大重试次数 ({max_retries})")
    
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

