"""
数据加载器模块 - 统一入口

提供数据加载功能的统一入口，内部使用 DataImportService。
此文件作为向后兼容层，保持原有导入路径可用。

推荐使用：
    from backend.infrastructure.data_loader import DataImportService
"""

# 从新模块导入所有公开接口
from backend.infrastructure.data_loader import (
    DocumentProcessor,
    safe_print,
    DataImportService,
    ImportResult,
    ProgressReporter,
    sync_github_repository,
    parse_github_url,
    handle_github_error,
)

__all__ = [
    'DocumentProcessor',
    'safe_print',
    'DataImportService',
    'ImportResult',
    'ProgressReporter',
    'sync_github_repository',
    'parse_github_url',
    'handle_github_error',
]
