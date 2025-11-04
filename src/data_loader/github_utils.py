"""
GitHub加载器工具函数模块
包含文件过滤、文档转换等辅助函数
"""

from typing import List, Optional

from llama_index.core.schema import Document as LlamaDocument

from src.logger import setup_logger

logger = setup_logger('data_loader')


def build_file_filter(
    filter_directories: Optional[List[str]] = None,
    filter_file_extensions: Optional[List[str]] = None
):
    """构建文件过滤器函数
    
    将用户友好的参数格式转换为 LangChain GitLoader 需要的 lambda 函数
    
    Args:
        filter_directories: 只包含指定目录的文件（例如: ["docs", "examples"]）
        filter_file_extensions: 只包含指定扩展名的文件（例如: [".md", ".py"]）
        
    Returns:
        文件过滤器函数 file_filter(file_path: str) -> bool
    """
    def file_filter(file_path: str) -> bool:
        """判断文件是否应该被加载
        
        Args:
            file_path: 相对于仓库根目录的文件路径
            
        Returns:
            是否加载该文件
        """
        # 默认排除的目录和文件
        excluded_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.pytest_cache'}
        excluded_exts = {'.pyc', '.pyo', '.lock', '.log'}
        
        # 检查是否在排除目录中
        path_parts = file_path.split('/')
        if any(part in excluded_dirs for part in path_parts):
            return False
        
        # 检查是否是排除的扩展名
        if any(file_path.endswith(ext) for ext in excluded_exts):
            return False
        
        # 如果指定了目录过滤
        if filter_directories:
            if not any(file_path.startswith(d.rstrip('/') + '/') or file_path.startswith(d.rstrip('/')) 
                      for d in filter_directories):
                return False
        
        # 如果指定了扩展名过滤
        if filter_file_extensions:
            if not any(file_path.endswith(ext) for ext in filter_file_extensions):
                return False
        
        return True
    
    return file_filter


def convert_langchain_to_llama_doc(
    lc_doc,
    owner: str,
    repo: str,
    branch: str
) -> LlamaDocument:
    """将 LangChain Document 转换为 LlamaIndex LlamaDocument
    
    Args:
        lc_doc: LangChain Document 对象
        owner: 仓库所有者
        repo: 仓库名称
        branch: 分支名称
        
    Returns:
        LlamaDocument 对象
    """
    # 从 LangChain Document 提取信息
    file_path = lc_doc.metadata.get('file_path', lc_doc.metadata.get('source', ''))
    file_name = lc_doc.metadata.get('file_name', '')
    
    # 如果没有 file_name，从 file_path 中提取
    if not file_name and file_path:
        file_name = file_path.split('/')[-1]
    
    # 构建 LlamaDocument
    return LlamaDocument(
        text=lc_doc.page_content,
        metadata={
            'file_path': file_path,
            'file_name': file_name,
            'source': lc_doc.metadata.get('source', ''),
            'source_type': 'github',
            'repository': f"{owner}/{repo}",
            'branch': branch,
            'url': f"https://github.com/{owner}/{repo}/blob/{branch}/{file_path}",
        },
        id_=f"github_{owner}_{repo}_{branch}_{file_path}"
    )


def handle_github_error(error: Exception, owner: str, repo: str, show_progress: bool = True) -> str:
    """统一 GitHub 错误处理
    
    Args:
        error: 异常对象
        owner: 仓库所有者
        repo: 仓库名称
        show_progress: 是否显示详细错误提示
        
    Returns:
        错误描述字符串（ASCII 安全）
    """
    from src.data_loader.processor import safe_print
    
    error_type = type(error).__name__
    error_str = str(error)
    
    # 处理 UnicodeEncodeError：安全转换错误消息
    try:
        _ = error_str.encode('ascii')
    except UnicodeEncodeError:
        error_str = error_str.encode('ascii', 'replace').decode('ascii')
    
    # GitHub API 错误
    if "404" in error_str or "Not Found" in error_str:
        if show_progress:
            safe_print(f"❌ 仓库不存在: {owner}/{repo}")
            safe_print("   请检查：1) 仓库名拼写 2) 是否为私有仓库（需要Token）")
        return "仓库不存在(404)"
    
    elif "403" in error_str or "Forbidden" in error_str or "rate limit" in error_str.lower():
        if show_progress:
            safe_print(f"❌ 访问被拒绝: {owner}/{repo}")
            safe_print("   请检查：1) Token权限 2) API限流（GitHub限制：每小时60次，有Token为5000次）")
            safe_print("   建议：配置 GITHUB_TOKEN 环境变量以提高限额")
        return "访问被拒绝(403)"
    
    elif "401" in error_str or "Unauthorized" in error_str or "Bad credentials" in error_str:
        if show_progress:
            safe_print(f"❌ 认证失败")
            safe_print("   请检查：1) Token是否正确 2) Token是否过期")
        return "认证失败(401)"
    
    # 网络相关错误
    elif "timeout" in error_str.lower() or "timed out" in error_str.lower():
        if show_progress:
            safe_print(f"❌ 网络超时: {owner}/{repo}")
            safe_print("   建议：1) 检查网络连接 2) 稍后重试")
        return "网络超时"
    
    elif "connection" in error_str.lower():
        if show_progress:
            safe_print(f"❌ 网络连接失败")
            safe_print("   建议：1) 检查网络 2) 检查代理设置")
        return "网络连接失败"
    
    # 通用错误
    else:
        if show_progress:
            safe_print(f"❌ 加载失败: {error_type}: {error}")
            safe_print(f"   如果问题持续，请报告到项目 Issue")
        return f"{error_type}: {error_str}"

