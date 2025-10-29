"""
数据来源层
负责从不同数据源获取文件路径
"""

from src.data_source.base import DataSource, SourceFile
from src.data_source.github_source import GitHubSource
from src.data_source.local_source import LocalFileSource
from src.data_source.web_source import WebSource

__all__ = [
    'DataSource',
    'SourceFile',
    'GitHubSource',
    'LocalFileSource',
    'WebSource',
]

