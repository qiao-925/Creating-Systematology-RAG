"""
日志系统配置模块
提供统一的日志记录功能
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logger(name: str, log_dir: Optional[Path] = None) -> logging.Logger:
    """配置日志系统
    
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
    
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    # 文件处理器（按日期）
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器（只显示 WARNING 及以上）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    
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


