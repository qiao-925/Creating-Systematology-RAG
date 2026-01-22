"""
数据导入服务 - 统一入口：封装GitHub和本地导入功能，提供统一的接口、错误处理、重试机制和进度反馈

主要功能：
- ImportResult类：导入结果数据类，包含文档列表、成功状态、统计信息等
- ProgressReporter类：进度反馈器，用于显示导入进度
- DataImportService类：数据导入服务，提供统一的导入接口

执行流程：
1. 初始化数据源（GitHub或本地文件）
2. 从数据源获取文件路径
3. 解析文件并生成文档
4. 返回导入结果和统计信息

特性：
- 支持GitHub和本地文件导入
- 完整的错误处理和重试机制
- 进度反馈和日志记录
- 统计信息收集
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, TYPE_CHECKING

from llama_index.core.schema import Document as LlamaDocument

from backend.infrastructure.logger import get_logger
from backend.infrastructure.data_loader.processor import DocumentProcessor
from backend.infrastructure.data_loader.models import ImportResult, ProgressReporter
from backend.infrastructure.data_loader.document_loader import load_documents_from_source

if TYPE_CHECKING:
    from backend.infrastructure.data_loader.source import DataSource

logger = get_logger('data_loader_service')

# 检查新架构是否可用
try:
    from backend.infrastructure.data_loader.source import GitHubSource, LocalFileSource
    from backend.infrastructure.data_loader.parser import DocumentParser
    NEW_ARCHITECTURE_AVAILABLE = True
    _GitHubSource = GitHubSource  # 保存引用以便后续使用
except ImportError:
    NEW_ARCHITECTURE_AVAILABLE = False
    _GitHubSource = None


class DataImportService:
    """数据导入服务 - 统一入口
    
    封装所有数据导入功能，提供统一的接口、错误处理、重试机制和进度反馈。
    只支持GitHub和本地两种数据源。
    """
    
    def __init__(
        self,
        show_progress: bool = True,
        enable_cache: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """初始化数据导入服务
        
        Args:
            show_progress: 是否显示进度
            enable_cache: 是否启用缓存（已废弃：缓存管理器功能已移除，此参数不再使用）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.show_progress = show_progress
        self.enable_cache = enable_cache  # 已废弃：保留参数以保持接口兼容性
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.progress_reporter = ProgressReporter(show_progress=show_progress)
    
    def import_from_source(
        self,
        source: "DataSource",
        clean: bool = True
    ) -> ImportResult:
        """从数据源导入文档
        
        Args:
            source: 数据源对象（GitHubSource, LocalFileSource）
            clean: 是否清理文本
            
        Returns:
            ImportResult: 导入结果（包含文档列表、统计信息、错误信息）
        """
        start_time = time.time()
        errors = []
        warnings = []
        
        try:
            self.progress_reporter.report_stage("🔍", "正在从数据源获取文件路径...")
            
            # 调用核心加载流程
            documents = load_documents_from_source(
                source=source,
                clean=clean,
                show_progress=self.show_progress,
                progress_reporter=self.progress_reporter
            )
            
            elapsed = time.time() - start_time
            
            # 构建统计信息
            stats = {
                'document_count': len(documents),
                'elapsed_time': elapsed,
                'source_type': getattr(source, 'source_type', 'unknown'),
            }
            
            # 获取数据源元数据
            if hasattr(source, 'get_source_metadata'):
                source_metadata = source.get_source_metadata()
                stats.update(source_metadata)
            
            if documents:
                self.progress_reporter.report_success(
                    f"成功导入 {len(documents)} 个文档 (耗时: {elapsed:.2f}s)"
                )
                return ImportResult(
                    documents=documents,
                    success=True,
                    stats=stats,
                    errors=errors,
                    warnings=warnings
                )
            else:
                warnings.append("未找到任何文档")
                self.progress_reporter.report_warning("未找到任何文档")
                return ImportResult(
                    documents=[],
                    success=False,
                    stats=stats,
                    errors=errors,
                    warnings=warnings
                )
                
        except Exception as e:
            error_msg = str(e)
            errors.append(error_msg)
            self.progress_reporter.report_error(f"导入失败: {error_msg}")
            logger.error(f"从数据源导入失败: {e}", exc_info=True)
            
            return ImportResult(
                documents=[],
                success=False,
                stats={'elapsed_time': time.time() - start_time},
                errors=errors,
                warnings=warnings
            )
    
    def import_from_directory(
        self,
        directory: str | Path,
        recursive: bool = True,
        clean: bool = True,
        **kwargs
    ) -> ImportResult:
        """从目录导入文档
        
        Args:
            directory: 目录路径
            recursive: 是否递归加载
            clean: 是否清理文本
            **kwargs: 其他参数（保留用于向后兼容）
            
        Returns:
            ImportResult: 导入结果
        """
        if not NEW_ARCHITECTURE_AVAILABLE:
            error_msg = "新架构未可用，无法使用统一服务"
            self.progress_reporter.report_error(error_msg)
            return ImportResult(
                documents=[],
                success=False,
                errors=[error_msg]
            )
        
        try:
            self.progress_reporter.report_stage("📂", f"从目录加载: {directory}")
            
            source = LocalFileSource(
                source=directory,
                recursive=recursive
            )
            
            result = self.import_from_source(source, clean=clean)
            
            # 为 Markdown 文件提取标题（保持原有行为）
            if result.success:
                for doc in result.documents:
                    file_name = doc.metadata.get('file_name', '')
                    if any(file_name.endswith(ext) for ext in ['.md', '.markdown']):
                        title = DocumentProcessor.extract_title_from_markdown(doc.text)
                        if not title:
                            title = Path(file_name).stem if file_name else "未命名"
                        doc.metadata.update({
                            "title": title,
                            "source_type": doc.metadata.get("source_type", "markdown"),
                        })
            
            return result
            
        except Exception as e:
            error_msg = f"从目录导入失败: {str(e)}"
            self.progress_reporter.report_error(error_msg)
            logger.error(error_msg, exc_info=True)
            return ImportResult(
                documents=[],
                success=False,
                errors=[error_msg]
            )
    
    def import_from_github(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        clean: bool = True,
        filter_directories: Optional[List[str]] = None,
        filter_file_extensions: Optional[List[str]] = None,
        **kwargs
    ) -> ImportResult:
        """从GitHub仓库导入文档
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称（默认 main）
            clean: 是否清理文本
            filter_directories: 只加载指定目录（可选）
            filter_file_extensions: 只加载指定扩展名（可选）
            **kwargs: 其他参数
            
        Returns:
            ImportResult: 导入结果
        """
        if not NEW_ARCHITECTURE_AVAILABLE:
            error_msg = "新架构未可用，无法使用统一服务"
            self.progress_reporter.report_error(error_msg)
            return ImportResult(
                documents=[],
                success=False,
                errors=[error_msg]
            )
        
        try:
            self.progress_reporter.report_stage(
                "🐙", 
                f"从GitHub加载: {owner}/{repo}@{branch}"
            )
            
            source = GitHubSource(
                owner=owner,
                repo=repo,
                branch=branch,
                filter_directories=filter_directories,
                filter_file_extensions=filter_file_extensions,
                show_progress=self.show_progress
            )
            
            return self.import_from_source(
                source,
                clean=clean
            )
            
        except Exception as e:
            error_msg = f"从GitHub导入失败: {str(e)}"
            self.progress_reporter.report_error(error_msg)
            logger.error(error_msg, exc_info=True)
            return ImportResult(
                documents=[],
                success=False,
                errors=[error_msg]
            )
    
    def sync_github_repository(
        self,
        owner: str,
        repo: str,
        branch: str,
        github_sync_manager,
        filter_directories: Optional[List[str]] = None,
        filter_file_extensions: Optional[List[str]] = None
    ) -> tuple:
        """增量同步GitHub仓库
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            github_sync_manager: GitHub同步管理器
            filter_directories: 只加载指定目录（可选）
            filter_file_extensions: 只加载指定扩展名（可选）
            
        Returns:
            (所有文档列表, FileChange对象, commit_sha)
        """
        from backend.infrastructure.data_loader.github_sync import FileChange
        from backend.infrastructure.config import config
        
        # 步骤 1: 克隆/更新仓库，获取最新 commit SHA
        try:
            from backend.infrastructure.git import GitRepositoryManager
            if GitRepositoryManager is None:
                error_msg = "GitRepositoryManager 未安装"
                self.progress_reporter.report_error(error_msg)
                return [], FileChange(), None
            
            git_manager = GitRepositoryManager(config.GITHUB_REPOS_PATH)
            self.progress_reporter.report_stage("🔄", f"正在同步仓库: {owner}/{repo}@{branch}")
            
            repo_path, commit_sha = git_manager.clone_or_update(
                owner=owner,
                repo=repo,
                branch=branch
            )
            
            self.progress_reporter.report_success(f"仓库已同步 (Commit: {commit_sha[:8]})")
            
        except RuntimeError as e:
            error_msg = f"Git 操作失败: {str(e)}"
            self.progress_reporter.report_error(error_msg)
            logger.error(error_msg)
            return [], FileChange(), None
        
        # 步骤 2: 快速检测 - 检查 commit SHA 是否变化
        old_sync_state = github_sync_manager.get_repository_sync_state(owner, repo, branch)
        
        if old_sync_state:
            old_commit_sha = old_sync_state.get('last_commit_sha', '')
            if old_commit_sha == commit_sha:
                # Commit 未变化，跳过加载
                self.progress_reporter.report_success("仓库无新提交，跳过加载")
                logger.info(f"仓库 {owner}/{repo}@{branch} 无新提交 (Commit: {commit_sha[:8]})")
                return [], FileChange(), commit_sha
        
        # 步骤 3: 有新提交，加载文档
        self.progress_reporter.report_stage("📄", "检测到新提交，正在加载文档...")
        
        import_result = self.import_from_github(
            owner=owner,
            repo=repo,
            branch=branch,
            clean=True,
            filter_directories=filter_directories,
            filter_file_extensions=filter_file_extensions
        )
        
        if not import_result.success or not import_result.documents:
            logger.warning(f"未能加载任何文档从 {owner}/{repo}")
            return [], FileChange(), commit_sha
        
        documents = import_result.documents
        
        # 步骤 4: 精细检测 - 文件级变更
        self.progress_reporter.report_stage("🔍", "正在检测文件变更...")
        
        changes = github_sync_manager.detect_changes(owner, repo, branch, documents)
        
        if changes.has_changes():
            self.progress_reporter.report_success(f"检测结果: {changes.summary()}")
        else:
            self.progress_reporter.report_success("没有检测到文件变更")
        
        return documents, changes, commit_sha
    
    def import_from_github_url(
        self,
        github_url: str,
        clean: bool = True,
        **kwargs
    ) -> ImportResult:
        """从GitHub URL导入文档
        
        Args:
            github_url: GitHub仓库URL
            clean: 是否清理文本
            **kwargs: 其他参数
            
        Returns:
            ImportResult: 导入结果
        """
        from backend.infrastructure.data_loader.github_url import parse_github_url
        
        # 解析URL
        repo_info = parse_github_url(github_url)
        if not repo_info:
            error_msg = f"无法解析GitHub URL: {github_url}"
            self.progress_reporter.report_error(error_msg)
            return ImportResult(
                documents=[],
                success=False,
                errors=[error_msg]
            )
        
        # 调用import_from_github
        return self.import_from_github(
            owner=repo_info['owner'],
            repo=repo_info['repo'],
            branch=repo_info.get('branch', 'main'),
            clean=clean,
            **kwargs
        )
    
