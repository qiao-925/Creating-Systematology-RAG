"""
数据加载器模块 - 模块化版本
保持向后兼容的接口导出
"""

from src.data_loader.processor import DocumentProcessor, safe_print
from src.data_loader.source_loader import load_documents_from_source
from src.data_loader.directory_loader import load_documents_from_directory
from src.data_loader.web_loader import load_documents_from_urls
from src.data_loader.github_loader import (
    load_documents_from_github,
    load_documents_from_github_url
)
from src.data_loader.github_sync import sync_github_repository
from src.data_loader.github_url import parse_github_url

__all__ = [
    'DocumentProcessor',
    'safe_print',
    'load_documents_from_source',
    'load_documents_from_directory',
    'load_documents_from_urls',
    'load_documents_from_github',
    'load_documents_from_github_url',
    'sync_github_repository',
    'parse_github_url',
]

