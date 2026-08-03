"""
文档操作模块：批量添加文档到索引
"""

from typing import List, Dict, Tuple

from llama_index.core.schema import Document as LlamaDocument

from backend.infrastructure.indexer.utils.ids import get_vector_ids_batch
from backend.infrastructure.logger import get_logger

logger = get_logger('indexer')


def add_documents(index_manager, documents: List[LlamaDocument]) -> Tuple[int, Dict[str, List[str]]]:
    """批量添加文档到索引（优化：使用批量插入）
    
    Args:
        documents: 文档列表
        
    Returns:
        (成功添加的文档数量, 文件路径到向量ID的映射)
    """
    if not documents:
        return 0, {}
    
    try:
        # 优先尝试使用insert_ref_docs批量插入
        try:
            # 尝试不带参数调用（新版本 LlamaIndex 不支持 show_progress）
            try:
                index_manager._index.insert_ref_docs(documents, show_progress=False)
            except TypeError:
                index_manager._index.insert_ref_docs(documents)
            count = len(documents)
        except AttributeError:
            # 使用节点批量插入
            from llama_index.core.node_parser import SentenceSplitter
            node_parser = SentenceSplitter(
                chunk_size=index_manager.chunk_size,
                chunk_overlap=index_manager.chunk_overlap
            )
            all_nodes = node_parser.get_nodes_from_documents(documents)
            for node in all_nodes:
                index_manager._index.insert(node)
            count = len(documents)
        except Exception as e:
            logger.warning(f"[阶段2.3] 批量插入失败，回退到逐个插入: {e}")
            count = 0
            for doc in documents:
                try:
                    index_manager._index.insert(doc)
                    count += 1
                except Exception as insert_error:
                    logger.warning(f"[阶段2.3] ⚠️  添加文档失败 [{doc.metadata.get('file_path', 'unknown')}]: {insert_error}")
    except Exception as e:
        logger.error(f"[阶段2.3] ❌ 批量添加文档失败: {e}")
        return 0, {}
    
    # 批量查询向量ID映射
    file_paths = [doc.metadata.get("file_path", "") for doc in documents 
                 if doc.metadata.get("file_path")]
    vector_ids_map = get_vector_ids_batch(index_manager, file_paths)
    
    return count, vector_ids_map
