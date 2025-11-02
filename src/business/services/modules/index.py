"""
RAG服务 - 索引构建处理模块
索引构建相关方法
"""

from typing import Optional

from src.logger import setup_logger
from src.business.services.modules.models import IndexResult

logger = setup_logger('rag_service')


def handle_build_index(
    service,
    source_path: str,
    collection_name: Optional[str] = None,
    **kwargs
) -> IndexResult:
    """处理索引构建请求
    
    Args:
        service: RAGService实例
        source_path: 数据源路径
        collection_name: 集合名称
        **kwargs: 其他参数
        
    Returns:
        IndexResult: 索引构建结果
    """
    target_collection = collection_name or service.collection_name
    logger.info(f"开始构建索引: source={source_path}, collection={target_collection}")
    
    try:
        # 检测数据源类型并加载文档
        from src.data_parser import DocumentParser
        
        if source_path.startswith(('http://', 'https://', 'git@')):
            # GitHub仓库或Web源
            if 'github.com' in source_path:
                from src.data_loader import load_documents_from_github
                documents = load_documents_from_github(source_path)
            else:
                from src.data_loader import load_documents_from_urls
                documents = load_documents_from_urls([source_path])
        else:
            # 本地文件系统
            from src.data_loader import load_documents_from_directory
            documents = load_documents_from_directory(source_path)
        
        if not documents:
            return IndexResult(
                success=False,
                collection_name=target_collection,
                doc_count=0,
                message="未找到文档"
            )
        
        # 构建索引
        service.index_manager.build_index(
            documents=documents,
            collection_name=target_collection,
            **kwargs
        )
        
        result = IndexResult(
            success=True,
            collection_name=target_collection,
            doc_count=len(documents),
            message=f"成功索引 {len(documents)} 个文档"
        )
        
        logger.info(f"索引构建成功: {result.message}")
        return result
        
    except Exception as e:
        logger.error(f"索引构建失败: {e}", exc_info=True)
        return IndexResult(
            success=False,
            collection_name=target_collection,
            doc_count=0,
            message=f"索引构建失败: {str(e)}"
        )

