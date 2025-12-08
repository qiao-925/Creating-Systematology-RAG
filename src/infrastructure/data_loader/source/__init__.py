"""
数据来源层：负责从不同数据源获取文件路径

主要功能：
- DataSource类：数据源抽象基类，定义统一接口
- SourceFile类：数据源文件信息数据类
- GitHubSource类：GitHub数据源实现
- LocalFileSource类：本地文件数据源实现

执行流程：
1. 创建数据源实例
2. 调用get_file_paths()获取文件路径列表
3. 返回SourceFile列表

特性：
- 统一的数据源接口
- 支持多种数据源类型
- 完整的元数据支持
"""

from src.infrastructure.data_loader.source.base import DataSource, SourceFile
from src.infrastructure.data_loader.source.github import GitHubSource
from src.infrastructure.data_loader.source.local import LocalFileSource

__all__ = [
    'DataSource',
    'SourceFile',
    'GitHubSource',
    'LocalFileSource',
]
