"""
文档解析器 - 缓存处理模块
缓存检查和保存逻辑
"""

import pickle
from pathlib import Path
from typing import List, Optional

from llama_index.core.schema import Document as LlamaDocument

from src.logger import setup_logger

logger = setup_logger('document_parser')


def check_cache(cache_manager, task_id: str, file_paths: List[Path]) -> Optional[List[LlamaDocument]]:
    """检查缓存并加载文档
    
    Args:
        cache_manager: 缓存管理器实例
        task_id: 任务ID
        file_paths: 文件路径列表
        
    Returns:
        缓存的文档列表，如果不存在则返回None
    """
    from src.config import config
    
    if not config.ENABLE_CACHE:
        return None
    
    try:
        input_hash = _compute_files_hash(file_paths)
        step_name = cache_manager.STEP_PARSE
        
        if cache_manager.check_step_cache(task_id, step_name, input_hash):
            cached_docs = _load_cached_documents(cache_manager, task_id)
            if cached_docs:
                logger.info(f"✅ 使用缓存: 加载了 {len(cached_docs)} 个已解析的文档")
                return cached_docs
    except Exception as e:
        logger.warning(f"检查缓存失败: {e}")
    
    return None


def save_cache(cache_manager, task_id: str, file_paths: List[Path], documents: List[LlamaDocument]):
    """保存解析结果到缓存
    
    Args:
        cache_manager: 缓存管理器实例
        task_id: 任务ID
        file_paths: 文件路径列表
        documents: 解析后的文档列表
    """
    from src.config import config
    
    if not config.ENABLE_CACHE:
        return
    
    try:
        input_hash = _compute_files_hash(file_paths)
        step_name = cache_manager.STEP_PARSE
        
        # 保存文档到临时文件
        cache_file = cache_manager.get_step_cache_file(task_id, step_name)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_file, 'wb') as f:
            pickle.dump(documents, f)
        
        cache_manager.mark_step_completed(
            task_id=task_id,
            step_name=step_name,
            input_hash=input_hash
        )
        
        logger.debug(f"解析结果已缓存: {len(documents)} 个文档")
    except Exception as e:
        logger.warning(f"保存缓存失败: {e}")


def _compute_files_hash(file_paths: List[Path]) -> str:
    """计算文件路径列表的哈希值
    
    Args:
        file_paths: 文件路径列表
        
    Returns:
        哈希值字符串
    """
    import hashlib
    
    # 使用文件路径的排序字符串计算哈希
    paths_str = '|'.join(sorted(str(p.resolve()) for p in file_paths))
    return hashlib.md5(paths_str.encode('utf-8')).hexdigest()


def _load_cached_documents(cache_manager, task_id: str) -> Optional[List[LlamaDocument]]:
    """从缓存加载文档
    
    Args:
        cache_manager: 缓存管理器实例
        task_id: 任务ID
        
    Returns:
        缓存的文档列表，如果加载失败返回None
    """
    try:
        step_name = cache_manager.STEP_PARSE
        cache_file = cache_manager.get_step_cache_file(task_id, step_name)
        
        if not cache_file.exists():
            return None
        
        with open(cache_file, 'rb') as f:
            documents = pickle.load(f)
        
        return documents
    except Exception as e:
        logger.warning(f"加载缓存文档失败: {e}")
        return None

