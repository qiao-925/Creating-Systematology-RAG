"""
GitHub加载器工具函数模块：GitHub相关错误处理

主要功能：
- handle_github_error()：处理GitHub相关错误，提供详细的用户提示

特性：
- 完整的错误处理
- 用户友好的错误提示
- ASCII安全输出
"""

from src.infrastructure.logger import get_logger

logger = get_logger('data_loader')


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
    from src.infrastructure.data_loader.processor import safe_print
    
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

