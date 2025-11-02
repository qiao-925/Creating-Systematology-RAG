"""
元数据管理 - 管理器核心模块
MetadataManager类实现
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from llama_index.core.schema import Document as LlamaDocument

from src.logger import setup_logger
from src.metadata.file_change import FileChange
from src.metadata.utils import compute_hash

logger = setup_logger('metadata_manager')


class MetadataManager:
    """元数据管理器
    
    负责管理 GitHub 仓库的元数据，追踪文件变化，支持增量更新
    """
    
    def __init__(self, metadata_path: Path):
        """初始化元数据管理器
        
        Args:
            metadata_path: 元数据文件路径
        """
        self.metadata_path = metadata_path
        self.metadata: Dict = self._load_metadata()
        
    def _load_metadata(self) -> Dict:
        """加载元数据文件
        
        Returns:
            元数据字典
        """
        if not self.metadata_path.exists():
            logger.info("元数据文件不存在，创建新的元数据")
            return {
                "version": "1.0",
                "repositories": {}
            }
        
        try:
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            logger.info(f"加载元数据成功，共 {len(metadata.get('repositories', {}))} 个仓库")
            return metadata
        except Exception as e:
            logger.error(f"加载元数据失败: {e}")
            logger.warning("将创建新的元数据文件")
            return {
                "version": "1.0",
                "repositories": {}
            }
    
    def save_metadata(self):
        """保存元数据到文件"""
        try:
            self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"元数据保存成功: {self.metadata_path}")
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")
            raise
    
    def get_repository_key(self, owner: str, repo: str, branch: str = "main") -> str:
        """生成仓库的唯一标识
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            
        Returns:
            仓库标识字符串
        """
        return f"{owner}/{repo}@{branch}"
    
    def has_repository(self, owner: str, repo: str, branch: str = "main") -> bool:
        """检查仓库是否已存在
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            
        Returns:
            是否已存在
        """
        repo_key = self.get_repository_key(owner, repo, branch)
        return repo_key in self.metadata["repositories"]
    
    def get_repository_metadata(self, owner: str, repo: str, branch: str = "main") -> Optional[Dict]:
        """获取仓库的元数据
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            
        Returns:
            仓库元数据，如果不存在返回 None
        """
        repo_key = self.get_repository_key(owner, repo, branch)
        return self.metadata["repositories"].get(repo_key)
    
    def list_repositories(self) -> List[Dict]:
        """列出所有已追踪的仓库
        
        Returns:
            仓库信息列表
        """
        repos = []
        for repo_key, repo_data in self.metadata["repositories"].items():
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
    
    def detect_changes(
        self,
        owner: str,
        repo: str,
        branch: str,
        current_documents: List[LlamaDocument]
    ) -> FileChange:
        """检测文件变更
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            current_documents: 当前从 GitHub 加载的文档列表
            
        Returns:
            FileChange 对象，包含新增、修改、删除的文件列表
        """
        repo_key = self.get_repository_key(owner, repo, branch)
        repo_metadata = self.metadata["repositories"].get(repo_key)
        
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
        historical_paths = set(historical_files.keys())
        current_paths = set(current_files.keys())
        changes.deleted = list(historical_paths - current_paths)
        
        logger.info(
            f"变更检测完成 [{repo_key}]: "
            f"新增 {len(changes.added)} 个, "
            f"修改 {len(changes.modified)} 个, "
            f"删除 {len(changes.deleted)} 个"
        )
        
        return changes
    
    def update_repository_metadata(
        self,
        owner: str,
        repo: str,
        branch: str,
        documents: List[LlamaDocument],
        vector_ids_map: Optional[Dict[str, List[str]]] = None,
        commit_sha: Optional[str] = None
    ):
        """更新仓库的元数据
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            documents: 文档列表
            vector_ids_map: 文件路径到向量ID列表的映射（可选）
            commit_sha: 提交哈希（可选）
        """
        repo_key = self.get_repository_key(owner, repo, branch)
        
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
        self.metadata["repositories"][repo_key] = {
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
        self.save_metadata()
    
    def update_file_vector_ids(
        self,
        owner: str,
        repo: str,
        branch: str,
        file_path: str,
        vector_ids: List[str]
    ):
        """更新单个文件的向量ID列表
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            file_path: 文件路径
            vector_ids: 向量ID列表
        """
        repo_key = self.get_repository_key(owner, repo, branch)
        repo_metadata = self.metadata["repositories"].get(repo_key)
        
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
        self,
        owner: str,
        repo: str,
        branch: str,
        file_path: str
    ) -> List[str]:
        """获取文件的向量ID列表
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            file_path: 文件路径
            
        Returns:
            向量ID列表
        """
        repo_key = self.get_repository_key(owner, repo, branch)
        repo_metadata = self.metadata["repositories"].get(repo_key)
        
        if not repo_metadata:
            return []
        
        files = repo_metadata.get("files", {})
        file_metadata = files.get(file_path, {})
        return file_metadata.get("vector_ids", [])
    
    def remove_repository(self, owner: str, repo: str, branch: str = "main"):
        """移除仓库的元数据
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
        """
        repo_key = self.get_repository_key(owner, repo, branch)
        
        if repo_key in self.metadata["repositories"]:
            del self.metadata["repositories"][repo_key]
            logger.info(f"移除仓库元数据: {repo_key}")
            self.save_metadata()
        else:
            logger.warning(f"仓库 {repo_key} 不存在，无法移除")
    
    def get_documents_by_change(
        self,
        documents: List[LlamaDocument],
        changes: FileChange
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
