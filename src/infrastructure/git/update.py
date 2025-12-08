"""
Git仓库管理 - 更新操作模块：处理仓库更新相关操作

主要功能：
- update_repository()：更新仓库（git pull），支持重试机制

执行流程：
1. 切换到指定分支
2. 执行git pull更新
3. 检查更新结果
4. 重试机制（如果失败）

特性：
- 支持指定分支更新
- 重试机制
- 完整的错误处理
- 日志记录
"""

import subprocess
import os
import time
from pathlib import Path

from src.infrastructure.logger import get_logger

logger = get_logger('git_repository_manager')


def update_repository(repo_path: Path, branch: str, max_retries: int = 3) -> bool:
    """更新仓库（git pull）
    
    Args:
        repo_path: 本地仓库路径
        branch: 分支名称
        max_retries: 最大重试次数（默认3次）
        
    Raises:
        RuntimeError: 更新失败时
    """
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
        logger.warning(f"[阶段1.1] 切换分支失败: {result.stderr}")
    
    # 2. 拉取最新更改
    pull_cmd = ['git', 'pull', 'origin', branch]
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    env['GIT_HTTP_LOW_SPEED_LIMIT'] = '1000'
    env['GIT_HTTP_LOW_SPEED_TIME'] = '30'
    env['GIT_HTTP_TIMEOUT'] = '300'
    
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"[阶段1.1] 执行 git pull (尝试 {attempt}/{max_retries})")
            
            result = subprocess.run(
                pull_cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300,
                env=env
            )
            
            if result.returncode == 0:
                stdout = result.stdout.strip()
                if "Already up to date" in stdout or "已经是最新的" in stdout:
                    logger.info("[阶段1.1] 仓库已是最新版本")
                else:
                    logger.info(f"[阶段1.1] 仓库已更新: {stdout[:100]}")
                return
            
            # 检查是否是网络相关错误
            error_msg = result.stderr.lower()
            is_network_error = any(keyword in error_msg for keyword in [
                'tls', 'ssl', 'connection', 'timeout', 'timed out',
                'handshake', 'gnutls', 'unable to access'
            ])
            
            if is_network_error and attempt < max_retries:
                last_error = RuntimeError(f"git pull 失败 (网络错误): {result.stderr}")
                wait_time = 2 ** attempt
                logger.warning(f"[阶段1.1] 网络错误，{wait_time} 秒后重试 (尝试 {attempt}/{max_retries})")
                logger.debug(f"[阶段1.1] 错误详情: {result.stderr[:200]}")
                time.sleep(wait_time)
                continue
            else:
                raise RuntimeError(f"git pull 失败: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            last_error = RuntimeError("git pull 超时（5分钟）")
            if attempt < max_retries:
                logger.warning(f"[阶段1.1] 拉取超时，{2 ** attempt} 秒后重试 (尝试 {attempt}/{max_retries})")
                time.sleep(2 ** attempt)
                continue
            raise last_error
        except RuntimeError as e:
            last_error = e
            if attempt < max_retries:
                error_msg = str(e).lower()
                is_network_error = any(keyword in error_msg for keyword in [
                    'tls', 'ssl', 'connection', 'timeout', 'handshake',
                    'gnutls', 'unable to access'
                ])
                if is_network_error:
                    wait_time = 2 ** attempt
                    logger.warning(f"[阶段1.1] 网络错误，{wait_time} 秒后重试 (尝试 {attempt}/{max_retries})")
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
                    logger.warning(f"[阶段1.1] 网络错误，{wait_time} 秒后重试 (尝试 {attempt}/{max_retries})")
                    time.sleep(wait_time)
                    continue
            raise
    
    # 如果所有重试都失败了
    raise last_error or RuntimeError(f"git pull 失败: 已达到最大重试次数 ({max_retries})")

