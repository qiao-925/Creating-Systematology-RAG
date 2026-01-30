"""
结构化日志配置模块：基于 structlog 的日志系统

主要功能：
- setup_structlog()：配置 structlog，支持 JSON、控制台和文件输出
- get_logger()：获取配置好的 structlog logger
- 支持从配置读取日志级别
- 开发环境使用控制台格式，生产环境使用 JSON 格式
- 文件日志持久化到根目录，支持按日期轮转

特性：
- 结构化日志，便于搜索和分析
- 自动记录上下文信息（函数名、模块名等）
- JSON 格式便于日志聚合工具处理
- 文件日志按日期轮转，自动清理旧日志
"""

import os
import sys
import logging
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

import structlog
from structlog.stdlib import LoggerFactory
from structlog.processors import TimeStamper, JSONRenderer


def _get_log_level(level_str: str) -> int:
    """将字符串日志级别转换为 logging 常量
    
    Args:
        level_str: 日志级别字符串（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        
    Returns:
        logging 级别常量
    """
    import logging
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    level_upper = level_str.upper()
    if level_upper not in level_map:
        valid_levels = ", ".join(level_map.keys())
        raise ValueError(
            f"无效的日志级别: {level_str}。有效值: {valid_levels}"
        )
    return level_map[level_upper]


def _is_production() -> bool:
    """判断是否为生产环境
    
    Returns:
        是否为生产环境
    """
    env = os.getenv("ENVIRONMENT", "").lower()
    return env in ("production", "prod")


def _get_console_level() -> str:
    """从配置获取控制台日志级别
    
    Returns:
        日志级别字符串
    """
    try:
        from backend.infrastructure.config import config
        return config.LOG_LEVEL
    except Exception:
        return "INFO"


def _get_file_level() -> str:
    """从配置获取文件日志级别
    
    Returns:
        日志级别字符串
    """
    try:
        from backend.infrastructure.config import config
        return config.LOG_FILE_LEVEL
    except Exception:
        return "DEBUG"


def _get_log_file_path() -> Path:
    """获取日志文件路径
    
    Returns:
        日志文件路径（项目根目录下的 logs/app.log）
    """
    # 获取项目根目录（logger_structlog.py 在 backend/infrastructure/ 下）
    project_root = Path(__file__).parent.parent.parent
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    return log_dir / "app.log"


def setup_structlog() -> None:
    """配置 structlog
    
    根据环境选择输出格式：
    - 生产环境：JSON 格式（便于日志聚合）
    - 开发环境：控制台格式（便于阅读）
    """
    is_prod = _is_production()
    console_level = _get_console_level()
    file_level = _get_file_level()
    
    # 基础处理器链
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        TimeStamper(fmt="iso", utc=False),  # 使用本地时间
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # 根据环境选择输出格式
    if is_prod:
        # 生产环境：JSON 格式
        processors.append(JSONRenderer())
    else:
        # 开发环境：控制台格式
        processors.append(structlog.dev.ConsoleRenderer())
    
    # 配置 structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 配置标准库 logging
    root_logger = logging.getLogger()
    # 设置根日志级别为最低级别，让各个处理器自己决定过滤
    root_logger.setLevel(logging.DEBUG)
    
    # 清除已有的处理器，避免重复添加
    root_logger.handlers.clear()
    
    # 控制台处理器（输出到 stdout）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(_get_log_level(console_level))
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    # 确保控制台输出不被缓冲
    console_handler.stream = sys.stdout
    root_logger.addHandler(console_handler)
    
    # 文件处理器（输出到文件，按日期轮转）
    log_file_path = _get_log_file_path()
    file_handler = TimedRotatingFileHandler(
        filename=str(log_file_path),
        when='midnight',  # 每天午夜轮转
        interval=1,  # 每1天
        backupCount=30,  # 保留30天的日志
        encoding='utf-8',
        delay=False,
    )
    file_handler.setLevel(_get_log_level(file_level))
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(file_handler)
    
    # 抑制底层HTTP库的详细调试日志（避免噪音）
    # 这些日志通常来自urllib3、httpx、httpcore等HTTP客户端库
    # 注意：chromadb 本身的日志保留，以便显示连接状态等有用信息
    http_loggers = [
        # HTTP 客户端库（完全抑制，这些太详细）
        'urllib3',
        'urllib3.connectionpool',
        'urllib3.util',
        'httpx',
        'httpcore',
        'httpcore.http11',
        'httpcore.connection',
        'httpcore.http2',
        'httpcore.sync',
        'httpcore.async',
    ]
    for logger_name in http_loggers:
        http_logger = logging.getLogger(logger_name)
        http_logger.setLevel(logging.WARNING)  # 只显示警告及以上级别
        http_logger.propagate = False
    
    # 抑制遥测和调试相关的日志（对用户无用的信息）
    telemetry_loggers = [
        # PostHog（Chroma 遥测库）
        'posthog',
        'posthog.client',
        # Chroma 遥测模块
        'chromadb.telemetry',
    ]
    for logger_name in telemetry_loggers:
        telemetry_logger = logging.getLogger(logger_name)
        telemetry_logger.setLevel(logging.WARNING)
        telemetry_logger.propagate = False
    
    # 抑制 LiteLLM 的 DEBUG 日志（非常详细，对用户无用）
    litellm_loggers = [
        'LiteLLM',
        'litellm',
        'LiteLLM Proxy',
        'LiteLLM Router',
    ]
    for logger_name in litellm_loggers:
        litellm_logger = logging.getLogger(logger_name)
        litellm_logger.setLevel(logging.WARNING)
        litellm_logger.propagate = False
    
    # 抑制 Streamlit 后台线程的 ScriptRunContext 警告
    streamlit_logger = logging.getLogger('streamlit.runtime.scriptrunner_utils.script_run_context')
    streamlit_logger.setLevel(logging.ERROR)
    streamlit_logger.propagate = False
    
    # 注意：chromadb、chromadb.api、chromadb.client 等保留默认日志级别
    # 这样可以看到连接成功、集合创建等有用的 INFO 级别日志


def get_logger(name: str) -> structlog.BoundLogger:
    """获取配置好的 structlog logger
    
    Args:
        name: logger 名称（通常是模块名）
        
    Returns:
        配置好的 structlog logger
    """
    # 确保 structlog 已配置
    if not structlog.is_configured():
        setup_structlog()
    
    return structlog.get_logger(name)


# 初始化时自动配置
if not structlog.is_configured():
    setup_structlog()
