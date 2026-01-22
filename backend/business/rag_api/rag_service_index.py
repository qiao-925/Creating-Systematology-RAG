"""
RAG服务：索引管理功能

主要功能：
- 索引构建
- 集合管理
"""

from typing import Optional
from pathlib import Path

from backend.infrastructure.indexer import IndexManager
from backend.infrastructure.logger import get_logger
from backend.business.rag_api.models import IndexResult

logger = get_logger('rag_service')


def load_documents_from_source(source_path: str) -> tuple[list, Optional[str]]:
    """从数据源加载文档
    
    Args:
        source_path: 数据源路径（本地目录或GitHub URL）
        
    Returns:
        (文档列表, 错误信息)
    """
    from backend.infrastructure.data_loader import DataImportService
    
    try:
        path_obj = Path(source_path)
        
        if path_obj.exists() and path_obj.is_dir():
            # 本地目录
            service = DataImportService()
            result = service.import_from_directory(str(path_obj))
            return result.documents, None
        elif source_path.startswith(('http://', 'https://')):
            # GitHub URL
            service = DataImportService()
            result = service.import_from_github(source_path)
            return result.documents, None
        else:
            return [], f"无效的数据源路径: {source_path}"
    except Exception as e:
        logger.error(f"加载文档失败: {e}", exc_info=True)
        return [], str(e)


def build_index(
    index_manager: IndexManager,
    source_path: str,
    collection_name: Optional[str] = None
) -> IndexResult:
    """构建索引
    
    Args:
        index_manager: 索引管理器
        source_path: 数据源路径
        collection_name: 集合名称（可选）
        
    Returns:
        索引构建结果
    """
    logger.info("开始构建索引", source_path=source_path, collection_name=collection_name)
    
    # 加载文档
    documents, error = load_documents_from_source(source_path)
    if error:
        return IndexResult(
            success=False,
            message=f"加载文档失败: {error}",
            document_count=0,
            collection_name=collection_name or index_manager.collection_name
        )
    
    if not documents:
        return IndexResult(
            success=False,
            message="未找到任何文档",
            document_count=0,
            collection_name=collection_name or index_manager.collection_name
        )
    
    # 构建索引
    try:
        if collection_name:
            index_manager.collection_name = collection_name
        
        index_manager.build_index(documents)
        
        stats = index_manager.get_stats()
        document_count = stats.get('document_count', len(documents))
        
        logger.info("索引构建成功", document_count=document_count, collection_name=index_manager.collection_name)
        
        return IndexResult(
            success=True,
            message=f"成功构建索引，包含 {document_count} 个文档",
            document_count=document_count,
            collection_name=index_manager.collection_name
        )
    except Exception as e:
        logger.error(f"索引构建失败: {e}", exc_info=True)
        return IndexResult(
            success=False,
            message=f"索引构建失败: {str(e)}",
            document_count=0,
            collection_name=collection_name or index_manager.collection_name
        )


def list_collections(index_manager: IndexManager) -> list:
    """列出所有向量集合"""
    try:
        collections = index_manager.list_collections()
        logger.info("列出集合", count=len(collections))
        return collections
    except Exception as e:
        logger.error("列出集合失败", error=str(e))
        return []


def delete_collection(index_manager: IndexManager, collection_name: str) -> bool:
    """删除向量集合"""
    try:
        index_manager.delete_collection(collection_name)
        logger.info("删除集合", collection=collection_name)
        return True
    except Exception as e:
        logger.error("删除集合失败", collection=collection_name, error=str(e))
        return False
