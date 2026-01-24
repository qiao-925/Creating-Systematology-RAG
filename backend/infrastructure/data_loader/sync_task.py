"""
后台同步任务：封装 GitHub 同步流程，支持后台执行和进度查询

与 ImportTask 保持一致的接口和进度管理逻辑。

主要功能：
- SyncTask: 后台同步任务类
- 支持启动、取消、进度查询
- 线程安全的状态管理

使用方式：
1. task = SyncTask.start(owner, repo, branch, index_manager, github_sync_manager)
2. while not task.is_complete:
       progress = task.get_progress()
       render_progress(progress)
       time.sleep(1)
3. if task.is_success: ...
"""

import threading
import traceback
from typing import Optional, Dict, Any, TYPE_CHECKING

from backend.infrastructure.logger import get_logger
from backend.infrastructure.data_loader.progress import ImportProgressManager, ImportStage

if TYPE_CHECKING:
    from backend.infrastructure.indexer.service import IndexService
    from backend.infrastructure.data_loader.github_sync.manager import GitHubSyncManager

logger = get_logger('sync_task')


class SyncTask:
    """后台同步任务
    
    封装 GitHub 同步的完整流程，在后台线程执行，
    支持实时进度查询和取消操作。
    与 ImportTask 保持一致的接口。
    """
    
    def __init__(
        self,
        owner: str,
        repo: str,
        branch: str,
        index_manager: "IndexService",
        github_sync_manager: "GitHubSyncManager"
    ):
        """初始化同步任务（不直接调用，使用 start() 类方法）"""
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.index_manager = index_manager
        self.github_sync_manager = github_sync_manager
        
        # 进度管理器（复用 ImportProgressManager）
        self.progress_manager = ImportProgressManager(owner, repo, branch)
        
        # 任务状态
        self._thread: Optional[threading.Thread] = None
        self._error: Optional[str] = None
        self._has_changes: bool = False
        self._changes_summary: str = ""
    
    @classmethod
    def start(
        cls,
        owner: str,
        repo: str,
        branch: str,
        index_manager: "IndexService",
        github_sync_manager: "GitHubSyncManager"
    ) -> "SyncTask":
        """启动同步任务"""
        task = cls(owner, repo, branch, index_manager, github_sync_manager)
        task._thread = threading.Thread(target=task._run, daemon=True)
        task._thread.start()
        logger.info(f"[SyncTask] 启动同步任务: {owner}/{repo}@{branch}")
        return task
    
    @property
    def is_complete(self) -> bool:
        """任务是否完成"""
        return self.progress_manager.is_complete
    
    @property
    def is_success(self) -> bool:
        """任务是否成功"""
        return self.progress_manager.current_stage == ImportStage.COMPLETE
    
    @property
    def error_message(self) -> Optional[str]:
        """错误消息"""
        return self._error
    
    @property
    def has_changes(self) -> bool:
        """是否有变更"""
        return self._has_changes
    
    @property
    def changes_summary(self) -> str:
        """变更摘要"""
        return self._changes_summary
    
    def get_progress(self) -> Dict[str, Any]:
        """获取当前进度"""
        return self.progress_manager.to_dict()
    
    def cancel(self):
        """请求取消任务"""
        self.progress_manager.request_cancel()
        logger.info(f"[SyncTask] 收到取消请求: {self.owner}/{self.repo}")
    
    def _run(self):
        """后台线程执行的同步流程"""
        pm = self.progress_manager
        
        try:
            # 阶段 1: 检查更新 (复用 GIT_CLONE 阶段表示同步)
            pm.start_stage(ImportStage.GIT_CLONE)
            pm.log_info(f"正在同步 {self.owner}/{self.repo}@{self.branch}...")
            
            from backend.infrastructure.data_loader import sync_github_repository
            
            documents, changes, commit_sha = sync_github_repository(
                owner=self.owner,
                repo=self.repo,
                branch=self.branch,
                github_sync_manager=self.github_sync_manager,
                show_progress=False
            )
            
            if commit_sha:
                pm.log_success(f"同步完成 (Commit: {commit_sha[:8]})")
            pm.complete_stage(ImportStage.GIT_CLONE)
            
            # 检查取消
            if pm.check_cancelled():
                return
            
            # 检查是否有变更
            if not changes.has_changes():
                self._has_changes = False
                pm.complete_import("已是最新版本")
                return
            
            self._has_changes = True
            self._changes_summary = changes.summary()
            pm.log_info(f"检测到变更: {self._changes_summary}")
            
            # 获取变更文档
            added_docs, modified_docs, deleted_paths = \
                self.github_sync_manager.get_documents_by_change(documents, changes)
            
            # 检查取消
            if pm.check_cancelled():
                return
            
            # 阶段 2: 构建索引（如果有新增或修改的文档）
            if added_docs or modified_docs:
                pm.start_stage(ImportStage.VECTORIZE, total=100)
                
                def progress_callback(current: int, total: int):
                    """索引构建进度回调"""
                    percent = int(current / total * 100) if total > 0 else 0
                    pm.update_progress(percent, f"向量化: {current}/{total} 节点")
                
                self.index_manager.build_index(
                    added_docs + modified_docs,
                    show_progress=False,
                    github_sync_manager=self.github_sync_manager,
                    progress_callback=progress_callback
                )
                
                pm.complete_stage(ImportStage.VECTORIZE)
            
            # 检查取消
            if pm.check_cancelled():
                return
            
            # 阶段 3: 增量更新索引
            pm.log_info("更新索引...")
            self.index_manager.incremental_update(
                added_docs=added_docs,
                modified_docs=modified_docs,
                deleted_file_paths=deleted_paths,
                github_sync_manager=self.github_sync_manager
            )
            
            # 阶段 4: 保存状态
            pm.log_info("保存同步状态...")
            
            # 获取 vector_ids_map
            vector_ids_map = {}
            for doc in documents:
                file_path = doc.metadata.get("file_path", "")
                if file_path:
                    vector_ids = self.github_sync_manager.get_file_vector_ids(
                        self.owner, self.repo, self.branch, file_path
                    )
                    vector_ids_map[file_path] = vector_ids
            
            self.github_sync_manager.update_repository_sync_state(
                owner=self.owner,
                repo=self.repo,
                branch=self.branch,
                documents=documents,
                vector_ids_map=vector_ids_map,
                commit_sha=commit_sha
            )
            
            # 完成
            pm.complete_import(f"同步完成！{self._changes_summary}")
            logger.info(f"[SyncTask] 同步完成: {self.owner}/{self.repo}")
            
        except Exception as e:
            error_msg = str(e)[:200]
            pm.fail_import(error_msg)
            self._error = error_msg
            logger.error(f"[SyncTask] 同步失败: {error_msg}")
            logger.debug(f"[SyncTask] 详细错误:\n{traceback.format_exc()}")
