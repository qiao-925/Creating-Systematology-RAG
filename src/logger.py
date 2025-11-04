"""
日志系统配置模块
提供统一的日志记录功能
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


def _get_log_level(level_str: str) -> int:
    """将字符串日志级别转换为 logging 常量
    
    Args:
        level_str: 日志级别字符串（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        
    Returns:
        logging 级别常量
        
    Raises:
        ValueError: 当级别字符串无效时
    """
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


def setup_logger(name: str, log_dir: Optional[Path] = None) -> logging.Logger:
    """配置日志系统
    
    日志级别从配置中读取：
    - LOG_LEVEL: 控制台日志级别（默认 INFO）
    - LOG_FILE_LEVEL: 文件日志级别（默认 DEBUG）
    
    Args:
        name: 日志器名称
        log_dir: 日志目录，默认为项目根目录下的 logs/
        
    Returns:
        配置好的 Logger 对象
    """
    if log_dir is None:
        log_dir = Path(__file__).parent.parent / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建 logger
    logger = logging.getLogger(name)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 从配置读取日志级别（延迟导入避免循环依赖）
    try:
        from src.config import config
        console_level_str = config.LOG_LEVEL
        file_level_str = config.LOG_FILE_LEVEL
    except Exception:
        # 如果配置不可用，使用默认值
        console_level_str = "INFO"
        file_level_str = "DEBUG"
    
    console_level = _get_log_level(console_level_str)
    file_level = _get_log_level(file_level_str)
    
    # Logger 级别设置为两者中的最低级别，确保所有消息都能被处理
    logger.setLevel(min(console_level, file_level))
    logger.propagate = False
    
    # 文件处理器（按日期）
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(file_level)
    
    # 控制台处理器
    # 注意：Windows 下需要特殊处理编码
    import sys
    
    # 确保 stdout 使用 UTF-8 编码（如果 encoding 模块已加载）
    try:
        from src.encoding import ensure_utf8_stdout
        ensure_utf8_stdout()
    except ImportError:
        # encoding 模块可能尚未加载，尝试基础设置
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    
    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """获取已配置的 logger（如果不存在则创建）
    
    Args:
        name: 日志器名称
        
    Returns:
        Logger 对象
    """
    return setup_logger(name)


if __name__ == "__main__":
    # 测试日志系统
    logger = setup_logger("test_logger")
    
    logger.debug("这是 DEBUG 消息（不会在控制台显示）")
    logger.info("这是 INFO 消息（只写入文件）")
    logger.warning("这是 WARNING 消息（文件+控制台）")
    logger.error("这是 ERROR 消息（文件+控制台）")
    logger.critical("这是 CRITICAL 消息（文件+控制台）")
    
    print(f"\n✅ 日志已写入: logs/{datetime.now().strftime('%Y-%m-%d')}.log")


