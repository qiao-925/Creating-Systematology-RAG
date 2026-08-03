"""
数据导入服务：核心文档加载流程

主要功能：
- 从数据源加载文档的核心流程
- 支持进度追踪和取消机制
"""

import time
from typing import List, Optional, TYPE_CHECKING

from llama_index.core.schema import Document as LlamaDocument

from backend.infrastructure.logger import get_logger
from backend.infrastructure.data_loader.processor import DocumentProcessor
from backend.infrastructure.data_loader.models import ProgressReporter

if TYPE_CHECKING:
    from backend.infrastructure.data_loader.source import DataSource
    from backend.infrastructure.data_loader.progress import ImportProgressManager

logger = get_logger('data_loader_service')

# 检查新架构是否可用
try:
    from backend.infrastructure.data_loader.parser import DocumentParser
    NEW_ARCHITECTURE_AVAILABLE = True
except ImportError:
    NEW_ARCHITECTURE_AVAILABLE = False
    DocumentParser = None


def load_documents_from_source(
    source: "DataSource",
    clean: bool = True,
    show_progress: bool = True,
    progress_reporter: ProgressReporter = None,
    progress_manager: Optional["ImportProgressManager"] = None
) -> List[LlamaDocument]:
    """从数据源加载文档（核心加载流程）
    
    Args:
        source: 数据源对象（GitHubSource, LocalFileSource等）
        clean: 是否清理文本
        show_progress: 是否显示进度
        progress_reporter: 进度反馈器（可选）
        progress_manager: 进度管理器（可选）
        
    Returns:
        文档列表
    """
    if not NEW_ARCHITECTURE_AVAILABLE:
        logger.error("[阶段1.2] 新架构未可用")
        return []
    
    if progress_reporter is None:
        progress_reporter = ProgressReporter(show_progress=show_progress)
    
    try:
        total_start_time = time.time()
        
        progress_reporter.print_if_enabled("🔍 正在从数据源获取文件路径...")
        
        source_start_time = time.time()
        source_files = source.get_file_paths()
        source_elapsed = time.time() - source_start_time
        
        if not source_files:
            logger.warning(f"[阶段1.2] 数据源未返回任何文件")
            progress_reporter.print_if_enabled("⚠️  未找到任何文件")
            return []
        
        logger.info(f"[阶段1.2] 数据源返回 {len(source_files)} 个文件 (耗时: {source_elapsed:.2f}s)")
        progress_reporter.print_if_enabled(f"✅ 找到 {len(source_files)} 个文件")
        
        # 取消检查点
        if progress_manager and progress_manager.check_cancelled():
            return []
        
        file_paths = [sf.path for sf in source_files]
        metadata_map = {
            sf.path: {**sf.metadata, 'source_type': sf.source_type}
            for sf in source_files
        }
        
        progress_reporter.print_if_enabled("📄 正在解析文件...")
        
        # 开始解析阶段
        if progress_manager:
            from backend.infrastructure.data_loader.progress import ImportStage
            progress_manager.start_stage(ImportStage.DOC_PARSE, total=len(file_paths))
        
        parser_start_time = time.time()
        documents = DocumentParser().parse_files(
            file_paths, metadata_map, clean=clean,
            progress_callback=_create_progress_callback(progress_manager) if progress_manager else None
        )
        parser_elapsed = time.time() - parser_start_time
        
        # 完成解析阶段
        if progress_manager:
            progress_manager.complete_stage(
                ImportStage.DOC_PARSE, 
                f"解析完成 ({len(documents)} 个文档)"
            )
        
        # 取消检查点
        if progress_manager and progress_manager.check_cancelled():
            return []
        
        if not documents:
            logger.warning(f"[阶段1.3] 解析器未返回任何文档 (输入文件数: {len(file_paths)})")
            progress_reporter.print_if_enabled("⚠️  未能解析任何文档")
            return []
        
        logger.info(f"[阶段1.3] 解析器返回 {len(documents)} 个文档 (耗时: {parser_elapsed:.2f}s)")
        
        clean_start_time = time.time()
        if clean:
            processor = DocumentProcessor()
            documents = [
                LlamaDocument(
                    text=processor.clean_text(doc.text),
                    metadata=doc.metadata,
                    id_=doc.id_
                )
                for doc in documents
            ]
        clean_elapsed = time.time() - clean_start_time if clean else 0.0
        
        total_elapsed = time.time() - total_start_time
        progress_reporter.print_if_enabled(f"✅ 成功加载 {len(documents)} 个文档")
        
        success_rate = (len(documents) / len(source_files) * 100) if source_files else 0
        logger.info(
            f"[阶段1.3] 文档加载完成: 源文件数={len(source_files)}, "
            f"解析文档数={len(documents)}, 成功率={success_rate:.1f}%, "
            f"总耗时={total_elapsed:.2f}s (获取路径={source_elapsed:.2f}s, "
            f"解析={parser_elapsed:.2f}s, 清理={clean_elapsed:.2f}s)"
        )
        
        return documents
        
    except Exception as e:
        logger.error(f"[阶段1.3] 文档加载失败: {e}", exc_info=True)
        progress_reporter.report_error(f"文档加载失败: {str(e)}")
        return []


def _create_progress_callback(progress_manager: "ImportProgressManager"):
    """创建进度回调函数"""
    def callback(current: int, total: int, filename: str = ""):
        progress_manager.update_progress(current, f"解析: {filename}" if filename else None)
    return callback
