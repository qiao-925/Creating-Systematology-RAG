"""
文档解析器 - 文档匹配模块：文档到文件的匹配逻辑

主要功能：
- match_documents_to_files()：匹配文档到文件，应用元数据映射

执行流程：
1. 解析目录得到文档列表
2. 根据文件路径匹配文档
3. 应用元数据映射
4. 返回匹配后的文档列表

特性：
- 智能文档匹配
- 元数据映射支持
- 完整的日志记录
- 性能统计
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from llama_index.core.schema import Document as LlamaDocument

from src.infrastructure.logger import get_logger

logger = get_logger('document_parser')


def match_documents_to_files(
    dir_documents: List[LlamaDocument],
    files: List[Path],
    dir_path: Path,
    metadata_map: Optional[Dict[Path, Dict[str, Any]]] = None
) -> List[LlamaDocument]:
    """匹配文档到文件
    
    Args:
        dir_documents: 目录解析得到的文档列表
        files: 目标文件路径列表
        dir_path: 目录路径
        metadata_map: 元数据映射
        
    Returns:
        匹配的文档列表
    """
    # 构建规范化路径集合
    normalized_file_paths: Dict[Path, Path] = {}
    file_names_to_paths: Dict[str, List[Path]] = {}
    
    for orig_path in files:
        normalized_path = orig_path.resolve()
        normalized_file_paths[normalized_path] = orig_path
        
        name = orig_path.name
        if name not in file_names_to_paths:
            file_names_to_paths[name] = []
        file_names_to_paths[name].append(orig_path)
    
    # 匹配文档
    filtered_docs = []
    matched_paths: Set[Path] = set()
    
    for doc in dir_documents:
        doc_file_path_str = doc.metadata.get('file_path', '')
        if not doc_file_path_str:
            logger.debug("文档缺少 file_path 元数据，跳过")
            continue
        
        # 规范化文档路径
        doc_file_path = Path(doc_file_path_str)
        if not doc_file_path.is_absolute():
            doc_file_path = (dir_path / doc_file_path).resolve()
        else:
            doc_file_path = doc_file_path.resolve()
        
        # 匹配逻辑
        matching_path = None
        
        # 方法1：直接路径匹配
        if doc_file_path in normalized_file_paths:
            matching_path = normalized_file_paths[doc_file_path]
        else:
            # 方法2：文件名匹配
            file_name = doc_file_path.name
            if file_name in file_names_to_paths:
                candidates = file_names_to_paths[file_name]
                if len(candidates) == 1:
                    matching_path = candidates[0]
                elif len(candidates) > 1:
                    # 多个同名文件，尝试相对路径匹配
                    try:
                        relative_doc_path = doc_file_path.relative_to(dir_path)
                        for candidate in candidates:
                            try:
                                relative_candidate = candidate.relative_to(dir_path)
                                if relative_doc_path == relative_candidate:
                                    matching_path = candidate
                                    break
                            except ValueError:
                                continue
                    except ValueError:
                        pass
        
        if matching_path:
            # 应用元数据
            if metadata_map and matching_path in metadata_map:
                doc.metadata.update(metadata_map[matching_path])
            
            filtered_docs.append(doc)
            matched_paths.add(matching_path)
    
    # 记录未匹配的文件
    unmatched = set(files) - matched_paths
    if unmatched:
        logger.warning(f"有 {len(unmatched)} 个文件未匹配到文档")
        for path in list(unmatched)[:5]:  # 只记录前5个
            logger.debug(f"未匹配文件: {path}")
    
    return filtered_docs
