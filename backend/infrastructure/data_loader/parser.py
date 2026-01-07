"""
文档解析器 - 核心解析模块：DocumentParser类和主要解析逻辑

主要功能：
- DocumentParser类：统一文档解析器，使用SimpleDirectoryReader自动支持多种文件格式
- parse_files()：解析文件列表，返回文档列表

执行流程：
1. 验证文件路径
2. 使用SimpleDirectoryReader解析文件
3. 应用元数据映射
4. 返回文档列表

特性：
- 自动支持多种文件格式
- 元数据映射
- 完整的错误处理
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document as LlamaDocument

from backend.infrastructure.logger import get_logger
from backend.infrastructure.data_loader.utils.file_utils import validate_files, group_files_by_directory
from backend.infrastructure.data_loader.utils.parse_utils import parse_single_file, parse_directory_files

logger = get_logger('document_parser')


class DocumentParser:
    """统一文档解析器
    
    使用 SimpleDirectoryReader 自动支持多种文件格式
    """
    
    def parse_files(
        self,
        file_paths: List[Path],
        metadata_map: Optional[Dict[Path, Dict[str, Any]]] = None,
        clean: bool = True
    ) -> List[LlamaDocument]:
        """解析文件列表，返回文档列表
        
        Args:
            file_paths: 文件路径列表
            metadata_map: 文件路径到元数据的映射（可选）
            clean: 是否清理文本（暂不使用，保留接口）
            
        Returns:
            文档列表
        """
        start_time = time.time()
        
        if not file_paths:
            logger.warning("[阶段1.3] 文件路径列表为空")
            return []
        
        logger.info(f"[阶段1.3] 开始解析 {len(file_paths)} 个文件")
        
        try:
            # 验证文件存在性
            valid_paths = validate_files(file_paths)
            
            if not valid_paths:
                logger.warning("[阶段1.3] 没有有效的文件路径")
                return []
            
            logger.info(f"[阶段1.3] 有效文件数量: {len(valid_paths)}/{len(file_paths)}")
            
            # 对于单个文件或少量文件，逐个解析
            if len(valid_paths) <= 3:
                unique_dirs = {p.parent for p in valid_paths}
                if len(unique_dirs) == len(valid_paths):
                    logger.debug("[阶段1.3] 文件分散在不同目录，采用逐个解析模式")
                    documents = []
                    for file_path in valid_paths:
                        parsed = parse_single_file(file_path, metadata_map)
                        documents.extend(parsed)
                    
                    elapsed = time.time() - start_time
                    logger.info(f"[阶段1.3] 成功解析 {len(documents)}/{len(valid_paths)} 个文档 (耗时: {elapsed:.2f}s)")
                    
                    return documents
            
            # 按目录分组批量处理
            dir_files_map = group_files_by_directory(valid_paths)
            logger.debug(f"[阶段1.3] 文件分布在 {len(dir_files_map)} 个目录中")
            
            documents = []
            for dir_path, files in dir_files_map.items():
                try:
                    dir_docs = parse_directory_files(dir_path, files, metadata_map)
                    documents.extend(dir_docs)
                except Exception as e:
                    logger.error(f"[阶段1.3] 解析目录失败 {dir_path}: {e}", exc_info=True)
                    continue
            
            elapsed = time.time() - start_time
            logger.info(f"[阶段1.3] 成功解析 {len(documents)}/{len(valid_paths)} 个文档 (耗时: {elapsed:.2f}s)")
            
            return documents
            
        except Exception as e:
            logger.error(f"[阶段1.3] 解析文件失败: {e}", exc_info=True)
            return []
