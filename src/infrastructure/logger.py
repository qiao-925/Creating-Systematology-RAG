"""
日志系统配置模块：提供统一的日志记录功能（基于 structlog）

主要功能：
- get_logger()：获取 structlog logger

特性：
- 结构化日志，便于搜索和分析
- 自动记录上下文信息
- JSON 格式便于日志聚合工具处理
- 开发环境使用控制台格式，生产环境使用 JSON 格式
"""

# 直接导出 structlog logger
from src.infrastructure.logger_structlog import get_logger

__all__ = ['get_logger']
