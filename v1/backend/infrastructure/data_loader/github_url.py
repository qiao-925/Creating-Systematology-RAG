"""
GitHub URL解析模块：解析GitHub URL获取仓库信息

主要功能：
- parse_github_url()：解析GitHub URL，提取owner、repo、branch信息

执行流程：
1. 清理和规范化URL（自动添加https://协议）
2. 解析URL路径
3. 提取仓库所有者和名称
4. 提取分支信息（如果URL中包含/tree/branch）

特性：
- 支持多种URL格式（带/不带协议、带/不带分支）
- 自动处理.git后缀
- 默认使用main分支
- 完整的错误处理和日志记录
"""

from typing import Optional
from urllib.parse import urlparse

from backend.infrastructure.logger import get_logger

logger = get_logger('data_loader')


def parse_github_url(url: str) -> Optional[dict]:
    """解析 GitHub URL 获取仓库信息
    
    支持的格式：
    - https://github.com/owner/repo
    - github.com/owner/repo
    - http://github.com/owner/repo
    - https://github.com/owner/repo/tree/branch
    
    Args:
        url: GitHub URL
        
    Returns:
        包含 owner, repo, branch 的字典，解析失败返回 None
    """
    try:
        # 清理 URL
        url = url.strip()
        
        # 如果没有协议，自动添加 https://
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # 解析 URL
        parsed = urlparse(url)
        
        # 检查是否是 GitHub
        if 'github.com' not in parsed.netloc:
            logger.warning(f"不是有效的 GitHub URL: {url}")
            return None
        
        # 解析路径: /owner/repo 或 /owner/repo/tree/branch
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if len(path_parts) < 2:
            logger.warning(f"URL 路径不完整: {url}")
            return None
        
        owner = path_parts[0]
        repo = path_parts[1]
        
        # 移除 .git 后缀（如果有）
        if repo.endswith('.git'):
            repo = repo[:-4]
        
        # 提取分支（如果 URL 中包含 /tree/branch）
        branch = None
        if len(path_parts) >= 4 and path_parts[2] == 'tree':
            branch = path_parts[3]
        
        result = {
            'owner': owner,
            'repo': repo,
            'branch': branch or 'main'  # 默认使用 main 分支
        }
        
        logger.info(f"解析 GitHub URL 成功: {result}")
        return result
        
    except Exception as e:
        logger.error(f"解析 GitHub URL 失败: {e}")
        return None

