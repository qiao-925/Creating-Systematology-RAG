"""
数据加载器工具模块：包含解析器相关的辅助工具函数

主要功能：
- validate_files()、group_files_by_directory()：文件工具函数
- parse_single_file()、parse_directory_files()：解析工具函数
- match_documents_to_files()：文档匹配函数

执行流程：
1. 文件验证和分组
2. 文件解析
3. 文档匹配

特性：
- 模块化工具函数
- 文件验证和分组
- 文档匹配功能
"""

from src.infrastructure.data_loader.utils.file_utils import validate_files, group_files_by_directory
from src.infrastructure.data_loader.utils.parse_utils import parse_single_file, parse_directory_files
from src.infrastructure.data_loader.utils.matching import match_documents_to_files

__all__ = [
    'validate_files',
    'group_files_by_directory',
    'parse_single_file',
    'parse_directory_files',
    'match_documents_to_files',
]
