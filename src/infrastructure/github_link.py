"""
GitHub链接生成器：所有引用统一通过GitHub在线查看

主要功能：
- generate_github_url()：生成GitHub在线查看链接

执行流程：
1. 从元数据提取仓库、分支、文件路径信息
2. 构建GitHub URL
3. 返回可访问的链接

特性：
- 自动链接生成
- 支持多种元数据格式
- 完整的错误处理
"""
from typing import Optional
from pathlib import Path


def generate_github_url(metadata: dict) -> Optional[str]:
    """生成 GitHub 在线查看链接
    
    Args:
        metadata: 文档元数据，必需字段：
            - repository: "owner/repo"
            - branch: "main" (可选，默认 main)
            - file_path: "相对路径/文件名.md"
    
    Returns:
        GitHub URL 或 None（无法生成时）
    
    示例:
        >>> generate_github_url({
        ...     'repository': 'qiao-925/Creating-Systematology-Test',
        ...     'branch': 'main',
        ...     'file_path': 'docs/README.md'
        ... })
        'https://github.com/qiao-925/Creating-Systematology-Test/blob/main/docs/README.md'
    """
    repository = metadata.get('repository')
    branch = metadata.get('branch', 'main')
    file_path = metadata.get('file_path', '')
    
    # 验证必需字段
    if not repository or not file_path:
        return None
    
    # 清理路径（移除开头的斜杠）
    file_path = file_path.lstrip('/')
    
    # 构建 GitHub blob URL
    return f"https://github.com/{repository}/blob/{branch}/{file_path}"


def get_display_title(metadata: dict) -> str:
    """获取显示标题
    
    优先级: title > file_name > file_path 文件名 > 'Unknown'
    
    Args:
        metadata: 文档元数据
        
    Returns:
        显示标题字符串
    """
    # 优先使用 title
    if metadata.get('title'):
        return metadata['title']
    
    # 其次使用 file_name
    if metadata.get('file_name'):
        return metadata['file_name']
    
    # 从 file_path 提取文件名
    file_path = metadata.get('file_path', '')
    if file_path:
        return Path(file_path).name
    
    return 'Unknown'

