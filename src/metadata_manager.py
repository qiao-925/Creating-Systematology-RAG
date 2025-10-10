"""
元数据管理模块
负责追踪 GitHub 仓库的文件变化，实现增量更新的核心逻辑
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

from llama_index.core.schema import Document as LlamaDocument

from src.logger import setup_logger

logger = setup_logger('metadata_manager')


class FileChange:
    """文件变更记录"""
    
    def __init__(self):
        self.added: List[str] = []      # 新增的文件
        self.modified: List[str] = []   # 修改的文件
        self.deleted: List[str] = []    # 删除的文件
    
    def has_changes(self) -> bool:
        """是否有变更"""
        return bool(self.added or self.modified or self.deleted)
    
    def summary(self) -> str:
        """变更摘要"""
        parts = []
        if self.added:
            parts.append(f"新增 {len(self.added)} 个")
        if self.modified:
            parts.append(f"修改 {len(self.modified)} 个")
        if self.deleted:
            parts.append(f"删除 {len(self.deleted)} 个")
        return "、".join(parts) if parts else "无变更"
    
    def total_count(self) -> int:
        """总变更数"""
        return len(self.added) + len(self.modified) + len(self.deleted)


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
            # 确保目录存在
            self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存为格式化的 JSON
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"元数据保存成功: {self.metadata_path}")
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")
            raise
    
    @staticmethod
    def compute_hash(content: str) -> str:
        """计算文本内容的 MD5 哈希值
        
        Args:
            content: 文本内容
            
        Returns:
            MD5 哈希值（十六进制字符串）
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
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
                file_hash = self.compute_hash(doc.text)
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
                # 新增文件
                changes.added.append(file_path)
            else:
                # 检查哈希是否变化
                old_hash = historical_files[file_path].get("hash", "")
                new_hash = file_info["hash"]
                if old_hash != new_hash:
                    changes.modified.append(file_path)
        
        # 检测删除
        current_file_set = set(current_files.keys())
        historical_file_set = set(historical_files.keys())
        changes.deleted = list(historical_file_set - current_file_set)
        
        # 日志输出
        if changes.has_changes():
            logger.info(f"检测到变更 [{repo_key}]: {changes.summary()}")
            if changes.added:
                logger.debug(f"新增文件: {changes.added[:5]}{'...' if len(changes.added) > 5 else ''}")
            if changes.modified:
                logger.debug(f"修改文件: {changes.modified[:5]}{'...' if len(changes.modified) > 5 else ''}")
            if changes.deleted:
                logger.debug(f"删除文件: {changes.deleted[:5]}{'...' if len(changes.deleted) > 5 else ''}")
        else:
            logger.info(f"未检测到变更 [{repo_key}]")
        
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
                file_hash = self.compute_hash(doc.text)
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
            })
        return repos
    
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


if __name__ == "__main__":
    # 测试代码
    from pathlib import Path
    import tempfile
    
    print("=== 测试元数据管理器 ===\n")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # 初始化管理器
        manager = MetadataManager(temp_path)
        
        # 测试文档
        test_docs = [
            LlamaDocument(
                text="# README\n\nThis is a test.",
                metadata={"file_path": "README.md", "source": "github"}
            ),
            LlamaDocument(
                text="# Guide\n\nThis is a guide.",
                metadata={"file_path": "docs/guide.md", "source": "github"}
            ),
        ]
        
        # 首次检测（应该全部是新增）
        print("1. 首次检测变更:")
        changes = manager.detect_changes("test", "repo", "main", test_docs)
        print(f"   {changes.summary()}")
        print(f"   新增: {changes.added}\n")
        
        # 更新元数据
        print("2. 更新元数据:")
        manager.update_repository_metadata("test", "repo", "main", test_docs)
        print(f"   ✅ 元数据已保存\n")
        
        # 修改一个文档，再次检测
        print("3. 修改文档后检测:")
        test_docs[0].text = "# README\n\nThis is updated."
        changes = manager.detect_changes("test", "repo", "main", test_docs)
        print(f"   {changes.summary()}")
        print(f"   修改: {changes.modified}\n")
        
        # 删除一个文档
        print("4. 删除文档后检测:")
        changes = manager.detect_changes("test", "repo", "main", test_docs[:1])
        print(f"   {changes.summary()}")
        print(f"   删除: {changes.deleted}\n")
        
        # 列出仓库
        print("5. 列出所有仓库:")
        repos = manager.list_repositories()
        for repo in repos:
            print(f"   - {repo['key']}: {repo['file_count']} 个文件")
        
        print("\n✅ 测试完成")
        
    finally:
        # 清理
        if temp_path.exists():
            temp_path.unlink()

