"""
元数据管理 - 变更检测模块
文件变更检测相关方法
"""

from typing import List, Set, Dict
from datetime import datetime

from llama_index.core.schema import Document as LlamaDocument

from src.logger import setup_logger
from src.metadata.file_change import FileChange
from src.metadata.utils import compute_hash

logger = setup_logger('metadata_manager')


def detect_changes(
    manager,
    owner: str,
    repo: str,
    branch: str,
    current_documents: List[LlamaDocument]
) -> FileChange:
    """检测文件变更
    
    Args:
        manager: MetadataManager实例
        owner: 仓库所有者
        repo: 仓库名称
        branch: 分支名称
        current_documents: 当前从 GitHub 加载的文档列表
        
    Returns:
        FileChange 对象，包含新增、修改、删除的文件列表
    """
    repo_key = manager.get_repository_key(owner, repo, branch)
    repo_metadata = manager.metadata["repositories"].get(repo_key)
    
    changes = FileChange()
    
    # 构建当前文件的哈希映射
    current_files = {}
    for doc in current_documents:
        file_path = doc.metadata.get("file_path", "")
        if file_path:
            file_hash = compute_hash(doc.text)
            current_files[file_path] = {
                "hash": file_hash,
                "size": len(doc.text),
                "content": doc.text,
                "metadata": doc.metadata
            }
    
    # 如果是首次索引，所有文件都是新增
    if not repo_metadata:
        changes.added = list(current_files.keys())
        logger.info(f"首次索引仓库 {repo_key}，所有 {len(changes.added)} 个文件视为新增")
        return changes
    
    # 获取历史文件记录
    historical_files = repo_metadata.get("files", {})
    
    # 检测新增和修改
    for file_path, file_info in current_files.items():
        if file_path not in historical_files:
            changes.added.append(file_path)
        else:
            historical_hash = historical_files[file_path].get("hash", "")
            if file_info["hash"] != historical_hash:
                changes.modified.append(file_path)
    
    # 检测删除
    historical_paths: Set[str] = set(historical_files.keys())
    current_paths: Set[str] = set(current_files.keys())
    changes.deleted = list(historical_paths - current_paths)
    
    logger.info(
        f"变更检测完成 [{repo_key}]: "
        f"新增 {len(changes.added)} 个, "
        f"修改 {len(changes.modified)} 个, "
        f"删除 {len(changes.deleted)} 个"
    )
    
    return changes

