"""
数据加载器统一入口模块
从数据源加载文档的统一接口
"""

import time
from typing import List, Optional

from llama_index.core.schema import Document as LlamaDocument

from src.data_source import DataSource
from src.data_parser import DocumentParser
from src.data_loader.processor import DocumentProcessor, safe_print
from src.logger import setup_logger

logger = setup_logger('data_loader')

# 检查新架构是否可用
try:
    from src.data_source import DataSource, GitHubSource, LocalFileSource, WebSource
    from src.data_parser import DocumentParser
    NEW_ARCHITECTURE_AVAILABLE = True
except ImportError:
    NEW_ARCHITECTURE_AVAILABLE = False


def load_documents_from_source(
    source: DataSource,
    clean: bool = True,
    show_progress: bool = True,
    cache_manager=None,
    task_id: Optional[str] = None
) -> List[LlamaDocument]:
    """从数据源加载文档（统一入口函数）
    
    新架构的统一入口，整合数据来源层和解析层
    
    Args:
        source: 数据源对象（GitHubSource, LocalFileSource, WebSource等）
        clean: 是否清理文本
        show_progress: 是否显示进度
        cache_manager: 缓存管理器实例（可选）
        task_id: 任务ID（可选，用于缓存）
        
    Returns:
        文档列表
    """
    if not NEW_ARCHITECTURE_AVAILABLE:
        logger.error("新架构未可用")
        return []
    
    try:
        total_start_time = time.time()
        
        # 步骤1: 从数据源获取文件路径
        if show_progress:
            safe_print(f"🔍 正在从数据源获取文件路径...")
        
        source_start_time = time.time()
        source_files = source.get_files()
        source_elapsed = time.time() - source_start_time
        
        if not source_files:
            logger.warning(f"数据源未返回任何文件")
            if show_progress:
                safe_print("⚠️  未找到任何文件")
            return []
        
        logger.info(f"数据源返回 {len(source_files)} 个文件 (耗时: {source_elapsed:.2f}s)")
        if show_progress:
            safe_print(f"✅ 找到 {len(source_files)} 个文件")
        
        # 步骤2: 构建文件路径列表和元数据映射
        logger.debug("构建文件路径列表和元数据映射")
        file_paths = [sf.path for sf in source_files]
        metadata_map = {}
        for sf in source_files:
            metadata_map[sf.path] = {
                **sf.metadata,
                'source_type': sf.source_type
            }
        logger.debug(f"元数据映射包含 {len(metadata_map)} 个条目")
        
        # 步骤3: 使用解析器解析文件
        if show_progress:
            safe_print(f"📄 正在解析文件...")
        
        parser_start_time = time.time()
        parser = DocumentParser()
        documents = parser.parse_files(
            file_paths, 
            metadata_map, 
            clean=clean,
            cache_manager=cache_manager,
            task_id=task_id
        )
        parser_elapsed = time.time() - parser_start_time
        
        if not documents:
            logger.warning(f"解析器未返回任何文档 (输入文件数: {len(file_paths)})")
            if show_progress:
                safe_print("⚠️  未能解析任何文档")
            return []
        
        logger.info(f"解析器返回 {len(documents)} 个文档 (耗时: {parser_elapsed:.2f}s)")
        
        # 步骤4: 可选的文本清理
        clean_elapsed = 0.0
        if clean:
            logger.debug("开始文本清理")
            clean_start_time = time.time()
            processor = DocumentProcessor()
            cleaned_documents = []
            for doc in documents:
                cleaned_text = processor.clean_text(doc.text)
                cleaned_doc = LlamaDocument(
                    text=cleaned_text,
                    metadata=doc.metadata,
                    id_=doc.id_
                )
                cleaned_documents.append(cleaned_doc)
            documents = cleaned_documents
            clean_elapsed = time.time() - clean_start_time
        else:
            logger.debug("跳过文本清理")
        
        total_elapsed = time.time() - total_start_time
        
        if show_progress:
            safe_print(f"✅ 成功加载 {len(documents)} 个文档")
        
        success_rate = (len(documents) / len(source_files) * 100) if source_files else 0
        logger.info(
            f"文档加载完成: "
            f"源文件数={len(source_files)}, "
            f"解析文档数={len(documents)}, "
            f"成功率={success_rate:.1f}%, "
            f"总耗时={total_elapsed:.2f}s "
            f"(获取路径={source_elapsed:.2f}s, "
            f"解析={parser_elapsed:.2f}s, "
            f"清理={clean_elapsed:.2f}s)"
        )
        
        return documents
        
    except Exception as e:
        logger.error(f"从数据源加载文档失败: {e}")
        if show_progress:
            safe_print(f"❌ 加载失败: {e}")
        return []

