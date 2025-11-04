"""
文档解析器 - 解析工具模块
单文件和目录解析逻辑
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document as LlamaDocument

from src.logger import setup_logger

logger = setup_logger('document_parser')


def parse_single_file(
    file_path: Path,
    metadata_map: Optional[Dict[Path, Dict[str, Any]]] = None
) -> List[LlamaDocument]:
    """解析单个文件
    
    Args:
        file_path: 文件路径
        metadata_map: 元数据映射
        
    Returns:
        文档列表
    """
    try:
        dir_path = file_path.parent
        file_name = file_path.name
        
        reader = SimpleDirectoryReader(
            input_dir=str(dir_path),
            recursive=False,
            filename_as_id=True,
            errors='ignore'
        )
        
        documents = reader.load_data()
        
        # 过滤出目标文件
        filtered_docs = []
        for doc in documents:
            doc_file_path = doc.metadata.get('file_path', '')
            if Path(doc_file_path).name == file_name:
                # 应用元数据
                if metadata_map and file_path in metadata_map:
                    doc.metadata.update(metadata_map[file_path])
                filtered_docs.append(doc)
        
        return filtered_docs
    except Exception as e:
        logger.error(f"解析文件失败 {file_path}: {e}")
        return []


def parse_directory_files(
    dir_path: Path,
    files: List[Path],
    metadata_map: Optional[Dict[Path, Dict[str, Any]]] = None
) -> List[LlamaDocument]:
    """解析目录中的文件
    
    Args:
        dir_path: 目录路径
        files: 文件路径列表
        metadata_map: 元数据映射
        
    Returns:
        文档列表
    """
    from src.data_parser.modules.matching import match_documents_to_files
    
    try:
        dir_start_time = time.time()
        logger.debug(f"解析目录: {dir_path} (包含 {len(files)} 个文件)")
        
        # 获取文件扩展名列表
        extensions = {f.suffix for f in files if f.suffix}
        
        # 使用 SimpleDirectoryReader 加载目录
        reader = SimpleDirectoryReader(
            input_dir=str(dir_path),
            recursive=False,
            required_exts=list(extensions) if extensions else None,
            filename_as_id=True,
            errors='ignore'
        )
        
        dir_documents = reader.load_data()
        logger.debug(f"SimpleDirectoryReader 返回 {len(dir_documents)} 个文档")
        
        # 匹配文档到文件
        matched_docs = match_documents_to_files(dir_documents, files, dir_path, metadata_map)
        
        elapsed = time.time() - dir_start_time
        logger.debug(f"目录解析完成: {len(matched_docs)} 个文档 (耗时: {elapsed:.2f}s)")
        
        return matched_docs
        
    except Exception as e:
        logger.error(f"解析目录失败 {dir_path}: {e}", exc_info=True)
        return []

