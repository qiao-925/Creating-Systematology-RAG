"""
Git仓库管理 - 克隆操作模块
处理仓库克隆相关操作
"""

import subprocess
import shutil
import time
from pathlib import Path

from src.logger import setup_logger

logger = setup_logger('git_repository_manager')


def clone_repository(clone_url: str, repo_path: Path, branch: str, max_retries: int = 3):
    """克隆仓库
    
    Args:
        clone_url: 克隆 URL
        repo_path: 本地存储路径
        branch: 分支名称
        max_retries: 最大重试次数（默认3次）
        
    Raises:
        RuntimeError: 克隆失败时
    """
    clone_cmd = [
        'git', 'clone',
        '--branch', branch,
        '--single-branch',
        '--depth', '1',  # 浅克隆，只获取最新提交
        clone_url,
        str(repo_path)
    ]
    
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    env['GIT_HTTP_LOW_SPEED_LIMIT'] = '1000'
    env['GIT_HTTP_LOW_SPEED_TIME'] = '30'
    env['GIT_HTTP_TIMEOUT'] = '300'
    
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"执行 git clone (尝试 {attempt}/{max_retries})")
            
            result = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                timeout=600,
                env=env
            )
            
            if result.returncode == 0:
                logger.info(f"✅ 仓库克隆成功: {repo_path}")
                return
            
            # 检查是否是网络相关错误
            error_msg = result.stderr.lower()
            is_network_error = any(keyword in error_msg for keyword in [
                'tls', 'ssl', 'connection', 'timeout', 'timed out',
                'handshake', 'gnutls', 'unable to access'
            ])
            
            if is_network_error and attempt < max_retries:
                last_error = RuntimeError(f"git clone 失败 (网络错误): {result.stderr}")
                wait_time = 2 ** attempt
                logger.warning(f"网络错误，{wait_time} 秒后重试 (尝试 {attempt}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                raise RuntimeError(f"git clone 失败: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            last_error = RuntimeError("git clone 超时（10分钟）")
            if attempt < max_retries:
                logger.warning(f"克隆超时，{2 ** attempt} 秒后重试 (尝试 {attempt}/{max_retries})")
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
                    logger.warning(f"网络错误，{wait_time} 秒后重试 (尝试 {attempt}/{max_retries})")
                    time.sleep(wait_time)
                    continue
            # 其他错误清理
            if repo_path.exists():
                shutil.rmtree(repo_path, ignore_errors=True)
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

