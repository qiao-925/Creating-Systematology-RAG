"""
元数据管理 - 仓库操作模块
仓库元数据的增删改查操作
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime

from llama_index.core.schema import Document as LlamaDocument

from src.logger import setup_logger

logger = setup_logger('metadata_manager')


def update_repository_metadata(
    manager,
    owner: str,
    repo: str,
    branch: str,
    documents: List[LlamaDocument],
    vector_ids_map: Optional[Dict[str, List[str]]] = None,
    commit_sha: Optional[str] = None
):
    """更新仓库元数据
    
    Args:
        manager: MetadataManager实例
        owner: 仓库所有者
        repo: 仓库名称
        branch: 分支名称
        documents: 文档列表
        vector_ids_map: 文件路径到向量ID的映射
        commit_sha: 当前 commit SHA
    """
    from src.metadata.utils import compute_hash
    
    repo_key = manager.get_repository_key(owner, repo, branch)
    
    # 构建文件元数据
    files_metadata = {}
    for doc in documents:
        file_path = doc.metadata.get("file_path", "")
        if file_path:
            file_hash = compute_hash(doc.text)
            files_metadata[file_path] = {
                "hash": file_hash,
                "size": len(doc.text),
                "last_modified": datetime.now().isoformat(),
                "vector_ids": vector_ids_map.get(file_path, []) if vector_ids_map else []
            }
    
    # 更新仓库元数据
    manager.metadata["repositories"][repo_key] = {
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "last_commit_sha": commit_sha or "",
        "last_indexed_at": datetime.now().isoformat(),
        "file_count": len(files_metadata),
        "files": files_metadata
    }
    
    logger.info(f"更新仓库元数据 [{repo_key}]: {len(files_metadata)} 个文件")
    
    # 保存到磁盘
    manager.save_metadata()


def update_file_vector_ids(
    manager,
    owner: str,
    repo: str,
    branch: str,
    file_path: str,
    vector_ids: List[str]
):
    """更新单个文件的向量ID列表
    
    Args:
        manager: MetadataManager实例
        owner: 仓库所有者
        repo: 仓库名称
        branch: 分支名称
        file_path: 文件路径
        vector_ids: 向量ID列表
    """
    repo_key = manager.get_repository_key(owner, repo, branch)
    repo_metadata = manager.metadata["repositories"].get(repo_key)
    
    if not repo_metadata:
        logger.warning(f"仓库 {repo_key} 不存在，无法更新向量ID")
        return
    
    files = repo_metadata.get("files", {})
    if file_path in files:
        files[file_path]["vector_ids"] = vector_ids
        logger.debug(f"更新文件向量ID [{file_path}]: {len(vector_ids)} 个向量")
    else:
        logger.warning(f"文件 {file_path} 不存在于仓库元数据中")


def get_file_vector_ids(
    manager,
    owner: str,
    repo: str,
    branch: str,
    file_path: str
) -> List[str]:
    """获取文件的向量ID列表
    
    Args:
        manager: MetadataManager实例
        owner: 仓库所有者
        repo: 仓库名称
        branch: 分支名称
        file_path: 文件路径
        
    Returns:
        向量ID列表
    """
    repo_key = manager.get_repository_key(owner, repo, branch)
    repo_metadata = manager.metadata["repositories"].get(repo_key)
    
    if not repo_metadata:
        return []
    
    files = repo_metadata.get("files", {})
    file_metadata = files.get(file_path, {})
    return file_metadata.get("vector_ids", [])


def remove_repository(manager, owner: str, repo: str, branch: str = "main"):
    """移除仓库的元数据
    
    Args:
        manager: MetadataManager实例
        owner: 仓库所有者
        repo: 仓库名称
        branch: 分支名称
    """
    repo_key = manager.get_repository_key(owner, repo, branch)
    
    if repo_key in manager.metadata["repositories"]:
        del manager.metadata["repositories"][repo_key]
        logger.info(f"移除仓库元数据: {repo_key}")
        manager.save_metadata()
    else:
        logger.warning(f"仓库 {repo_key} 不存在，无法移除")


def list_repositories(manager) -> List[Dict]:
    """列出所有已追踪的仓库
    
    Args:
        manager: MetadataManager实例
        
    Returns:
        仓库信息列表
    """
    repos = []
    for repo_key, repo_data in manager.metadata["repositories"].items():
        repos.append({
            "key": repo_key,
            "owner": repo_data.get("owner", ""),
            "repo": repo_data.get("repo", ""),
            "branch": repo_data.get("branch", "main"),
            "file_count": repo_data.get("file_count", 0),
            "last_indexed_at": repo_data.get("last_indexed_at", ""),
            "commit_sha": repo_data.get("last_commit_sha", "")[:8] if repo_data.get("last_commit_sha") else None
        })
    return repos


def get_documents_by_change(
    documents: List[LlamaDocument],
    changes
) -> Tuple[List[LlamaDocument], List[LlamaDocument], List[str]]:
    """根据变更类型分组文档
    
    Args:
        documents: 当前文档列表
        changes: 变更记录
        
    Returns:
        (新增文档列表, 修改文档列表, 删除文件路径列表)
    """
    # 创建文件路径到文档的映射
    doc_map = {}
    for doc in documents:
        file_path = doc.metadata.get("file_path", "")
        if file_path:
            doc_map[file_path] = doc
    
    # 分组
    added_docs = [doc_map[path] for path in changes.added if path in doc_map]
    modified_docs = [doc_map[path] for path in changes.modified if path in doc_map]
    deleted_paths = changes.deleted
    
    return added_docs, modified_docs, deleted_paths

