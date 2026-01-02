"""
增量更新模块：执行增量更新，处理新增、修改、删除的文档
"""

from typing import List

from llama_index.core.schema import Document as LlamaDocument

from src.infrastructure.indexer.utils.documents import add_documents
from src.infrastructure.indexer.utils.ids import delete_vectors_by_ids
from src.infrastructure.logger import get_logger

logger = get_logger('indexer')


def incremental_update(
    index_manager,
    added_docs: List[LlamaDocument],
    modified_docs: List[LlamaDocument],
    deleted_file_paths: List[str],
    github_sync_manager=None
) -> dict:
    """执行增量更新
    
    Args:
        added_docs: 新增的文档列表
        modified_docs: 修改的文档列表
        deleted_file_paths: 删除的文件路径列表
        github_sync_manager: GitHub同步管理器实例（用于查询向量ID）
        
    Returns:
        更新统计信息
    """
    stats = {
        "added": 0,
        "modified": 0,
        "deleted": 0,
        "errors": []
    }
    
    # 确保索引存在
    if index_manager._index is None:
        index_manager.get_index()
    
    # 1. 处理新增
    if added_docs:
        try:
            added_count, added_vector_ids = add_documents(index_manager, added_docs)
            stats["added"] = added_count
            logger.info(f"✅ 新增 {added_count} 个文档")
            
            # 更新同步状态的向量ID
            if github_sync_manager and added_docs:
                for doc in added_docs:
                    file_path = doc.metadata.get("file_path", "")
                    if file_path and file_path in added_vector_ids:
                        owner = doc.metadata.get("repository", "").split("/")[0] if "/" in doc.metadata.get("repository", "") else ""
                        repo = doc.metadata.get("repository", "").split("/")[1] if "/" in doc.metadata.get("repository", "") else ""
                        branch = doc.metadata.get("branch", "main")
                        
                        if owner and repo:
                            github_sync_manager.update_file_vector_ids(
                                owner, repo, branch, file_path,
                                added_vector_ids[file_path]
                            )
        except Exception as e:
            error_msg = f"新增文档失败: {e}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
    
    # 2. 处理修改（先批量删除旧的，再批量添加新的）
    if modified_docs:
        try:
            # 批量收集所有需要删除的向量ID
            all_vector_ids_to_delete = []
            for doc in modified_docs:
                file_path = doc.metadata.get("file_path", "")
                if file_path and github_sync_manager:
                    owner = doc.metadata.get("repository", "").split("/")[0] if "/" in doc.metadata.get("repository", "") else ""
                    repo = doc.metadata.get("repository", "").split("/")[1] if "/" in doc.metadata.get("repository", "") else ""
                    branch = doc.metadata.get("branch", "main")
                    
                    vector_ids = github_sync_manager.get_file_vector_ids(owner, repo, branch, file_path)
                    if vector_ids:
                        all_vector_ids_to_delete.extend(vector_ids)
            
            # 批量删除所有旧向量
            deleted_vector_count = 0
            if all_vector_ids_to_delete:
                unique_vector_ids = list(set(all_vector_ids_to_delete))
                batch_delete_size = 100
                for i in range(0, len(unique_vector_ids), batch_delete_size):
                    batch_ids = unique_vector_ids[i:i+batch_delete_size]
                    delete_vectors_by_ids(index_manager, batch_ids)
                    deleted_vector_count += len(batch_ids)
            
            # 批量添加新版本
            modified_count, modified_vector_ids = add_documents(index_manager, modified_docs)
            stats["modified"] = modified_count
            logger.info(f"✅ 更新 {modified_count} 个文档（批量删除 {deleted_vector_count} 个旧向量）")
            
            # 更新同步状态的向量ID
            if github_sync_manager and modified_docs:
                for doc in modified_docs:
                    file_path = doc.metadata.get("file_path", "")
                    if file_path and file_path in modified_vector_ids:
                        owner = doc.metadata.get("repository", "").split("/")[0] if "/" in doc.metadata.get("repository", "") else ""
                        repo = doc.metadata.get("repository", "").split("/")[1] if "/" in doc.metadata.get("repository", "") else ""
                        branch = doc.metadata.get("branch", "main")
                        
                        if owner and repo:
                            github_sync_manager.update_file_vector_ids(
                                owner, repo, branch, file_path,
                                modified_vector_ids[file_path]
                            )
        except Exception as e:
            error_msg = f"更新文档失败: {e}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
    
    # 3. 处理删除
    if deleted_file_paths and github_sync_manager:
        try:
            # 从同步状态获取向量ID并删除
            deleted_count = 0
            # 这里需要github_sync_manager提供向量ID信息
            # 暂时跳过具体实现
            stats["deleted"] = deleted_count
            logger.info(f"✅ 删除 {deleted_count} 个文档")
        except Exception as e:
            error_msg = f"删除文档失败: {e}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
    
    return stats
