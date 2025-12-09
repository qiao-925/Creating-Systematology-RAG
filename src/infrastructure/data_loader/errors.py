"""
数据导入错误处理模块：统一错误分类、处理和重试机制

主要功能：
- DataImportError类：数据导入错误基类
- NetworkError类：网络错误（可重试）
- AuthenticationError类：认证错误（不可重试）
- NotFoundError类：资源不存在（不可重试）
- ParseError类：解析错误（不可重试）
- classify_error()：分类错误类型，判断是否可重试
- handle_import_error()：统一错误处理，返回重试建议和错误消息
- retry_with_backoff()：带指数退避的重试装饰器

执行流程：
1. 捕获异常
2. 分类错误类型
3. 判断是否可重试
4. 根据错误类型决定重试或抛出异常

特性：
- 智能错误分类
- 指数退避重试机制
- 完整的错误消息处理
- 支持Unicode编码问题处理
"""

from typing import Tuple, Optional
import time

from src.infrastructure.logger import get_logger

logger = get_logger('data_loader_errors')


class DataImportError(Exception):
    """数据导入错误基类"""
    pass


class NetworkError(DataImportError):
    """网络错误（可重试）"""
    pass


class AuthenticationError(DataImportError):
    """认证错误（不可重试）"""
    pass


class NotFoundError(DataImportError):
    """资源不存在（不可重试）"""
    pass


class ParseError(DataImportError):
    """解析错误（不可重试）"""
    pass


def classify_error(error: Exception) -> Tuple[type, bool]:
    """分类错误类型
    
    Args:
        error: 异常对象
        
    Returns:
        (错误类型, 是否可重试)
    """
    error_str = str(error).lower()
    error_type = type(error).__name__
    
    # 网络相关错误（可重试）
    network_keywords = [
        'timeout', 'timed out', 'connection', 'network', 'tls', 'ssl',
        'handshake', 'unable to access', 'gnutls'
    ]
    if any(keyword in error_str for keyword in network_keywords):
        return NetworkError, True
    
    # 认证错误（不可重试）
    auth_keywords = ['401', 'unauthorized', 'bad credentials', 'authentication']
    if any(keyword in error_str for keyword in auth_keywords):
        return AuthenticationError, False
    
    # 资源不存在（不可重试）
    not_found_keywords = ['404', 'not found', '不存在']
    if any(keyword in error_str for keyword in not_found_keywords):
        return NotFoundError, False
    
    # 权限错误（不可重试）
    forbidden_keywords = ['403', 'forbidden', 'rate limit', '访问被拒绝']
    if any(keyword in error_str for keyword in forbidden_keywords):
        return AuthenticationError, False
    
    # 解析错误（不可重试）
    parse_keywords = ['parse', '解析', 'decode', 'encoding']
    if any(keyword in error_str for keyword in parse_keywords):
        return ParseError, False
    
    # 默认：网络错误（可重试）
    return NetworkError, True


def handle_import_error(
    error: Exception,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    attempt: int = 0
) -> Tuple[bool, str, Optional[Exception]]:
    """统一错误处理
    
    Args:
        error: 异常对象
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        attempt: 当前尝试次数
        
    Returns:
        (should_retry, error_message, error_type)
    """
    error_class, should_retry = classify_error(error)
    error_str = str(error)
    
    # 处理Unicode编码问题
    try:
        _ = error_str.encode('ascii')
    except UnicodeEncodeError:
        error_str = error_str.encode('ascii', 'replace').decode('ascii')
    
    # 构建错误消息
    match error_class:
        case cls if cls is NetworkError:
            error_message = f"网络错误: {error_str}"
        case cls if cls is AuthenticationError:
            error_message = f"认证错误: {error_str}"
        case cls if cls is NotFoundError:
            error_message = f"资源不存在: {error_str}"
        case cls if cls is ParseError:
            error_message = f"解析错误: {error_str}"
        case _:
            error_message = f"未知错误: {error_str}"
    
    # 判断是否应该重试
    if should_retry and attempt < max_retries:
        wait_time = retry_delay * (2 ** attempt)  # 指数退避
        logger.warning(
            f"错误（可重试）: {error_message}, "
            f"{wait_time:.1f}秒后重试 (尝试 {attempt + 1}/{max_retries})"
        )
        return True, error_message, error_class
    else:
        logger.error(f"错误（不可重试）: {error_message}")
        return False, error_message, error_class


def retry_with_backoff(
    func,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    error_handler=None
):
    """带指数退避的重试装饰器
    
    Args:
        func: 要重试的函数
        max_retries: 最大重试次数
        retry_delay: 初始重试延迟（秒）
        error_handler: 错误处理函数（可选）
        
    Returns:
        函数结果或抛出最后一个异常
    """
    def wrapper(*args, **kwargs):
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                if attempt < max_retries:
                    should_retry, error_msg, error_type = handle_import_error(
                        e, max_retries, retry_delay, attempt
                    )
                    
                    if should_retry:
                        wait_time = retry_delay * (2 ** attempt)
                        time.sleep(wait_time)
                        continue
                    else:
                        # 不可重试的错误，直接抛出
                        break
                else:
                    # 达到最大重试次数
                    break
        
        # 所有重试都失败，抛出最后一个异常
        if error_handler:
            error_handler(last_error)
        raise last_error
    
    return wrapper
