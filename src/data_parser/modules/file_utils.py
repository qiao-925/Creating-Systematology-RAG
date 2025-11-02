"""
文档解析器 - 文件工具模块
文件验证和目录分组
"""

from pathlib import Path
from typing import List, Dict, Set

from src.logger import setup_logger

logger = setup_logger('document_parser')


def validate_files(file_paths: List[Path]) -> List[Path]:
    """验证文件存在性
    
    Args:
        file_paths: 文件路径列表
        
    Returns:
        有效的文件路径列表
    """
    valid_paths = []
    for file_path in file_paths:
        if not file_path.exists():
            logger.warning(f"文件不存在，跳过: {file_path}")
            continue
        if not file_path.is_file():
            logger.warning(f"不是文件，跳过: {file_path}")
            continue
        valid_paths.append(file_path)
    
    return valid_paths


def group_files_by_directory(file_paths: List[Path]) -> Dict[Path, List[Path]]:
    """按文件所在目录分组
    
    Args:
        file_paths: 文件路径列表
        
    Returns:
        目录到文件列表的映射
    """
    dir_files_map: Dict[Path, List[Path]] = {}
    for file_path in file_paths:
        dir_path = file_path.resolve().parent
        if dir_path not in dir_files_map:
            dir_files_map[dir_path] = []
        dir_files_map[dir_path].append(file_path.resolve())
    
    return dir_files_map

