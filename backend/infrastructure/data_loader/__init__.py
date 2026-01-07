"""
数据加载器模块 - 统一的数据导入服务

核心功能：从本地目录或GitHub仓库导入文档，解析为LlamaIndex文档对象。

快速开始：
    >>> from backend.infrastructure.data_loader import DataImportService
    >>> service = DataImportService()
    >>> result = service.import_from_directory("./data")
    >>> docs = result.documents

主要接口：
- DataImportService: 统一导入服务（推荐）
  - import_from_directory(): 本地目录导入
  - import_from_github(): GitHub仓库导入
  - sync_github_repository(): GitHub增量同步
- 便捷函数: load_documents_from_directory(), load_documents_from_github()
- 底层组件: DataSource, DocumentParser（高级用法）

模块结构：
- service.py: 服务层，统一导入接口和流程编排
- source/: 数据源层（GitHub、本地文件）
- parser.py + utils/: 解析层（文档解析、缓存、文件处理）
- errors.py, processor.py: 错误处理、文本清理

设计说明：
本包整合了数据导入的完整流程（数据源→解析→清理），采用服务层统一接口。
将原本分散的 data_parser 和 data_source 模块整合，简化项目结构。
"""

from pathlib import Path
from typing import List, Optional

from llama_index.core.schema import Document as LlamaDocument

from backend.infrastructure.data_loader.processor import DocumentProcessor, safe_print
from backend.infrastructure.data_loader.github_utils import handle_github_error
from backend.infrastructure.data_loader.github_sync import sync_github_repository
from backend.infrastructure.data_loader.github_url import parse_github_url

# 统一服务类（新接口）
from backend.infrastructure.data_loader.service import DataImportService, ImportResult, ProgressReporter
from backend.infrastructure.data_loader.errors import (
    DataImportError,
    NetworkError,
    AuthenticationError,
    NotFoundError,
    ParseError,
    handle_import_error,
    retry_with_backoff
)

# 导出数据源和解析器
from backend.infrastructure.data_loader.source import DataSource, SourceFile, GitHubSource, LocalFileSource
from backend.infrastructure.data_loader.parser import DocumentParser

# 导出GitHub同步管理
from backend.infrastructure.data_loader.github_sync import FileChange, GitHubSyncManager

# 便捷函数（使用统一服务）
def load_documents_from_directory(
    directory_path: str | Path,
    recursive: bool = True,
    clean: bool = True,
    **kwargs
) -> List[LlamaDocument]:
    """从目录加载文档（便捷函数，使用DataImportService）
    
    Args:
        directory_path: 目录路径
        recursive: 是否递归加载
        clean: 是否清理文本
        **kwargs: 其他参数
        
    Returns:
        文档列表
    """
    service = DataImportService(show_progress=True)
    result = service.import_from_directory(
        directory=directory_path,
        recursive=recursive,
        clean=clean,
        **kwargs
    )
    return result.documents if result.success else []


def load_documents_from_github(
    owner: str,
    repo: str,
    branch: Optional[str] = None,
    clean: bool = True,
    show_progress: bool = True,
    filter_directories: Optional[List[str]] = None,
    filter_file_extensions: Optional[List[str]] = None
) -> List[LlamaDocument]:
    """从GitHub仓库加载文档（便捷函数，使用DataImportService）
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        branch: 分支名称（可选）
        clean: 是否清理文本
        show_progress: 是否显示进度
        filter_directories: 只加载指定目录（可选）
        filter_file_extensions: 只加载指定扩展名（可选）
        
    Returns:
        文档列表
    """
    service = DataImportService(show_progress=show_progress)
    result = service.import_from_github(
        owner=owner,
        repo=repo,
        branch=branch or "main",
        clean=clean,
        filter_directories=filter_directories,
        filter_file_extensions=filter_file_extensions
    )
    return result.documents if result.success else []


def load_documents_from_github_url(
    github_url: str,
    clean: bool = True,
    show_progress: bool = True
) -> List[LlamaDocument]:
    """从GitHub URL加载文档（便捷函数，使用DataImportService）
    
    Args:
        github_url: GitHub仓库URL
        clean: 是否清理文本
        show_progress: 是否显示进度
        
    Returns:
        文档列表
    """
    service = DataImportService(show_progress=show_progress)
    result = service.import_from_github_url(github_url, clean=clean)
    return result.documents if result.success else []


__all__ = [
    # 工具类
    'DocumentProcessor',
    'safe_print',
    # GitHub工具
    'sync_github_repository',
    'parse_github_url',
    'handle_github_error',
    # 统一服务接口（推荐使用）
    'DataImportService',
    'ImportResult',
    'ProgressReporter',
    # 便捷函数
    'load_documents_from_directory',
    'load_documents_from_github',
    'load_documents_from_github_url',
    # 错误处理
    'DataImportError',
    'NetworkError',
    'AuthenticationError',
    'NotFoundError',
    'ParseError',
    'handle_import_error',
    'retry_with_backoff',
    # 数据源和解析器
    'DataSource',
    'SourceFile',
    'GitHubSource',
    'LocalFileSource',
    'DocumentParser',
    # GitHub同步管理
    'FileChange',
    'GitHubSyncManager',
]

# 导出为 _handle_github_error（别名）
_handle_github_error = handle_github_error

