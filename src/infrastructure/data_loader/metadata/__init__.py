"""
元数据管理模块 - 向后兼容层：保持向后兼容的接口导出

主要功能：
- FileChange类：文件变更记录类，包含新增、修改、删除的文件列表
- MetadataManager类：元数据管理器，管理GitHub仓库的元数据，追踪文件变化

执行流程：
1. 初始化元数据管理器
2. 检测文件变更
3. 更新元数据
4. 支持增量更新

特性：
- 文件变更追踪
- 元数据持久化
- 增量更新支持
- 完整的错误处理
"""

from src.infrastructure.data_loader.metadata.file_change import FileChange
from src.infrastructure.data_loader.metadata.manager import MetadataManager

__all__ = [
    'FileChange',
    'MetadataManager',
]
