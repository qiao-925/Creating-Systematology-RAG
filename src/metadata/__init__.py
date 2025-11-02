"""
元数据管理模块 - 向后兼容层
保持向后兼容的接口导出
"""

from src.metadata.file_change import FileChange
from src.metadata.manager import MetadataManager

__all__ = [
    'FileChange',
    'MetadataManager',
]

