"""
GitHub 仓库预检模块：克隆前检查仓库状态

主要功能：
- check_repository(): 检查仓库存在性、大小、是否私有
- PreflightResult: 预检结果数据类

特性：
- 快速失败：仓库不存在时秒级返回
- 大仓库警告：超过阈值时提示用户
- 私有仓库检测：提示需要 Token
"""

import os
from dataclasses import dataclass
from typing import Optional
import urllib.request
import urllib.error
import json

from backend.infrastructure.logger import get_logger

logger = get_logger('github_preflight')

# 大仓库阈值（KB），超过此值给出警告
LARGE_REPO_THRESHOLD_KB = 100 * 1024  # 100MB


@dataclass
class PreflightResult:
    """预检结果"""
    success: bool
    exists: bool = True
    is_private: bool = False
    size_kb: int = 0
    default_branch: str = "main"
    error_message: Optional[str] = None
    warning_message: Optional[str] = None
    
    @property
    def size_mb(self) -> float:
        """返回仓库大小（MB）"""
        return self.size_kb / 1024
    
    @property
    def is_large(self) -> bool:
        """是否为大仓库"""
        return self.size_kb > LARGE_REPO_THRESHOLD_KB


def check_repository(owner: str, repo: str, timeout: int = 10) -> PreflightResult:
    """检查 GitHub 仓库状态
    
    通过 GitHub API 检查仓库的存在性、大小、是否私有等信息。
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        timeout: 请求超时时间（秒）
        
    Returns:
        PreflightResult: 预检结果
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "RAG-System-Preflight/1.0"
    }
    
    # 如果有 GitHub Token，添加认证头
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    logger.info(f"[预检] 检查仓库: {owner}/{repo}")
    
    try:
        request = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            size_kb = data.get("size", 0)
            is_private = data.get("private", False)
            default_branch = data.get("default_branch", "main")
            
            result = PreflightResult(
                success=True,
                exists=True,
                is_private=is_private,
                size_kb=size_kb,
                default_branch=default_branch
            )
            
            # 检查是否为大仓库
            if result.is_large:
                result.warning_message = (
                    f"仓库较大 ({result.size_mb:.1f}MB)，克隆可能需要较长时间"
                )
                logger.warning(f"[预检] {result.warning_message}")
            
            logger.info(
                f"[预检] 仓库检查通过: size={result.size_mb:.1f}MB, "
                f"private={is_private}, branch={default_branch}"
            )
            
            return result
            
    except urllib.error.HTTPError as e:
        if e.code == 404:
            logger.error(f"[预检] 仓库不存在: {owner}/{repo}")
            return PreflightResult(
                success=False,
                exists=False,
                error_message=f"仓库不存在: {owner}/{repo}"
            )
        elif e.code == 401:
            logger.error(f"[预检] 认证失败，请检查 GITHUB_TOKEN")
            return PreflightResult(
                success=False,
                error_message="GitHub 认证失败，请检查 GITHUB_TOKEN 环境变量"
            )
        elif e.code == 403:
            # 可能是速率限制或私有仓库
            error_body = e.read().decode('utf-8', errors='ignore')
            if "rate limit" in error_body.lower():
                logger.error(f"[预检] GitHub API 速率限制")
                return PreflightResult(
                    success=False,
                    error_message="GitHub API 速率限制，请稍后重试或配置 GITHUB_TOKEN"
                )
            else:
                logger.error(f"[预检] 访问被拒绝，可能是私有仓库")
                return PreflightResult(
                    success=False,
                    is_private=True,
                    error_message=f"无法访问仓库 {owner}/{repo}，可能是私有仓库，请配置 GITHUB_TOKEN"
                )
        else:
            logger.error(f"[预检] HTTP 错误 {e.code}: {e.reason}")
            return PreflightResult(
                success=False,
                error_message=f"GitHub API 错误: {e.code} {e.reason}"
            )
            
    except urllib.error.URLError as e:
        logger.error(f"[预检] 网络错误: {e.reason}")
        return PreflightResult(
            success=False,
            error_message=f"网络错误: {e.reason}"
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"[预检] 解析响应失败: {e}")
        return PreflightResult(
            success=False,
            error_message="GitHub API 响应解析失败"
        )
        
    except Exception as e:
        logger.error(f"[预检] 未知错误: {e}", exc_info=True)
        return PreflightResult(
            success=False,
            error_message=f"预检失败: {str(e)}"
        )
